import asyncio
import logging


logging.basicConfig(level=logging.DEBUG)
logging.getLogger("httpx").setLevel(logging.DEBUG)
logging.getLogger("httpcore").setLevel(logging.DEBUG)


from scraper import MovieScraper


scraper = MovieScraper()


async def main() -> None:

    await scraper.download_movie(
        "movies/DARKCRYSTAL.mp4",
        "https://moon.peakstorm.top/vd/dkZ3bXJuZzBNajQtWUVDcmpYRldsUTpWU1lxZXRXV1oxTHo2Tlk1VzBkajZB/index-s1080p-v1-a1.m3u8",
        {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Host": "moon.peakstorm.top",
            "Origin": "https://www.movy.bz",
            "Referer": "https://www.movy.bz/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
            "Sec-GPC": "1",
            "TE": "trailers",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0"
        }
    )
    





asyncio.run(main())
