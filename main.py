import asyncio
import logging


logging.basicConfig(level=logging.DEBUG)
logging.getLogger("httpx").setLevel(logging.DEBUG)
logging.getLogger("httpcore").setLevel(logging.DEBUG)


from scraper import MovieScraper


scraper = MovieScraper()


async def main() -> None:

    await scraper.download_movie(
        "movies/movie.mp4",
        'https://proxy.valhallastream.dpdns.org/m3u8-proxy?url=https://boldvisionstrategy.site/AIQnpSU7C/pl/H4sIAAAAAAAAAw3NW3KDIBQA0C2B6Fj71zxw4igOCBflD0MyFvHRjmlSV9.eDZzbG77jKLWZTdPMZcndIkT6LE4Sgqwl6Tuf1tbR8Sl0QsUOlYbhs9sPc0_d4mZWG4RefEqMOAsPSOEyMouZoa41PcLvZtUJsFXb0xH30J55G4WzI0XDYAU9rk0_mVpKN1oCJbQmVO3hYXYXV21AjSq2mxIdh.XX5FvHJkykD7jP.avKme.wk1V.JYyscXXiSKpNNJhSiRzVPlg30u8yCqqfQ6vmYmVq2DvlCIdDqQNQNv3_KnzJ6BJVKlmEXn.ak5lu53C8tgUy_kJYtAGgbOvxICVm6KocZ_gjbrQZzI6yPzaImwlBAQAA/master.m3u8&headers={"Origin":"https://nextgencloudfabric.com","Referer":"https://nextgencloudfabric.com/"}',
        {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Host": "proxy.valhallastream.dpdns.org",
            "Origin": "https://www.rivestream.app",
            "Referer": "https://www.rivestream.app/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
            "Sec-GPC": "1",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:140.0) Gecko/20100101 Firefox/140.0",
        }
    )





asyncio.run(main())
