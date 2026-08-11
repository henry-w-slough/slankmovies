import asyncio

import http_scraper


scraper = http_scraper.HTTPScraper()


async def main() -> None:

    with open("movie.mp4", "ab") as file:
        x = 1
        while x != 1365:
            x += 1
            response = await scraper.get_movie_response(
                f"https://steelatom.top/vd/N2Zfa2Z2eGVHX25fdmQyeEw5UFBJQTpkZEYwUlgyaHhzWHRoRkduSGxMRXdQVEh3THN6RHM3TEtEUzJhOUlUd0Iw/seg-{x}-s1080p-v1-a1.m4s",
                {
                    "Accept": "*/*",
                    "Accept-Encoding": "gzip, deflate, br, zstd",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Connection": "keep-alive",
                    "Host": "steelatom.top",
                    "Origin": "https://www.cineplay.to",
                    "Referer": "https://www.cineplay.to/",
                    "Sec-Fetch-Dest": "empty",
                    "Sec-Fetch-Mode": "cors",
                    "Sec-Fetch-Site": "cross-site",
                    "Sec-GPC": "1",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0",
                }
            )
            file.write(response.content)
    


asyncio.run(main())
