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