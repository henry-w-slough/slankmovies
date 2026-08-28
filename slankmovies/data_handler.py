import m3u8
import re
import httpx
import os
from typing import Any

class DataHandler:


    def __init__(self) -> None:
        """Handles all operations relating to data management."""


    def get_m3u8_master_variants(self, master: m3u8.M3U8) -> list[m3u8.Playlist]:

        variants = []

        for variant in master.playlists:
            variants.append(variant)

        return variants
    
        
    def get_m3u8_variant_resolutions(self, variants: list[m3u8.Playlist]) -> dict[m3u8.Playlist, tuple[int, int]]:
        """Returns the resolutions of the given variants with the absolute uri of the variant."""

        resolutions: dict[m3u8.Playlist, tuple[int, int]] = {}

        for variant in variants:
            resolution = variant.stream_info.resolution
            if resolution is not None:
                resolutions[variant] = resolution

        return resolutions


    def write_segment_response_batch_content(self, dir: str, batch_responses: list[httpx.Response]) -> None:

        file_path = os.path.dirname(dir)
        if file_path != "":
            os.makedirs(file_path, exist_ok=True)

        with open(dir, "wb") as file:
            for response in batch_responses:
                file.write(response.content)
        
        

        

  

            
