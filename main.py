import asyncio

import config

from slankmovies import Scraper

scraper = Scraper(proxies={
    "http://": config.HTTP_PROXY_ADDRESS,
    "https://": config.HTTPS_PROXY_ADDRESS,
})


async def main() -> None:
    await scraper.download(
        "https://ev-h.phncdn.com/hls/c6251/videos/202608/23/59896325/720P_4000K_59896325.mp4/master.m3u8?validfrom=1789243394&validto=1789250594&ipa=1&hdl=-1&hash=PhILdxMKtBkp1QU1cGWo3O1wSII=",
        file_name=f"movie.{config.MOVIE_FORMAT}",
        headers={
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            "Host": "ev-h.phncdn.com",
            "Origin": "https://www.pornhub.com",
            "Referer": "https://www.pornhub.com/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
            "Sec-GPC": "1",
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:155.0) "
                "Gecko/20100101 Firefox/155.0"
            ),
        },
    )


if __name__ == "__main__":
    asyncio.run(main())
