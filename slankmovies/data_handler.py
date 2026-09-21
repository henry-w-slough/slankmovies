from typing import AsyncGenerator
import aiofiles
import os


class DataHandler:


    async def write_byte_stream(self, src: str, stream: AsyncGenerator[bytes, None]) -> None:

        if not os.path.exists(os.path.dirname(src)):
            os.makedirs(os.path.dirname(src))
            
        async with aiofiles.open(src, "wb") as file:
            async for chunk in stream:
                await file.write(chunk)