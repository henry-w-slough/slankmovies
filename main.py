import http_client

import asyncio
import httpx
import yt_dlp


connection = httpx.AsyncClient()


#note the m3u8 
ydl_address = "https://ibm.earthcleaner.cc/m3u8?=YjlGjjQS3L58PXfadit8vqfmw_OWDO8qdFV4yyEnrvdrqZ6KrsGwLIPPijHeCsf34FHOY8y-ge9483oqUIvPUMfQHT483-wL69h8d6LIfvT7z-kUZLSMoXBR2bc6CerhdIbrY8I22Yc-cKBszTuvB3dT46XReHEqON4n3mn2r36LsRAKdFHDvHlfXrjXuog_hdYrMpXa0qMQyJyurmRB6TZDbddbxB2MuYDIGnKFPxr_rS5uRBEFSC0NiTcQA5y1E8FfsHZk4F0z0zW_6XpolzDFfumQ_Rc8etWnQkvbchZS576-rWdBj9j1tRX60qV9E6Gf6Ab5IyyTN1BXZqyBXBxMzb7kPqZrHsZeDWszb5HzMPh9vzMhtf7Yff9VdLAZNPKyWPRmXFhIGxtyV5n7Mtn5_PS3d8mR-QAV4wzKPHrykKHim4xLcOyVYC07zUslp5HNjOqgCbKfwTYAB2FyUaiPiI6Ya1ZYa0KLhI_eJ9hUWKfKDsAvfU8YGKMGGqDSV9KKl9rYD7gAEF_DjKKZ6YhXbgvks0WzF4euoneQD7lcHOji1bo3uuqP_WRBWsT50HG2KNQTf6CiO8XLRNKSwq0mpUwAA45bG25uFYyOV3XsCIkiex7FGQ82JUoI2dbjneXhUqHjLBH_PrkxbEwwoC8H5Z500-La83LhhkOHd_DbyhIyDmv4a5h7W_7w4iXnkXNaumFxGWGuVLY2DfqF6ugsBq-k8HoTYC1hsCEeeODnddF_8-PxNsyUZuSGG63t",


# 2. Configure yt-dlp options and inject your headers
ydl_opts = {
    # Specify the output file name structure
    'outtmpl': 'movie.mp4',
    
    # Merge video into an mp4 container automatically
    'merge_output_format': 'mp4',
    
    # Inject your exact browser headers
    'http_headers': {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Host": "ibm.earthcleaner.cc",
        "Origin": "https://cinejoy.to",
        "Referer": "https://cinejoy.to",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
        "Sec-GPC": "1",
        "TE": "trailers",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:153.0) Gecko/20100101 Firefox/153.0"
    },
    
    # Optional: Shows progress bar and download details in the terminal
    'quiet': False, 
}



async def main():

    with yt_dlp.YoutubeDL(ydl_opts) as ydl: #type: ignore
        ydl.download(ydl_address)


asyncio.run(main())