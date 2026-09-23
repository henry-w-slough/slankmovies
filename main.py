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

    print("Getting movie entries from TMDB...")

    movies = await id_scrape.get_movie_entries()

    for movie in movies:

        print(f"Attemping to download '{movie.name}' (id: {movie.id})...")

        try:
            await scrape.download_movie(f"MOVIES/{movie.name}.ts", f"https://cinejoy.pk/watch/movie/{movie.id}")
        except:
            print(f"\r ---Exception caught while downloading '{movie.name}': {scrape.request_handler.logs["error"]}")
            continue

    await scrape.close()


if __name__ == "__main__":
    asyncio.run(main())