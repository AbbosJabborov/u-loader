from __future__ import annotations
import re
import html as html_lib
import urllib.parse
import requests
import yt_dlp
from pathlib import Path

def extract_pinterest_media(url: str, cookie_file: str | None = None) -> dict:
    """Extracts media from Pinterest video pins or high-res image pins."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }

    # Resolve shortlinks like pin.it
    try:
        r = requests.get(url, headers=headers, allow_redirects=True, timeout=12)
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
                available_formats = [
                    {'id': 'video_720p', 'label': 'Video MP4 (HD)', 'type': 'video', 'quality': '720p', 'ext': 'mp4'},
                    {'id': 'audio_mp3_320k', 'label': 'Audio MP3 (320 kbps)', 'type': 'audio', 'quality': '320k', 'ext': 'mp3'}
                ]
                if thumbnail:
                    available_formats.append({
                        'id': 'image_cover',
                        'label': 'Cover Photo / Thumbnail (JPG)',
                        'type': 'image',
                        'quality': 'original',
                        'ext': 'jpg',
                        'direct_url': thumbnail,
                    })
                return {
                    'platform': 'pinterest',
                    'title': title,
                    'thumbnail': thumbnail,
                    'duration': info.get('duration'),
                    'author': info.get('uploader') or 'Pinterest',
                    'url': final_url,
                    'is_playlist': False,
                    'formats': available_formats
                }
    except Exception:
        pass

    # Second attempt: Extract high-resolution image pin
    if not html:
        r = requests.get(final_url, headers=headers, allow_redirects=True, timeout=12)
        html = r.text

    title_m = re.search(r'<title>([^<]+)</title>', html)
    raw_title = title_m.group(1).split('|')[0].split('-')[0].strip() if title_m else 'Pinterest Image'
    title = html_lib.unescape(raw_title)

    candidates: list[str] = []

    # 1. Check og:image meta tags
    og_imgs = re.findall(r'<meta[^>]+property=[\'"]og:image[\'"][^>]+content=[\'"]([^\'"]+)[\'"]', html, re.IGNORECASE)
    if not og_imgs:
        og_imgs = re.findall(r'<meta[^>]+content=[\'"]([^\'"]+)[\'"][^>]+property=[\'"]og:image[\'"]', html, re.IGNORECASE)

    for img in og_imgs:
        if 'pinimg.com' in img and 'd53b014d' not in img:
            candidates.append(re.sub(r'/(?:\d+x|\d+p)/', '/originals/', img))

    # 2. Check relay completed request scripts in HTML
    relay_matches = re.findall(r'data-relay-completed-request="true"[^>]*>(.*?)</script>', html, re.DOTALL)
    for m in relay_matches:
        decoded = urllib.parse.unquote(m)
        orig_matches = re.findall(r'https://i\.pinimg\.com/originals/[a-f0-9/]+\.(?:jpg|png|webp)', decoded)
        for o in orig_matches:
            if 'd53b014d' not in o and o not in candidates:
                candidates.append(o)

    # 3. Check regex across entire HTML
    html_origs = re.findall(r'https://i\.pinimg\.com/originals/[a-f0-9/]+\.(?:jpg|png|webp)', html)
    for o in html_origs:
        if 'd53b014d' not in o and o not in candidates:
            candidates.append(o)

    # Filter out sprite sheets, avatars, and non-content images
    filtered_candidates = [
        c for c in candidates
        if not any(token in c for token in ('d53b014d', 'logo', 'favicon', 'webapp', '_RS', 'custom_covers', 'upload/'))
    ]

    selected_img = filtered_candidates[0] if filtered_candidates else (candidates[0] if candidates else None)

    if selected_img:
        ext = 'png' if selected_img.endswith('.png') else ('webp' if selected_img.endswith('.webp') else 'jpg')
        return {
            'platform': 'pinterest',
            'title': title,
            'thumbnail': selected_img,
            'duration': None,
            'author': 'Pinterest',
            'url': final_url,
            'is_playlist': False,
            'formats': [
                {
                    'id': 'image_original',
                    'label': f'Original High Quality Photo ({ext.upper()})',
                    'type': 'image',
                    'quality': 'original',
                    'ext': ext,
                    'direct_url': selected_img,
                }
            ]
        }

    raise ValueError("Could not extract video or image from this Pinterest link.")
