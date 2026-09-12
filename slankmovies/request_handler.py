import asyncio
from typing import AsyncGenerator

import httpx
import m3u8

from .exceptions.invalid_m3u8_error import InvalidM3U8Error


class RequestHandler:
    def __init__(self, proxies: dict[str, str] | None = None) -> None:
        """Handles all operations related to sending or receiving requests."""

        self.proxies = proxies or {}
        self.mounts: dict[str, httpx.AsyncHTTPTransport] = {}

        for scheme, proxy in self.proxies.items():
            if not scheme.endswith("://"):
                scheme = f"{scheme}://"
            self.mounts[scheme] = httpx.AsyncHTTPTransport(proxy=proxy)

        self.connection = httpx.AsyncClient(
            mounts=self.mounts,
            limits=httpx.Limits(max_connections=200),
            timeout=httpx.Timeout(connect=10.0, read=20.0, write=20.0, pool=10.0),
            trust_env=False,
        )

        self.semaphore = asyncio.Semaphore(150)


    async def close(self) -> None:
        await self.connection.aclose()


    async def __aenter__(self):
        return self


    async def __aexit__(self, exc_type, exc, tb):
        await self.close()


    async def send_request(self, method: str, url: str, headers: dict | None = None, log: bool = True, retries: int = 3, backoff: float = 0.5, *args, **kwargs) -> httpx.Response:

        async with self.semaphore:

            last_error = None

            for attempt in range(retries + 1):

                try:
                    if log:
                        print(f"[Request] {method.upper()} {url} (attempt {attempt + 1}/{retries + 1})")

                    response = await self.connection.request(
                        method,
                        url,
                        headers=headers,
                        *args,
                        **kwargs,
                    )

                    if response.status_code in {429, 500, 502, 503, 504}:
                        raise httpx.HTTPStatusError(
                            f"Retryable status code: {response.status_code}",
                            request=response.request,
                            response=response,
                        )

                    response.raise_for_status()

                    if log:
                        print(f"[Request] SUCCESS {method.upper()} {url} -> {response.status_code}")

                    return response

                except (httpx.TimeoutException, httpx.RequestError, httpx.HTTPStatusError) as exc:
                    last_error = exc

                    if attempt >= retries:
                        raise

                    # waiting to not block the whole system
                    await asyncio.sleep(backoff * (2 ** attempt))

            if last_error is not None:
                raise last_error

            raise RuntimeError(f"Request failed without caught exception for: {url}")


    async def get_m3u8(self, url: str, headers: dict | None = None, log: bool = True) -> m3u8.M3U8:
        """Fetch a playlist and return a parsed M3U8 object."""

        response = await self.send_request(
            "GET",
            url,
            headers=headers,
            log=log,
            follow_redirects=True,
        )

        content = response.text

        if not content or "#EXTM3U" not in content:
            raise InvalidM3U8Error(f"URL did not return a valid M3U8 playlist: {url}")

        return m3u8.loads(content)


    async def _fetch_segment(self, url: str, headers: dict | None = None, log: bool = True) -> bytes:
        response = await self.send_request(
            "GET",
            url,
            headers=headers,
            log=log,
            follow_redirects=True,
        )
        return response.content


    async def download_segments(self, segment_urls: list[str], headers: dict | None = None, log: bool = True) -> AsyncGenerator[bytes, None]:
        """Yield segment bytes in order as they are downloaded."""

        for index, url in enumerate(segment_urls):
            print(f"[Segment] Downloading segment {index}/{len(segment_urls) - 1}: {url}")
            yield await self._fetch_segment(url, headers=headers, log=log)
