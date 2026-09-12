import asyncio
import aiofiles
import config
import httpx
from exceptions.invalid_m3u8_exception import InvalidM3U8Exception


from slankmovies import DataHandler
from slankmovies import RequestHandler
from slankmovies import WebScraper


class MovieScraper:


    def __init__(self) -> None:

        self.data_handler = DataHandler()
        self.request_handler = RequestHandler(
            proxies= {
                "http://": config.HTTP_PROXY_ADDRESS,
                "https://": config.HTTPS_PROXY_ADDRESS
            }
        )
        self.web_scraper = WebScraper()


    async def start(self) -> None:
        await self.web_scraper.start()


    async def download_movie(self, dir: str, url: str) -> None:

        print(f"----Obtaining master.m3u8 data from URL: '{url}'----")

        master_data = await self.web_scraper.get_master_m3u8_data(url)

        print(f"----Got master.m3u8 data. URL: {master_data["url"]}'")

        master = await self.request_handler.get_m3u8(master_data["url"], master_data["headers"])
        variants = self.data_handler.get_m3u8_master_variants(master)
        variants_resolutions = self.data_handler.get_m3u8_variant_resolutions(variants)

        # finding variant with best res
        variant = next((k for k, v in variants_resolutions.items() if v == max(variants_resolutions.values())), None)

        if variant is None:
            print("---No variants found, assuming given URL is an index m3u8---")
        else:
            print(f"---Defaulting to best resolution: {variant.stream_info.resolution}---")
            print("---Attempting to parse variant m3u8 file for segments and request for response content...---")
            segment_responses = await self.request_handler.get_segment_batch_responses(variant, master_data["headers"])
            print(f"---Writing segment batch response content to directory: '{dir}'---")
            self.data_handler.write_segment_response_batch_content(dir, segment_responses)

