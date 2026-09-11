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
        'extractor_args': {
            'youtube': {
                'player_client': ['mweb', 'web_embedded', 'ios', 'android', 'web']
            }
        },
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

    # Handle direct image downloads (e.g. Pinterest picture pins or direct image streams)
    if media_type == 'image':
        import requests
        if platform == 'pinterest':
            from .pinterest import extract_pinterest_media
            p_info = extract_pinterest_media(url)
            img_format = next((f for f in p_info.get('formats', []) if f.get('type') == 'image'), None)
            img_url = (img_format and img_format.get('direct_url')) or p_info.get('thumbnail')
            if img_url:
                ext = img_format.get('ext', 'jpg') if img_format else 'jpg'
                title = sanitize_filename(p_info.get('title', 'pinterest_image'))
                out_file = output_dir / f"{title}.{ext}"
                r = requests.get(
                    img_url,
                    headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'},
                    stream=True,
                    timeout=25
                )
                r.raise_for_status()
                with open(out_file, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=65536):
                        f.write(chunk)
                return out_file

    with yt_dlp.YoutubeDL(opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
        except Exception as e:
            # Fallback for image extraction if yt-dlp fails on photo URL
            if media_type == 'image':
                import requests
                from .extractor import extract_media_info
                media_info = extract_media_info(url)
                img_url = media_info.get('thumbnail')
                if img_url:
                    title = sanitize_filename(media_info.get('title', 'image'))
                    out_file = output_dir / f"{title}.jpg"
                    r = requests.get(
                        img_url,
                        headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'},
                        stream=True,
                        timeout=25
                    )
                    r.raise_for_status()
                    with open(out_file, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=65536):
                            f.write(chunk)
                    return out_file
            raise e

        # Handle post-processed extensions (e.g. mp3 conversion)
        expected_ext = 'mp3' if (media_type == 'audio' and 'm4a' not in format_id) else ('m4a' if 'm4a' in format_id else 'mp4')
        path_obj = Path(filename)
        candidate = path_obj.with_suffix(f".{expected_ext}")

        if candidate.exists():
            return candidate
        if path_obj.exists():
            return path_obj

        # Check for any images downloaded in output_dir
        all_files = list(output_dir.iterdir())
        image_files = [f for f in all_files if f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']]
        if len(image_files) > 1:
            # Carousel/multiple images -> bundle into zip
            import zipfile
            zip_path = output_dir / f"{sanitize_filename(info.get('title', 'instagram_post'))}.zip"
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for img_f in image_files:
                    zipf.write(img_f, arcname=img_f.name)
            return zip_path
        elif len(image_files) == 1:
            return image_files[0]

        # Scan folder for newly created file with same stem
        for f in output_dir.glob(f"{path_obj.stem}.*"):
            return f

        if all_files:
            return all_files[0]

        raise FileNotFoundError("Downloaded file could not be located after completion.")
