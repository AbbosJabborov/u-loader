from __future__ import annotations
import os
import re
import yt_dlp
from pathlib import Path
from django.conf import settings
from .extractor import get_cookie_file
from .detector import detect_platform

def sanitize_filename(name: str) -> str:
    """Sanitizes filename for cross-platform compatibility."""
    return re.sub(r'[\\/*?:"<>|]', "_", name).strip()[:180]

def build_ydl_options(
    output_dir: Path,
    media_type: str,
    format_id: str,
    platform: str,
    progress_callback = None
) -> dict:
    cookie_file = get_cookie_file(platform)
    out_template = str(output_dir / "%(title).150s_%(id)s.%(ext)s")

    opts = {
        'outtmpl': out_template,
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
    }

    if cookie_file:
        opts['cookiefile'] = cookie_file

    if progress_callback:
        opts['progress_hooks'] = [progress_callback]

    # Video download configurations
    if media_type == 'video':
        if '1080' in format_id:
            opts['format'] = 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=1080]+bestaudio/best[height<=1080]/best'
        elif '720' in format_id:
            opts['format'] = 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=720]+bestaudio/best[height<=720]/best'
        elif '480' in format_id:
            opts['format'] = 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=480]+bestaudio/best[height<=480]/best'
        elif '360' in format_id:
            opts['format'] = 'bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=360]+bestaudio/best[height<=360]/best'
        else:
            opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best[ext=mp4]/best'

        opts['merge_output_format'] = 'mp4'

    # Audio download configurations
    elif media_type == 'audio':
        bitrate = '320' if '320' in format_id else ('128' if '128' in format_id else '192')
        codec = 'm4a' if 'm4a' in format_id else 'mp3'

        opts['format'] = 'bestaudio/best'
        opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': codec,
            'preferredquality': bitrate,
        }]

    # Platform-specific tweaks
    if platform == 'tiktok':
        # TikTok: ensures unwatermarked stream extraction
        opts['format'] = 'best[ext=mp4]/best'
    elif platform == 'instagram':
        opts['format'] = 'best[ext=mp4]/best'

    return opts

def execute_media_download(
    url: str,
    output_dir: Path,
    media_type: str = 'video',
    format_id: str = 'best',
    progress_callback = None
) -> Path:
    """Downloads media from URL using yt-dlp and returns the final saved Path."""
    platform = detect_platform(url)
    opts = build_ydl_options(output_dir, media_type, format_id, platform, progress_callback)

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)

        # Handle post-processed extensions (e.g. mp3 conversion)
        expected_ext = 'mp3' if (media_type == 'audio' and 'm4a' not in format_id) else ('m4a' if 'm4a' in format_id else 'mp4')
        path_obj = Path(filename)
        candidate = path_obj.with_suffix(f".{expected_ext}")

        if candidate.exists():
            return candidate
        if path_obj.exists():
            return path_obj

        # Scan folder for newly created file with same stem
        for f in output_dir.glob(f"{path_obj.stem}.*"):
            return f

        raise FileNotFoundError("Downloaded file could not be located after completion.")
