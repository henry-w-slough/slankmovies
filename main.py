import asyncio

import http_scraper


scraper = http_scraper.HTTPScraper()


async def main() -> None:
    scraper.download_movie(
        "https://www.youtube.com/watch?v=vknjVXisOgk",
        {}
    )
    


asyncio.run(main())
