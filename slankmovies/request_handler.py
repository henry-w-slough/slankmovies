import httpx
import m3u8
from urllib.parse import urlparse
from typing import AsyncGenerator
import asyncio


class RequestHandler:


    def __init__(self) -> None:
        "Handles all HTTPS and HTTP requests. Assumes Tor daemon is in use and calls through the proxy."

        self.proxy = httpx.AsyncHTTPTransport(proxy="socks5h://127.0.0.1:9050")

        self.client = httpx.AsyncClient(

            timeout=httpx.Timeout(
                connect=10.0,
                read=60.0,
                write=30.0,
                pool=10.0,
            ),

            limits = httpx.Limits(
                max_connections=200
            ),

            trust_env=False,
            verify=False
        )

        self.semaphore = asyncio.Semaphore(100)

        self.default_retries = 3
        self.default_batch_size = 200


    async def send_request(self, url: str, method: str, headers: dict[str, str], logging: bool = False, *args, **kwargs) -> httpx.Response:

        try:
            async with self.semaphore:

                response = await self.client.request(
                    method,
                    url,
                    headers=headers,
                    *args,
                    **kwargs
                )
            response.raise_for_status()

            if logging:
                print(f"---Request to URL: '{url}' succeeded ({response.status_code}).---")

            return response
        
        except httpx.ConnectError:
            raise httpx.ConnectError(f"---Failed to connect to '{url}'---")

        except httpx.ConnectTimeout:
            raise httpx.ConnectTimeout(f"---Timed out while connecting to '{url}'---")

        except httpx.ReadTimeout:
            raise httpx.ReadTimeout(f"---Timed out while receiving data from '{url}'---")

        except httpx.HTTPStatusError as e:
            raise httpx.HTTPStatusError(f"---Received {e.response.status_code} on response from '{url}'---'", request=e.request, response=e.response)



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
            raise ValueError(f"---URL passed was not a valid M3U8: ({url})---")

        playlist = m3u8.loads(
            response.content.decode(encoding),
            uri=url,
        )

        return playlist


    async def get_segment_batch_byte_stream(self, segments: list[m3u8.Segment], headers: dict[str, str], logging: bool = False) -> AsyncGenerator[bytes, None]:

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
                logging = logging
            )
            yield init_response.content

        for start in range(0, len(segments), self.default_batch_size):

            #gets the segment batch based on the index of iteration for all segments
            segment_batch = segments[start:start + self.default_batch_size]

            #creates all request tasks for this batch
            tasks = [
                asyncio.create_task(
                    self.send_request(
                        segment.absolute_uri,
                        "get",
                        headers,
                        logging = logging
                    )
                )
                for segment in segment_batch
            ]

            try:
                responses = await asyncio.gather(*tasks)
                # gather preserves the order in which tasks were created.
                for response in responses:
                    yield response.content
                    
            except BaseException:
                for task in tasks:
                    if not task.done():
                        task.cancel()

                await asyncio.gather(*tasks, return_exceptions=True)
                raise



