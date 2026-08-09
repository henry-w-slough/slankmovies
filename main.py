import http_client
import config

import asyncio
import httpx
import yt_dlp


connection = httpx.AsyncClient()


async def main():

    for seg in range(1, 101):

        ydl_address = f"https://glassfalcon.site/vd/N2Zfa2Z2eGVHX25fdmQyeEw5UFBJQTpkZEYwUlgyaHhzWHRoRkduSGxMRXdQVEh3THN6RHM3TEtEUzJhOUlUd0Iw/seg-{seg}-s1080p-v1-a1.m4s"

        with yt_dlp.YoutubeDL(config.ydl_opts) as ydl: #type: ignore
            ydl.download(config.ydl_address)


asyncio.run(main())