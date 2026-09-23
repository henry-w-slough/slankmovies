import httpx
import m3u8
from urllib.parse import urlparse
from typing import AsyncGenerator
import asyncio

from .dns_resolver import DohNetworkBackend, DohResolver


class RequestHandler:


    def __init__(self) -> None:
        "Handles all HTTPS and HTTP requests."

        # The system resolver is bypassed on purpose: on DNS-filtering
        # networks (FortiGuard and the like) plaintext DNS is answered with a
        # block portal, which presented as 403s on every m3u8 and segment
        # request. See dns_resolver.py.
        self.resolver = DohResolver()

        transport: httpx.AsyncHTTPTransport

        if _tor_reachable():
            # A Tor daemon is running: route through it. socks5h keeps DNS on
            # the Tor exit, so no client-side resolver is involved at all.
            transport = httpx.AsyncHTTPTransport(proxy="socks5h://127.0.0.1:9050")
        else:
            # Direct connection with DoH-resolved addresses (curl --resolve
            # semantics): connect_tcp returns the real edge IP while SNI, the
            # Host header and certificate checks stay bound to the hostname.
            transport = httpx.AsyncHTTPTransport()
            transport._pool._network_backend = DohNetworkBackend(self.resolver)

        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=10.0,
                read=60.0,
                write=30.0,
                pool=10.0,
            ),

            limits = httpx.Limits(
                max_connections=250
            ),

            trust_env=False,
            verify=False,
            transport=transport,
        )

        self.semaphore = asyncio.Semaphore(200)

        self.default_retries = 3
        self.default_batch_size = 200

        self.logs = {
            "newest_request_url": "",
            "last_successful_request": "",
            "error": "", 
        }

        self.retryable_status_codes = {502, 503, 504}


    async def send_request(self, url: str, method: str, headers: dict[str, str], logging: bool = False, *args, **kwargs) -> httpx.Response:

        last_exception: Exception | None = None

        for attempt in range(self.default_retries + 1):

            try:
                async with self.semaphore:
                    response = await self.client.request(method, url, headers=headers, *args, **kwargs)

                if logging:
                    self.logs["newest_request_url"] = url

                response.raise_for_status()

                if logging:
                    self.logs["last_successful_request"] = f"Request to URL: '{url}' succeeded ({response.status_code})."

                return response

            except httpx.ConnectError:
                last_exception = httpx.ConnectError(f"Failed to connect to '{url}'")

            except httpx.ConnectTimeout:
                last_exception = httpx.ConnectTimeout(f"Timed out while connecting to '{url}'")

            except httpx.ReadTimeout:
                last_exception = httpx.ReadTimeout(f"Timed out while receiving data from '{url}'")

            except httpx.HTTPStatusError as e:
                if e.response.status_code not in self.retryable_status_codes:
                    self.logs["error"] = f"Received {e.response.status_code} on response from '{url}''"
                    print(e.response.text)
                    raise httpx.HTTPStatusError(self.logs["error"], request=e.request, response=e.response)

                last_exception = httpx.HTTPStatusError(
                    f"Received {e.response.status_code} on response from '{url}''",
                    request=e.request,
                    response=e.response,
                )

            if attempt < self.default_retries:
                await asyncio.sleep(0.5 * (2 ** attempt))

        self.logs["error"] = str(last_exception)

        if last_exception:
            raise last_exception


    async def get_m3u8(self, url: str, headers: dict[str, str], *args, **kwargs) -> m3u8.M3U8:

        response = await self.send_request(
            url,
            "get",
            headers,
            *args,
            **kwargs
        )

        encoding = response.charset_encoding or "utf-8"

        #checking for proper m3u8 signatures
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError(f"URL passed was not a valid M3U8: ({url})")

        playlist = m3u8.loads(
            response.content.decode(encoding),
            uri=url,
        )

        return playlist


    async def get_segment_batch_byte_stream(self, segments: list[m3u8.Segment], headers: dict[str, str], logging: bool = False, window: int = 20) -> AsyncGenerator[bytes, None]:

        if not segments:
            return

        # Fragmented MP4 playlists require the EXT-X-MAP initialization segment
        # before the media fragments, otherwise the output starts with `moof`.
        init_section = segments[0].init_section
        if init_section is not None:
            init_response = await self.send_request(
                init_section.absolute_uri,
                "get",
                headers,
                logging=logging
            )
            yield init_response.content

        queue: asyncio.Queue = asyncio.Queue(maxsize=window)

        async def worker(index: int, segment: m3u8.Segment) -> None:
            try:
                response = await self.send_request(
                    segment.absolute_uri,
                    "get",
                    headers,
                    logging=logging
                )
                await queue.put((index, response.content))
            except Exception as e:
                await queue.put((index, e))

        async def scheduler() -> None:
            # window caps in-flight requests via queue backpressure instead of
            # holding self.default_batch_size full responses in memory at once
            sem = asyncio.Semaphore(window)

            async def bounded_worker(index, segment):
                async with sem:
                    await worker(index, segment)

            tasks = [
                asyncio.create_task(bounded_worker(i, seg))
                for i, seg in enumerate(segments)
            ]
            await asyncio.gather(*tasks, return_exceptions=True)
            await queue.put(None)  # sentinel

        scheduler_task = asyncio.create_task(scheduler())

        buffer: dict[int, bytes] = {}
        next_index = 0
        try:
            while True:
                item = await queue.get()
                if item is None:
                    break

                index, payload = item

                if isinstance(payload, Exception):
                    print(f"Skipping permanently failed segment {index}: {segments[index].absolute_uri}")
                    buffer[index] = b""  # empty placeholder keeps ordering intact
                else:
                    buffer[index] = payload

                while next_index in buffer:
                    yield buffer.pop(next_index)
                    next_index += 1

        finally:
            if not scheduler_task.done():
                scheduler_task.cancel()
            await asyncio.gather(scheduler_task, return_exceptions=True)





def _tor_reachable() -> bool:
    """True when a Tor SOCKS daemon is listening on the local proxy port."""
    import socket

    try:
        with socket.create_connection(("127.0.0.1", 9050), timeout=0.5):
            return True
    except OSError:
        return False
