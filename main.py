import asyncio
import config
import logging



import scraper


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logging.getLogger("httpx").setLevel(logging.INFO)
logging.getLogger("httpcore").setLevel(logging.INFO)


s = scraper.Scraper()


async def main() -> None:

    await s.start()

    await s.download_movie(
        "movies/movie.mp4",
        "https://cinejoy.to/movie/244786-whiplash-2014",
    )

    await s.close()


    


if __name__ == "__main__":
    asyncio.run(main())