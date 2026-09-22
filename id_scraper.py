import gzip
import io
import os
import datetime
import json
from pydantic import BaseModel
import httpx

from slankmovies import RequestHandler


class Movie(BaseModel):
    name: str
    id: int


class MovieIdScraper:


    def __init__(self):

        self.request_handler = RequestHandler()
                    

    async def get_movie_entries(self, adult: bool = False, rating_floor: float = 40.0) -> list[ Movie]:

        movies: list[Movie] = []

        date = datetime.datetime.now(datetime.timezone.utc).strftime("%m_%d_%Y")

        url_to_send = f"https://files.tmdb.org/p/exports/movie_ids_{date}.json.gz" if not adult else f"https://files.tmdb.org/p/exports/adult_movie_ids_{date}.json.gz"
        movie_db_response = await self.request_handler.send_request(
            url_to_send,
            "get",
            headers = {}
        )

        with gzip.GzipFile(fileobj=io.BytesIO(movie_db_response.content)) as gz:
            movie_db_content = gz.read().decode('utf-8')

        for line in movie_db_content.splitlines():

            if not line.strip():  # Skip empty lines
                continue

            entry = json.loads(line)

            if entry["popularity"] < rating_floor:
                continue

            movies.append(
                Movie(
                    name = entry["original_title"],
                    id = entry["id"]
                )
            )

        return movies





