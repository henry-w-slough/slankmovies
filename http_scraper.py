import yt_dlp
import httpx
import os

import config


class HTTPScraper:


    def __init__(self) -> None:
        """Handles all operations related to obtaining data from a website."""

        self._download_configs = yt_dlp.parse_options([])[-1]

        self._download_configs["proxy"] = config.PROXY_ADDRESS
        self._download_configs["merge_output_format"] = config.MOVIE_FORMAT
        self._download_configs["quiet"] = False


    async def get_movie_response(self, url: str, headers: dict, *args, **kwargs) -> httpx.Response:
        """Returns the full response of the given request as a Response."""
        
        async with httpx.AsyncClient() as client:

            response = await client.get(
                url,
                headers=headers,
                *args,
                **kwargs
            )

            response.raise_for_status()

            return response


    def download_movie(self, url: str, headers: dict, dir: str) -> None:
        """Calls to the given URLS and downloads it's contents to the given directory."""

        request_parameters = self._download_configs
        request_parameters["http_headers"] = headers
        request_parameters["outtmpl"] = os.path.join(dir, config.MOVIE_FILENAME)

        with yt_dlp.YoutubeDL(params=request_parameters) as connection:
            connection.download([url])


        