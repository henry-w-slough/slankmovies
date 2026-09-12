
from pathlib import Path

import aiofiles


class DataHandler:

    def __init__(self, root_dir: str = "movies") -> None:
        self.root_directory = root_dir


    async def write_segment_stream(self, segment_stream, relative_directory: str, file_name: str) -> str:
        """Write an async generator of bytes into a directory under self.root_directory."""

        base_dir = Path(self.root_directory) / relative_directory
        base_dir.mkdir(parents=True, exist_ok=True)

        file_path = base_dir / file_name

        async with aiofiles.open(file_path, "wb") as file:
            async for chunk in segment_stream:
                await file.write(chunk)

        return str(file_path)
