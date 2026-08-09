#note the m3u8 
ydl_address = "https://glassfalcon.site/vd/N2Zfa2Z2eGVHX25fdmQyeEw5UFBJQTpkZEYwUlgyaHhzWHRoRkduSGxMRXdQVEh3THN6RHM3TEtEUzJhOUlUd0Iw/seg-18-s1080p-v1-a1.m4s"

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
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Host": "glassfalcon.site",
        "Origin": "https://www.cineby.at",
        "Referer": "https://www.cineby.at",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
        "Sec-GPC": "1",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:140.0) Gecko/20100101 Firefox/140.0"
    },
    
    # Optional: Shows progress bar and download details in the terminal
    'quiet': False, 
}