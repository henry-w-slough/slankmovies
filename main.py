import asyncio
import logging
import uuid

from scraper import MovieScraper

 
scraper = MovieScraper()


async def main() -> None:

    await scraper.start()

    await scraper.download_movie(
        f"movies/{uuid.uuid4()}.mp4",
        "https://www.pornhub.com/view_video.php?viewkey=645e0d3d4bbfd"
    )
    

asyncio.run(main())
