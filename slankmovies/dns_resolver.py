"""DNS resolution that cannot be hijacked by network-level DNS filters.

The RequestHandler used to rely on the system resolver, which on a FortiGate
/ FortiGuard managed network answers *every* plaintext DNS query (even those
sent to 1.1.1.1 or 8.8.8.8, because outbound port 53 is intercepted) with the
address of a block portal. Every request then lands on the portal and comes
back as a 403 "Web Page Blocked!" HTML page instead of the m3u8.

The fix is to resolve over HTTPS (DoH), which the filter cannot intercept,
and connect to the resolved address directly. httpcore performs the TLS
handshake with ``server_hostname`` taken from the request's origin -- not
from whatever address the backend connected to -- so SNI, the Host header and
certificate validation all stay bound to the real hostname, equivalent to
``curl --resolve``.
"""

from __future__ import annotations

import asyncio
import ipaddress
import socket
import time
from typing import Iterable

import httpx
from httpcore._backends.auto import AutoBackend
from httpcore._backends.base import SOCKET_OPTION, AsyncNetworkStream


class DohResolver:
	"""Resolve hostnames over DNS-over-HTTPS with caching and coalescing.

	Providers are tried in order: ``1.1.1.1`` first because it is an IP
	literal and needs no bootstrap DNS at all, then ``dns.google`` which is
	reached through the (possibly filtered) system resolver. If every provider
	fails, the system resolver itself is used as a last resort so behaviour on
	an unfiltered network degrades to the status quo rather than failing.
	"""

	# 1.1.1.1 is queried by address, so the DoH lookup itself never depends
	# on the resolver it is trying to bypass.
	_PROVIDERS = (
		("https://1.1.1.1/dns-query", {"name": "{host}", "type": "A"}),
		("https://dns.google/resolve", {"name": "{host}", "type": "A"}),
	)

	_DEFAULT_TTL = 300.0
	_MAX_TTL = 3600.0
	_FAILURE_TTL = 60.0
	_NEGATIVE_TTL = 30.0

	def __init__(self, timeout: float = 4.0) -> None:
		self._client = httpx.AsyncClient(
			verify=False,
			trust_env=False,
			timeout=httpx.Timeout(
				connect=timeout,
				read=timeout,
				write=timeout,
				pool=timeout,
			),
		)
		self._cache: dict[str, tuple[float, list[str]]] = {}
		self._locks: dict[str, asyncio.Lock] = {}
		self._round_robin: dict[str, int] = {}

	async def resolve(self, host: str) -> str:
		"""Return one IPv4 address for ``host``, bypassing the system resolver."""
		# Hosts given as IP literals (proxies, tests) need no lookup, and
		# looking them up would be wrong.
		try:
			ipaddress.ip_address(host)
			return host
		except ValueError:
			pass

		now = time.monotonic()
		entry = self._cache.get(host)
		if entry is not None and entry[0] > now:
			return self._pick(host, entry[1])

		# Coalesce concurrent lookups for the same host: a batch of segment
		# requests all resolve once, not once per connection.
		lock = self._locks.setdefault(host, asyncio.Lock())
		async with lock:
			entry = self._cache.get(host)
			if entry is not None and entry[0] > now:
				return self._pick(host, entry[1])

			addresses, ttl = await self._lookup(host)
			self._cache[host] = (time.monotonic() + ttl, addresses)
			return self._pick(host, addresses)

	async def aclose(self) -> None:
		await self._client.aclose()

	async def _lookup(self, host: str) -> tuple[list[str], float]:
		for provider, template in self._PROVIDERS:
			try:
				response = await self._client.get(
					provider,
					params={key: value.format(host=host) for key, value in template.items()},
					headers={"accept": "application/dns-json"},
				)
				response.raise_for_status()
			except httpx.HTTPError:
				continue

			answers = [
				answer
				for answer in response.json().get("Answer", [])
				if answer.get("type") == 1
			]
			if answers:
				addresses = _unique(answer["data"] for answer in answers)
				ttls = [answer.get("TTL") for answer in answers if answer.get("TTL")]
				ttl = min(ttls) if ttls else self._DEFAULT_TTL
				return addresses, min(max(ttl, 1.0), self._MAX_TTL)

		# Every DoH provider failed or returned no A record. Fall back to the
		# system resolver with a short TTL: on an unfiltered network this is
		# simply the correct answer, on a filtered one it is the same result
		# the pipeline produced before this module existed.
		try:
			infos = await asyncio.to_thread(
				socket.getaddrinfo, host, None, family=socket.AF_INET
			)
		except socket.gaierror as error:
			self._cache[host] = (time.monotonic() + self._NEGATIVE_TTL, [])
			raise httpx.ConnectError(
				f"DNS resolution failed for '{host}' via DoH and system resolver"
			) from error

		addresses = _unique(info[4][0] for info in infos)
		if not addresses:
			self._cache[host] = (time.monotonic() + self._NEGATIVE_TTL, [])
			raise httpx.ConnectError(f"No IPv4 address found for '{host}'")
		return addresses, self._FAILURE_TTL

	def _pick(self, host: str, addresses: list[str]) -> str:
		# Spread concurrent connections across the returned addresses;
		# Cloudflare edge IPs are interchangeable, but one dead IP should not
		# receive every connection.
		if not addresses:
			raise httpx.ConnectError(f"No cached address for '{host}'")
		index = self._round_robin.get(host, 0)
		self._round_robin[host] = index + 1
		return addresses[index % len(addresses)]


def _unique(values) -> list[str]:
	seen: set[str] = set()
	ordered: list[str] = []
	for value in values:
		if value not in seen:
			seen.add(value)
			ordered.append(value)
	return ordered


class DohNetworkBackend(AutoBackend):
	"""httpcore network backend that connects to DoH-resolved addresses.

	Only ``connect_tcp`` is overridden: httpcore itself performs the TLS
	handshake afterwards with ``server_hostname`` set to the request's origin
	hostname, so SNI and the Host header stay bound to the real name no matter
	which address the TCP connection was opened against.
	"""

	def __init__(self, resolver: DohResolver) -> None:
		self._resolver = resolver

	async def connect_tcp(
		self,
		host: str,
		port: int,
		timeout: float | None = None,
		local_address: str | None = None,
		socket_options: Iterable[SOCKET_OPTION] | None = None,
	) -> AsyncNetworkStream:
		address = await self._resolver.resolve(host)
		return await super().connect_tcp(
			address,
			port,
			timeout=timeout,
			local_address=local_address,
			socket_options=socket_options,
		)
