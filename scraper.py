import asyncio
import aiofiles
import config
import httpx
from exceptions.invalid_m3u8_exception import InvalidM3U8Exception


from slankmovies import DataHandler
from slankmovies import RequestHandler


class MovieScraper:


    def __init__(self) -> None:

        self.data_handler = DataHandler()
        self.request_handler = RequestHandler(
            proxies= {
                "http://": config.HTTP_PROXY_ADDRESS,
                "https://": config.HTTPS_PROXY_ADDRESS
            }
        )


    async def download_movie(self, dir: str, master_url: str, headers: dict) -> None:

        master = await self.request_handler.get_m3u8(master_url, headers)
        variants = await asyncio.to_thread(self.data_handler.get_m3u8_master_variants, master)
        variants_resolutions = await asyncio.to_thread(self.data_handler.get_m3u8_variant_resolutions, variants)

        #finding variant with best res
        variant = next((k for k, v in variants_resolutions.items() if v == max(variants_resolutions.values())), None)

        if variant is None:
            print("---No variants found, assuming given URL is an index m3u8---")
        else:
            print(f"---Defaulting to best resolution: {variant.stream_info.resolution}---")
            print("---Attempting to parse variant m3u8 file for segments and request for response content...---")
            segment_responses = await self.request_handler.get_segment_batch_responses(variant, headers)
            print(f"---Writing segment batch response content to directory: '{dir}'---")
            await asyncio.to_thread(self.data_handler.write_segment_response_batch_content, dir, segment_responses)


