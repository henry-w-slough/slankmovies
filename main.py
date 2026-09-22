import asyncio
import logging
import random
import uuid

import scraper
import id_scraper


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
            print(f"! Exception caught while downloading '{movie.name}' !")
            continue

    await scrape.close()


if __name__ == "__main__":
    asyncio.run(main())