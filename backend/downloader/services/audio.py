from __future__ import annotations
import shutil
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

def compress_audio_to_size(
    input_path: Path,
    max_bytes: int = 48 * 1024 * 1024,
    bitrates: list[str] | None = None
) -> Path | None:
    """
    Downsamples an audio file to a lower bitrate (e.g. 128k, 96k, 64k) using ffmpeg
    so that it fits safely under Telegram's 50 MB upload limit.
    Preserves audio metadata and ID3 tags.
    """
    if bitrates is None:
        bitrates = ['128k', '96k', '64k']

    ffmpeg_bin = shutil.which('ffmpeg') or 'ffmpeg'

    for br in bitrates:
        compressed_path = input_path.with_name(f"{input_path.stem}_{br}.mp3")
        cmd = [
            ffmpeg_bin,
            "-y",
            "-i", str(input_path),
            "-vn",
            "-map_metadata", "0",
            "-acodec", "libmp3lame",
            "-b:a", br,
            str(compressed_path)
        ]
        try:
            subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
                timeout=120
            )
            if compressed_path.exists():
                size = compressed_path.stat().st_size
                logger.info(
                    "Compressed '%s' at bitrate %s -> %s MB",
                    input_path.name,
                    br,
                    round(size / (1024 * 1024), 2)
                )
                if size <= max_bytes:
                    return compressed_path
        except Exception as e:
            logger.warning("Failed to compress '%s' at bitrate %s: %s", input_path.name, br, e)
            continue

    return None
