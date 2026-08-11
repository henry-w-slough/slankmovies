import yt_dlp

import config


class HTTPScraper:


    def __init__(self) -> None:
        """Handles all operations related to obtaining data from a website."""

        self._download_configs = yt_dlp.parse_options([])[-1]

        self._download_configs["proxy"] = config.PROXY_ADDRESS
        self._download_configs["outtmpl"] = f"{config.MOVIE_FILENAME}.{config.MOVIE_FORMAT}"
        self._download_configs["merge_output_format"] = config.MOVIE_FORMAT
        self._download_configs["quiet"] = False

        self._download_connection = yt_dlp.YoutubeDL(params=self._download_configs)


    def download_movie(self, url: str, http_headers: dict = {}) -> None:
        """Calls to the given URLS and downloads their contents.
        
        Note that http_headers is optional but strongly recommended, as
        most sites require request headers to return a proper response."""

        self._download_connection.params["http_headers"] = http_headers

        self._download_connection.download([url])


        