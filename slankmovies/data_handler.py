from typing import AsyncGenerator
import aiofiles


class DataHandler:


    async def write_byte_stream(self, src: str, stream: AsyncGenerator[bytes, None]) -> None:

        async with aiofiles.open(src, "wb") as file:
            async for chunk in stream:
                await file.write(chunk)