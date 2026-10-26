from __future__ import annotations
import os
import warnings

warnings.filterwarnings("ignore")

try:
    import yt_dlp
    yt_dlp.YoutubeDL.deprecated_feature = lambda *args, **kwargs: None
except Exception:
    pass
from django.conf import settings
from .detector import detect_platform
from .spotify import extract_spotify_info, is_spotify_url
from .pinterest import extract_pinterest_media

def get_cookie_file(platform: str) -> str | None:
    """Returns path to platform cookie file if present."""
    cookie_candidates = [
        settings.COOKIES_DIR / f"{platform}.txt",
        settings.COOKIES_DIR / "cookies.txt",
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

    # Resolve Instagram /share/ redirect links to canonical URL
    if platform == 'instagram' and '/share/' in url:
        try:
            import requests
            r = requests.head(url, headers={'User-Agent': 'Mozilla/5.0'}, allow_redirects=True, timeout=6)
            if r.url and '/share/' not in r.url:
                url = r.url
        except Exception:
            pass

    # For Instagram & TikTok, allow multi-item carousel / album extraction
    is_multi_platform = platform in ('instagram', 'tiktok')

    ydl_opts = {
        'skip_download': True,
        'extract_flat': False,
        'quiet': True,
        'no_warnings': True,
        'noplaylist': False if is_multi_platform else True,
        'extractor_args': {
            'youtube': {
                'player_client': ['all']
            }
        },
    }
    if cookie_file:
        ydl_opts['cookiefile'] = cookie_file

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
        except Exception as e:
            # Fallback for TikTok photo post: try rewriting /photo/ to /video/
            if platform == 'tiktok' and '/photo/' in url:
                try:
                    fallback_url = url.replace('/photo/', '/video/')
                    info = ydl.extract_info(fallback_url, download=False)
                except Exception:
                    raise ValueError(f"Failed to extract info: {str(e)}")
            else:
                raise ValueError(f"Failed to extract info: {str(e)}")

        if not info:
            raise ValueError("No media could be extracted from this URL.")

        # Check for multi-item post (Instagram carousel, TikTok photo slideshow)
        entries = [e for e in (info.get('entries') or []) if e]
        is_carousel = len(entries) > 1

        title = info.get('title', 'Unknown Title')
        thumbnail = (
            info.get('thumbnail')
            or (entries and entries[0].get('thumbnail'))
            or (info.get('thumbnails') and info['thumbnails'][-1].get('url'))
            or ''
        )
        duration = info.get('duration') or (entries and entries[0].get('duration'))
        author = info.get('uploader') or info.get('channel') or info.get('creator') or ''

        # Collect formats
        available_formats = []

        if is_carousel:
            item_count = len(entries)
            # Check if entries contain video
            carousel_has_video = any(
                any(f.get('vcodec') and f.get('vcodec') != 'none' for f in e.get('formats', []))
                for e in entries
            )

            # 1. Download all items as ZIP bundle
            available_formats.append({
                'id': 'carousel_zip',
                'label': f'📦 Download All Items (ZIP - {item_count} items)',
                'type': 'image',
                'quality': f'{item_count} items',
                'ext': 'zip',
            })

            # 2. Primary Photo / Cover
            if thumbnail:
                available_formats.append({
                    'id': 'image_original',
                    'label': '🖼️ Primary Photo / Cover (HD JPG)',
                    'type': 'image',
                    'quality': 'original',
                    'ext': 'jpg',
                    'direct_url': thumbnail,
                })

            # 3. Video option if video item is included
            if carousel_has_video:
                available_formats.append({
                    'id': 'video_best',
                    'label': '🎬 Video MP4 (Best Quality)',
                    'type': 'video',
                    'quality': 'Best',
                    'ext': 'mp4',
                })

            # 4. Audio option (e.g. background music / audio track)
            available_formats.append({
                'id': 'audio_mp3_320k',
                'label': '🎵 Audio MP3 (320 kbps)',
                'type': 'audio',
                'quality': '320k',
                'ext': 'mp3',
            })

        else:
            # Single item extraction
            formats = info.get('formats', [])
            video_qualities = set()
            has_video = False

            for f in formats:
                vcodec = f.get('vcodec')
                height = f.get('height')
                if vcodec and vcodec != 'none' and height:
                    has_video = True
                    if height >= 2160:
                        video_qualities.add('4K')
                    elif height >= 1440:
                        video_qualities.add('2K')
                    elif height >= 1080:
                        video_qualities.add('1080p')
                    elif height >= 720:
                        video_qualities.add('720p')
                    elif height >= 480:
                        video_qualities.add('480p')
                    elif height >= 360:
                        video_qualities.add('360p')

            if has_video:
                standard_video_order = ['4K', '2K', '1080p', '720p', '480p', '360p']
                found_any = False
                for q in standard_video_order:
                    if q in video_qualities:
                        found_any = True
                        available_formats.append({
                            'id': f"video_{q.lower().replace(' ', '_')}",
                            'label': f"Video MP4 ({q})",
                            'type': 'video',
                            'quality': q,
                            'ext': 'mp4',
                        })

                if not found_any:
                    available_formats.append({
                        'id': 'video_best',
                        'label': 'Video MP4 (Best Quality)',
                        'type': 'video',
                        'quality': 'Best',
                        'ext': 'mp4',
                    })

                available_formats.append({
                    'id': 'audio_mp3_320k',
                    'label': 'Audio MP3 (320 kbps)',
                    'type': 'audio',
                    'quality': '320k',
                    'ext': 'mp3',
                })

            # Image format options
            if not has_video:
                available_formats.append({
                    'id': 'image_original',
                    'label': '🖼️ High Quality Photo (JPG)',
                    'type': 'image',
                    'quality': 'original',
                    'ext': 'jpg',
                    'direct_url': thumbnail,
                })
            elif thumbnail:
                available_formats.append({
                    'id': 'image_cover',
                    'label': '🖼️ Cover Photo / Thumbnail (JPG)',
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
