from typing import AsyncGenerator
import aiofiles
import ffmpeg
import os
import asyncio
import shutil


FFMPEG = shutil.which("ffmpeg") or r"C:\ffmpeg\bin\ffmpeg.exe"


class DataHandler:


    def sniff(self, data: bytes) -> tuple[str | None, int]:
        """Return (ffmpeg input format, offset where real data starts)."""
        # MPEG-TS: 0x47 sync byte repeating every 188 bytes (possibly after junk)
        for off in range(min(len(data), 1024)):
            if data[off] == 0x47 and all(
                off + i * 188 >= len(data) or data[off + i * 188] == 0x47
                for i in range(1, 5)
            ) and off + 188 * 4 < len(data):
                return "mpegts", off
        if data[4:8] in (b"ftyp", b"styp") or data[4:8] == b"moof":
            return "mp4", 0
        if data[:4] == b"\x1a\x45\xdf\xa3":
            return "matroska", 0          # mkv / webm
        if data[:3] == b"FLV":
            return "flv", 0
        if data[:4] == b"RIFF" and data[8:12] == b"AVI ":
            return "avi", 0
        if data[:4] == b"OggS":
            return "ogg", 0
        if data[:7] == b"#EXTM3U":
            return None, 0                # it's a playlist, not media
        if data[:1] in (b"<", b"{"):
            return None, 0                # HTML / JSON error page
        return None, 0

    async def write_byte_stream(self, ts_stream: AsyncGenerator[bytes, None], output_path: str) -> None:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        # Buffer until there's enough to sniff reliably
        buf = b""
        async for chunk in ts_stream:
            buf += chunk
            if len(buf) >= 4096:
                break
        fmt, offset = self.sniff(buf)
        if fmt is None:
            raise RuntimeError(f"Unrecognized input, first bytes: {buf[:32].hex()}")
        buf = buf[offset:]

        # Copy is only safe for TS/MP4/MKV with compatible codecs; fall back to re-encode otherwise
        out_kwargs = dict(movflags="faststart")
        if fmt == "mpegts":
            out_kwargs.update(vcodec="copy", acodec="copy", bsf="a:aac_adtstoasc")
        elif fmt in ("mp4", "matroska"):
            out_kwargs.update(vcodec="copy", acodec="copy")
        else:
            out_kwargs.update(vcodec="libx264", acodec="aac")

        args = (
            ffmpeg.input("pipe:", format=fmt)
            .output(f"{output_path}.{fmt}", **out_kwargs)
            .overwrite_output()
            .compile(cmd=FFMPEG)
        )
        proc = await asyncio.create_subprocess_exec(
            *args, stdin=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stderr_task = asyncio.create_task(proc.stderr.read())

        try:
            proc.stdin.write(buf)
            async for chunk in ts_stream:
                proc.stdin.write(chunk)
                await proc.stdin.drain()
        except (BrokenPipeError, ConnectionResetError):
            pass
        except BaseException:
            proc.kill()
            raise
        finally:
            if not proc.stdin.is_closing():
                proc.stdin.close()

        await proc.wait()
        err = await stderr_task
        if proc.returncode != 0:
            raise RuntimeError(err.decode())