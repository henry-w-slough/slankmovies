from slankmovies import *

class Scraper:


    def __init__(self) -> None:

        self.data_handler = DataHandler()
        self.request_handler = RequestHandler()
        self.m3u8_handler = M3U8Handler()
        self.web_scraper = WebScraper()


    async def start(self) -> None:
        await self.web_scraper.start()


    async def close(self) -> None:
        await self.web_scraper.close()


    async def download_movie(self, src: str, url: str) -> None:

        m3u8_info = await self.web_scraper.resolve_m3u8(url)

        master_m3u8 = await self.request_handler.get_m3u8(m3u8_info["url"], m3u8_info["headers"])

        print("---Successfully got master M3U8, now attemping to get variants---")

        variant = self.m3u8_handler.get_m3u8_playlists(master_m3u8)[0]

        print(f"---Using default variant: ({variant.stream_info.resolution})---")

        variant_m3u8 = await self.request_handler.get_m3u8(variant.absolute_uri, m3u8_info["headers"])

        segments = self.m3u8_handler.get_m3u8_segments(variant_m3u8)

        print(f"---Attempting to download all segments into source path: '{src}'---")

        await self.data_handler.write_byte_stream(
            src,
            self.request_handler.get_segment_batch_byte_stream(segments, m3u8_info["headers"], logging=True)
        )

        print(f"---Successfully downloaded movie into source path: '{src}'")

        