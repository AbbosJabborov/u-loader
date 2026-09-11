from __future__ import annotations
import re
import requests
import yt_dlp
from pathlib import Path

def extract_pinterest_media(url: str, cookie_file: str | None = None) -> dict:
    """Extracts media from Pinterest video pins or high-res image pins."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    # Resolve shortlinks like pin.it
    try:
        r = requests.get(url, headers=headers, allow_redirects=True, timeout=10)
        final_url = r.url
        html = r.text
    except Exception:
        final_url = url
        html = ''

    # First attempt: yt-dlp for video pins
    ydl_opts = {
        'skip_download': True,
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
    }
    if cookie_file:
        ydl_opts['cookiefile'] = cookie_file

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(final_url, download=False)
            formats = info.get('formats', [])
            has_video = any(f.get('vcodec') and f.get('vcodec') != 'none' for f in formats)
            if has_video:
                title = info.get('title') or 'Pinterest Video'
                thumbnail = info.get('thumbnail') or (info.get('thumbnails') and info['thumbnails'][-1].get('url')) or ''
                return {
                    'platform': 'pinterest',
                    'title': title,
                    'thumbnail': thumbnail,
                    'duration': info.get('duration'),
                    'author': info.get('uploader') or 'Pinterest',
                    'url': final_url,
                    'is_playlist': False,
                    'formats': [
                        {'id': 'video_720p', 'label': 'Video MP4 (HD)', 'type': 'video', 'quality': '720p', 'ext': 'mp4'},
                        {'id': 'audio_mp3_320k', 'label': 'Audio MP3 (320 kbps)', 'type': 'audio', 'quality': '320k', 'ext': 'mp3'}
                    ]
                }
    except Exception:
        pass

    # Second attempt: Extract high-resolution image pin
    if not html:
        r = requests.get(final_url, headers=headers, allow_redirects=True, timeout=10)
        html = r.text

    title_m = re.search(r'<title>([^<]+)</title>', html)
    title = title_m.group(1).split('|')[0].strip() if title_m else 'Pinterest Image'

    # Find highest quality image URL in HTML
    imgs = re.findall(r'(https://i\.pinimg\.com/(?:originals|\d+x)/[a-f0-9/]+(?:\.jpg|\.png|\.webp))', html)
    if not imgs:
        imgs = re.findall(r'<meta property=\"og:image\" content=\"([^\"]+)\"', html)

    if imgs:
        orig_img = re.sub(r'/(?:\d+x|\d+p)/', '/originals/', imgs[0])
        ext = 'png' if orig_img.endswith('.png') else ('webp' if orig_img.endswith('.webp') else 'jpg')
        return {
            'platform': 'pinterest',
            'title': title,
            'thumbnail': orig_img,
            'duration': None,
            'author': 'Pinterest',
            'url': final_url,
            'is_playlist': False,
            'formats': [
                {
                    'id': 'image_original',
                    'label': f'Original Image ({ext.upper()})',
                    'type': 'image',
                    'quality': 'original',
                    'ext': ext,
                    'direct_url': orig_img,
                }
            ]
        }

    raise ValueError("Could not extract video or image from this Pinterest link.")
