from __future__ import annotations
import os
import yt_dlp
from django.conf import settings
from .detector import detect_platform
from .spotify import extract_spotify_info, is_spotify_url
from .pinterest import extract_pinterest_media

def get_cookie_file(platform: str) -> str | None:
    """Returns path to platform cookie file if present."""
    cookie_candidates = [
        settings.COOKIES_DIR / f"{platform}.txt",
        settings.COOKIES_DIR / "cookies.txt",
        settings.COOKIES_DIR / "youtube.txt",
    ]
    for c in cookie_candidates:
        if c.exists() and c.stat().st_size > 0:
            return str(c)
    return None

def extract_media_info(url: str) -> dict:
    """Extracts metadata, thumbnails, available video/audio formats, or playlist items."""
    platform = detect_platform(url)

    # Spotify handled with custom Spotify service
    if platform == 'spotify' or is_spotify_url(url):
        return extract_spotify_info(url)

    cookie_file = get_cookie_file(platform)

    # Pinterest handled with dedicated video & image extractor
    if platform == 'pinterest':
        return extract_pinterest_media(url, cookie_file=cookie_file)

    ydl_opts = {
        'skip_download': True,
        'extract_flat': False,
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['mweb', 'web_embedded', 'android', 'ios']
            }
        },
    }
    if cookie_file:
        ydl_opts['cookiefile'] = cookie_file

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
        except Exception as e:
            raise ValueError(f"Failed to extract info: {str(e)}")

        if not info:
            raise ValueError("No media could be extracted from this URL.")

        title = info.get('title', 'Unknown Title')
        thumbnail = info.get('thumbnail') or (info.get('thumbnails') and info['thumbnails'][-1].get('url')) or ''
        duration = info.get('duration')
        author = info.get('uploader') or info.get('channel') or info.get('creator') or ''

        # Analyze available formats
        formats = info.get('formats', [])
        video_qualities = set()
        has_video = False

        for f in formats:
            vcodec = f.get('vcodec')
            height = f.get('height')
            if vcodec and vcodec != 'none' and height:
                has_video = True
                if height >= 1080:
                    video_qualities.add('1080p')
                elif height >= 720:
                    video_qualities.add('720p')
                elif height >= 480:
                    video_qualities.add('480p')
                elif height >= 360:
                    video_qualities.add('360p')

        # Construct clean format options for frontend
        available_formats = []

        if has_video:
            standard_video_order = ['1080p', '720p', '480p', '360p', 'Best Available']
            for q in standard_video_order:
                if q in video_qualities or q == 'Best Available' and not video_qualities:
                    available_formats.append({
                        'id': f"video_{q.lower().replace(' ', '_')}",
                        'label': f"Video MP4 ({q})",
                        'type': 'video',
                        'quality': q,
                        'ext': 'mp4',
                    })

            # Audio formats for video
            available_formats.extend([
                {'id': 'audio_mp3_320k', 'label': 'Audio MP3 (320 kbps High)', 'type': 'audio', 'quality': '320k', 'ext': 'mp3'},
                {'id': 'audio_mp3_192k', 'label': 'Audio MP3 (192 kbps Standard)', 'type': 'audio', 'quality': '192k', 'ext': 'mp3'},
                {'id': 'audio_mp3_128k', 'label': 'Audio MP3 (128 kbps Light)', 'type': 'audio', 'quality': '128k', 'ext': 'mp3'},
                {'id': 'audio_m4a', 'label': 'Audio M4A / AAC', 'type': 'audio', 'quality': 'original', 'ext': 'm4a'},
            ])

        # If it's an image post or carousel (no video)
        if not has_video:
            available_formats.append({
                'id': 'image_original',
                'label': 'High Quality Photo (JPG)',
                'type': 'image',
                'quality': 'original',
                'ext': 'jpg',
                'direct_url': thumbnail,
            })
        elif thumbnail:
            # Also offer cover image for video posts
            available_formats.append({
                'id': 'image_cover',
                'label': 'Cover Photo / Thumbnail (JPG)',
                'type': 'image',
                'quality': 'original',
                'ext': 'jpg',
                'direct_url': thumbnail,
            })

        return {
            'platform': platform,
            'title': title,
            'thumbnail': thumbnail,
            'duration': duration,
            'author': author,
            'url': url,
            'is_playlist': False,
            'formats': available_formats,
        }
