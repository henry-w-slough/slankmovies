from typing import Any, Mapping
from urllib.parse import urlsplit

import config

from .data_handler import DataHandler
from .m3u8_handler import get_segment_urls, get_variants
from .request_handler import RequestHandler


class Scraper:
    def __init__(self, root_dir: str = "movies", proxies: dict[str, str] | None = None) -> None:
        self.root_directory: str = root_dir
        self.data_handler: DataHandler = DataHandler(root_dir=root_dir)

        if proxies is None:
            proxies = {
                "http://": config.HTTP_PROXY_ADDRESS,
                "https://": config.HTTPS_PROXY_ADDRESS,
            }

        self.request_handler: RequestHandler = RequestHandler(proxies=proxies)


    @staticmethod
    def _get_base_url(url: str) -> str:
        parsed = urlsplit(url)
        if not parsed.path:
            return f"{parsed.scheme}://{parsed.netloc}/"

        directory = parsed.path.rsplit('/', 1)[0]
        return f"{parsed.scheme}://{parsed.netloc}{directory}/"


    @staticmethod
    def _pick_best_variant(variants: Mapping[str, Any]) -> str:
        best_name: str | None = None
        best_score: tuple[int, int] = (-1, -1)

        for name, variant in variants.items():
            stream_info = getattr(variant, "stream_info", None)
            resolution = getattr(stream_info, "resolution", None)
            bandwidth = getattr(stream_info, "bandwidth", None)

            if resolution:
                score: tuple[int, int] = (int(resolution[0]) * int(resolution[1]), int(bandwidth or 0))
            elif bandwidth:
                score = (0, int(bandwidth))
            else:
                score = (0, 0)

            if score[0] > best_score[0] or (score[0] == best_score[0] and score[1] > best_score[1]):
                best_score = score
                best_name = name

        if best_name is None:
            best_name = next(iter(variants))

        return best_name


    async def download(self, playlist_url: str, output_directory: str = "downloads", file_name: str = "movie.ts", variant_name: str | None = None, headers: dict[str, str] | None = None) -> str:
        """Fetch a master playlist, auto-select the best variant, stream its segments, and save them under self.root_directory."""

        print(f"[Scraper] Fetching master playlist: {playlist_url}")
        master_playlist = await self.request_handler.get_m3u8(playlist_url, headers=headers)
        base_url = self._get_base_url(playlist_url)
        variants = get_variants(master_playlist, base_url=base_url)

        if not variants:
            raise ValueError(f"No variants found in playlist: {playlist_url}")

        if variant_name is None:
            variant_name = self._pick_best_variant(variants)

        if variant_name not in variants:
            raise KeyError(f"Variant '{variant_name}' not found. Available variants: {list(variants.keys())}")

        print(f"[Scraper] Selected variant: {variant_name}")
        variant_playlist = variants[variant_name]
        variant_url = getattr(variant_playlist, "uri", None)

        if not variant_url:
            raise ValueError(f"No variant URL was found for variant '{variant_name}'")

        print(f"[Scraper] Fetching variant playlist: {variant_url}")
        loaded_variant = await self.request_handler.get_m3u8(variant_url, headers=headers)
        segment_urls = get_segment_urls(loaded_variant, base_url=base_url)

        if not segment_urls:
            raise ValueError(f"No segment URLs were found for variant '{variant_name}'")

        print(f"[Scraper] Found {len(segment_urls)} segment URLs")
        segment_stream = self.request_handler.download_segments(segment_urls, headers=headers)
        return await self.data_handler.write_segment_stream(
            segment_stream=segment_stream,
            relative_directory=output_directory,
            file_name=file_name,
        )
