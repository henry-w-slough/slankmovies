import asyncio
import ffmpeg

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

    movies = id_scrape.get_movie_entries()

    for movie in await movies:
        await scrape.download_movie(f"Movies/{movie.name}", f"https://cinejoy.pk/watch/movie/{movie.id}")
    await scrape.close()


if __name__ == "__main__":
    asyncio.run(main())






    