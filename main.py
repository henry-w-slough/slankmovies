import asyncio

import scraper
import id_scraper

import logging

# Configure the root logger format and level
logging.basicConfig(
    format="%(levelname)s [%(asctime)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.DEBUG
)


scrape = scraper.Scraper()
id_scrape = id_scraper.MovieIdScraper()


async def main() -> None:

    await scrape.start()

    await scrape.download_movie(f"MOVIES/TheGodfather.ts", f"https://cinejoy.pk/watch/movie/238")

    await scrape.close()


if __name__ == "__main__":
    asyncio.run(main())






    