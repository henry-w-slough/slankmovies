import httpx
import asyncio
import m3u8
import charset_normalizer


class RequestHandler:


    def __init__(self, proxies: dict[str, str] | None = None) -> None:
        """Handles all operations related to sending or receiving requests."""

        self.mounts = {}

        #creating HTTPTransports from proxies for self.mounts
        if proxies is not None:
            for scheme, proxy in proxies.items():
                self.mounts[scheme] = httpx.AsyncHTTPTransport(proxy=proxy)

        self.connection = httpx.AsyncClient(
            mounts = self.mounts,
            limits = httpx.Limits(max_connections=200),
            timeout = httpx.Timeout(connect=10.0, read=20.0, write=20.0, pool=10.0)
        )

        self.semaphore = asyncio.Semaphore(50)


    async def send_request(self, method: str, url: str, headers: dict | None = None, *args, **kwargs) -> httpx.Response:

        async with self.semaphore:
            try:
                response = await self.connection.request(
                    method,
                    url,
                    headers=headers,
                    *args,
                    **kwargs
                )
                response.raise_for_status()
                return response
                
            except httpx.HTTPStatusError as e:
                print(f"-----HTTPS STATUS ERROR EXCEPTION CAUGHT-----")
                print(f"Status Code: {e.response.status_code}")
                print(f"Message: {e.response.text}")
                raise
            except Exception as e:
                print(f"-----EXCEPTION CAUGHT DURING REQUEST OF TYPE: '{type(e).__name__}'-----")
                raise


    async def get_m3u8(self, url: str, headers: dict[str, str] | None) -> m3u8.M3U8:
        """Returns a new M3U8 object based on the content of the return from the given URL. Raises an InvalidMasterM3U8Exception if the given url is not a master.m3u8."""
        #using httpx in custom request function to allow proxy use
        response = await self.send_request("get", url, headers)

        #getting encoding
        encoding_charset = charset_normalizer.from_bytes(response.content).best()

        if encoding_charset is None:
            raise LookupError()

        playlist = m3u8.loads(response.content.decode(encoding_charset.encoding), url)

        return playlist
    

    async def get_segment_batch_responses(self, variant: m3u8.Playlist, headers: dict[str, str]) -> list[httpx.Response]:

        responses = []

        variant_response = await self.send_request("get", variant.absolute_uri, headers)
        variant_data = m3u8.loads(str(variant_response.content), variant.absolute_uri)

        segment_urls = [seg.absolute_uri for seg in variant_data.segments]

        #gathering request tasks for asyncio for async
        tasks = [self.send_request("get", url, headers) for url in segment_urls]
        responses = await asyncio.gather(*tasks)

        return responses


        
        