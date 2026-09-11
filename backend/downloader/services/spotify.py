from __future__ import annotations
import os
import re
import json
import zipfile
import requests
import yt_dlp
from pathlib import Path
from django.conf import settings
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC, error as ID3Error

SPOTIFY_URL_REGEX = r'(?:open\.spotify\.com/(track|playlist|album)/|spotify:(track|playlist|album):)([a-zA-Z0-9]+)'

def is_spotify_url(url: str) -> bool:
    return bool(re.search(SPOTIFY_URL_REGEX, url))

def parse_spotify_url(url: str) -> tuple[str, str]:
    """Returns (entity_type, entity_id), e.g. ('track', '4cOdK2wGUTYLY946tQ157V')"""
    match = re.search(SPOTIFY_URL_REGEX, url)
    if not match:
        raise ValueError("Invalid Spotify URL")
    entity_type = match.group(1) or match.group(2)
    entity_id = match.group(3)
    return entity_type, entity_id

def get_spotify_client():
    """Returns authenticated spotipy client if credentials exist, else None."""
    client_id = getattr(settings, 'SPOTIFY_CLIENT_ID', None)
    client_secret = getattr(settings, 'SPOTIFY_CLIENT_SECRET', None)
    if client_id and client_secret:
        try:
            import spotipy
            from spotipy.oauth2 import SpotifyClientCredentials
            return spotipy.Spotify(auth_manager=SpotifyClientCredentials(
                client_id=client_id,
                client_secret=client_secret
            ))
        except Exception:
            return None
    return None

def fetch_spotify_public_token() -> str | None:
    """Fetches an anonymous web client access token from Spotify's open web player."""
    try:
        res = requests.get(
            'https://open.spotify.com/get_access_token?reason=transport&productType=web_player',
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'},
            timeout=8
        )
        if res.status_code == 200:
            return res.json().get('accessToken')
    except Exception:
        pass
    return None

def extract_spotify_info(url: str) -> dict:
    """Extracts metadata from a Spotify track, playlist, or album."""
    entity_type, entity_id = parse_spotify_url(url)
    sp = get_spotify_client()

    if sp:
        try:
            return _extract_with_spotipy(sp, entity_type, entity_id, url)
        except Exception:
            pass

    # Embed extraction (zero-auth, extracts full tracklist directly from Spotify embed)
    try:
        embed_data = _extract_with_embed(entity_type, entity_id, url)
        if embed_data and (not embed_data.get('is_playlist') or embed_data.get('track_count', 0) > 0):
            return embed_data
    except Exception:
        pass

    # Fallback to public API / web token
    token = fetch_spotify_public_token()
    if token:
        try:
            return _extract_with_token(token, entity_type, entity_id, url)
        except Exception:
            pass

    # Final fallback: oEmbed
    return _extract_with_oembed(entity_type, entity_id, url)

def _extract_with_spotipy(sp, entity_type: str, entity_id: str, url: str) -> dict:
    if entity_type == 'track':
        track = sp.track(entity_id)
        artists = ", ".join(a['name'] for a in track['artists'])
        cover = track['album']['images'][0]['url'] if track['album']['images'] else ''
        return {
            'platform': 'spotify',
            'title': f"{artists} - {track['name']}",
            'author': artists,
            'thumbnail': cover,
            'duration': int(track['duration_ms'] / 1000),
            'url': url,
            'is_playlist': False,
            'formats': [
                {'id': 'audio_mp3_320k', 'label': 'MP3 (320 kbps High Quality)', 'type': 'audio', 'quality': '320k', 'ext': 'mp3'},
                {'id': 'audio_mp3_192k', 'label': 'MP3 (192 kbps Standard)', 'type': 'audio', 'quality': '192k', 'ext': 'mp3'},
            ]
        }
    elif entity_type in ['playlist', 'album']:
        if entity_type == 'playlist':
            data = sp.playlist(entity_id)
            items = data['tracks']['items']
            tracks = []
            for idx, item in enumerate(items):
                t = item.get('track')
                if not t:
                    continue
                art = ", ".join(a['name'] for a in t.get('artists', []))
                cover = t['album']['images'][0]['url'] if t.get('album', {}).get('images') else ''
                tracks.append({
                    'id': t['id'] or f"track_{idx}",
                    'title': t['name'],
                    'artist': art,
                    'duration': int(t['duration_ms'] / 1000) if t.get('duration_ms') else 0,
                    'thumbnail': cover,
                    'query': f"{art} - {t['name']} audio"
                })
        else: # album
            data = sp.album(entity_id)
            cover = data['images'][0]['url'] if data['images'] else ''
            art = ", ".join(a['name'] for a in data.get('artists', []))
            tracks = []
            for idx, t in enumerate(data['tracks']['items']):
                track_art = ", ".join(a['name'] for a in t.get('artists', [])) or art
                tracks.append({
                    'id': t['id'] or f"track_{idx}",
                    'title': t['name'],
                    'artist': track_art,
                    'duration': int(t['duration_ms'] / 1000) if t.get('duration_ms') else 0,
                    'thumbnail': cover,
                    'query': f"{track_art} - {t['name']} audio"
                })

        return {
            'platform': 'spotify',
            'title': data.get('name', 'Spotify Playlist'),
            'author': data.get('owner', {}).get('display_name', '') if entity_type == 'playlist' else art,
            'thumbnail': data['images'][0]['url'] if data.get('images') else '',
            'url': url,
            'is_playlist': True,
            'track_count': len(tracks),
            'tracks': tracks,
            'formats': [
                {'id': 'spotify_zip_320k', 'label': 'Download All as ZIP (320 kbps)', 'type': 'playlist', 'quality': '320k', 'ext': 'zip'},
                {'id': 'spotify_zip_192k', 'label': 'Download All as ZIP (192 kbps)', 'type': 'playlist', 'quality': '192k', 'ext': 'zip'},
            ]
        }

def _extract_with_token(token: str, entity_type: str, entity_id: str, url: str) -> dict:
    headers = {'Authorization': f'Bearer {token}'}
    if entity_type == 'track':
        res = requests.get(f'https://api.spotify.com/v1/tracks/{entity_id}', headers=headers, timeout=10)
        res.raise_for_status()
        data = res.json()
        artists = ", ".join(a['name'] for a in data['artists'])
        cover = data['album']['images'][0]['url'] if data['album']['images'] else ''
        return {
            'platform': 'spotify',
            'title': f"{artists} - {data['name']}",
            'author': artists,
            'thumbnail': cover,
            'duration': int(data['duration_ms'] / 1000),
            'url': url,
            'is_playlist': False,
            'formats': [
                {'id': 'audio_mp3_320k', 'label': 'MP3 (320 kbps High Quality)', 'type': 'audio', 'quality': '320k', 'ext': 'mp3'},
                {'id': 'audio_mp3_192k', 'label': 'MP3 (192 kbps Standard)', 'type': 'audio', 'quality': '192k', 'ext': 'mp3'},
            ]
        }
    elif entity_type in ['playlist', 'album']:
        endpoint = f'https://api.spotify.com/v1/playlists/{entity_id}' if entity_type == 'playlist' else f'https://api.spotify.com/v1/albums/{entity_id}'
        res = requests.get(endpoint, headers=headers, timeout=10)
        res.raise_for_status()
        data = res.json()

        cover = data['images'][0]['url'] if data.get('images') else ''
        tracks = []
        raw_items = data['tracks']['items'] if entity_type == 'album' else [i['track'] for i in data['tracks']['items'] if i.get('track')]
        for idx, t in enumerate(raw_items):
            art = ", ".join(a['name'] for a in t.get('artists', []))
            track_cover = t.get('album', {}).get('images', [{}])[0].get('url', cover) if entity_type == 'playlist' else cover
            tracks.append({
                'id': t.get('id') or f"track_{idx}",
                'title': t['name'],
                'artist': art,
                'duration': int(t['duration_ms'] / 1000) if t.get('duration_ms') else 0,
                'thumbnail': track_cover,
                'query': f"{art} - {t['name']} audio"
            })

        return {
            'platform': 'spotify',
            'title': data.get('name', 'Spotify Collection'),
            'author': data.get('owner', {}).get('display_name', '') if entity_type == 'playlist' else 'Spotify',
            'thumbnail': cover,
            'url': url,
            'is_playlist': True,
            'track_count': len(tracks),
            'tracks': tracks,
            'formats': [
                {'id': 'spotify_zip_320k', 'label': 'Download All as ZIP (320 kbps)', 'type': 'playlist', 'quality': '320k', 'ext': 'zip'},
                {'id': 'spotify_zip_192k', 'label': 'Download All as ZIP (192 kbps)', 'type': 'playlist', 'quality': '192k', 'ext': 'zip'},
            ]
        }

def _extract_with_embed(entity_type: str, entity_id: str, url: str) -> dict:
    """Extracts metadata and tracks directly from Spotify's embedded Next.js state."""
    embed_url = f"https://open.spotify.com/embed/{entity_type}/{entity_id}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    res = requests.get(embed_url, headers=headers, timeout=10)
    res.raise_for_status()

    match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', res.text, re.DOTALL)
    if not match:
        raise ValueError("Spotify embed data not found")

    data = json.loads(match.group(1))
    entity = data.get('props', {}).get('pageProps', {}).get('state', {}).get('data', {}).get('entity', {})
    if not entity:
        raise ValueError("Spotify entity payload empty")

    name = entity.get('name') or entity.get('title') or 'Spotify Collection'
    cover = ''
    if entity.get('coverArt') and entity['coverArt'].get('sources'):
        cover = entity['coverArt']['sources'][0].get('url')
    elif entity.get('visualIdentity', {}).get('image'):
        cover = entity['visualIdentity']['image'][0].get('url')

    is_playlist = entity_type in ['playlist', 'album']

    if is_playlist:
        raw_tracks = entity.get('trackList', [])
        tracks = []
        for idx, t in enumerate(raw_tracks):
            track_id = t.get('uri', '').split(':')[-1] or f"track_{idx}"
            artist = t.get('subtitle', '').replace('\xa0', ' ') or 'Unknown Artist'
            t_title = t.get('title', 'Unknown Title')
            duration = int(t.get('duration', 0) / 1000)
            tracks.append({
                'id': track_id,
                'title': t_title,
                'artist': artist,
                'duration': duration,
                'thumbnail': cover,
                'query': f"{artist} - {t_title} audio"
            })

        return {
            'platform': 'spotify',
            'title': name,
            'author': entity.get('subtitle') or 'Spotify',
            'thumbnail': cover,
            'url': url,
            'is_playlist': True,
            'track_count': len(tracks),
            'tracks': tracks,
            'formats': [
                {'id': 'spotify_zip_320k', 'label': 'Download All as ZIP (320 kbps)', 'type': 'playlist', 'quality': '320k', 'ext': 'zip'},
                {'id': 'spotify_zip_192k', 'label': 'Download All as ZIP (192 kbps)', 'type': 'playlist', 'quality': '192k', 'ext': 'zip'},
            ]
        }
    else:
        artists = ', '.join(a['name'] for a in entity.get('artists', [])) if entity.get('artists') else (entity.get('subtitle') or '')
        return {
            'platform': 'spotify',
            'title': f"{artists} - {name}" if artists else name,
            'author': artists,
            'thumbnail': cover,
            'duration': int(entity.get('duration', 0) / 1000),
            'url': url,
            'is_playlist': False,
            'formats': [
                {'id': 'audio_mp3_320k', 'label': 'MP3 (320 kbps High Quality)', 'type': 'audio', 'quality': '320k', 'ext': 'mp3'},
                {'id': 'audio_mp3_192k', 'label': 'MP3 (192 kbps Standard)', 'type': 'audio', 'quality': '192k', 'ext': 'mp3'},
            ]
        }

def _extract_with_oembed(entity_type: str, entity_id: str, url: str) -> dict:
    """Zero-configuration fallback using Spotify oEmbed endpoint."""
    res = requests.get(f'https://open.spotify.com/oembed?url={url}', timeout=8)
    res.raise_for_status()
    data = res.json()
    title = data.get('title', 'Spotify Media')
    thumbnail = data.get('thumbnail_url', '')

    is_playlist = entity_type in ['playlist', 'album']
    return {
        'platform': 'spotify',
        'title': title,
        'author': 'Spotify',
        'thumbnail': thumbnail,
        'duration': 0,
        'url': url,
        'is_playlist': is_playlist,
        'track_count': 1 if not is_playlist else 0,
        'tracks': [],
        'formats': [
            {'id': 'audio_mp3_320k', 'label': 'MP3 (320 kbps High Quality)', 'type': 'audio', 'quality': '320k', 'ext': 'mp3'}
        ]
    }

def download_and_tag_spotify_track(
    title: str,
    artist: str,
    output_dir: Path,
    thumbnail_url: str = '',
    quality: str = '320k',
    progress_callback = None
) -> Path:
    """Downloads matching audio from YouTube via ytsearch, encodes to MP3, and tags with ID3 metadata."""
    query = f"ytsearch1:{artist} - {title} official audio"
    clean_filename = re.sub(r'[\\/*?:"<>|]', "", f"{artist} - {title}")[:120]
    mp3_path = output_dir / f"{clean_filename}.mp3"

    bitrate = '320' if '320' in quality else '192'

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': str(output_dir / f"{clean_filename}.%(ext)s"),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': bitrate,
        }],
        'quiet': True,
        'no_warnings': True,
        'default_search': 'ytsearch',
        'extractor_args': {
            'youtube': {
                'player_client': ['mweb', 'web_embedded', 'ios', 'android', 'web']
            }
        },
    }

    if progress_callback:
        ydl_opts['progress_hooks'] = [progress_callback]

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([query])

    # Tag with ID3 metadata (Artist, Title, Album)
    if mp3_path.exists():
        try:
            audio = EasyID3(str(mp3_path))
        except ID3Error:
            audio = EasyID3()
            audio.save(str(mp3_path))

        audio['title'] = title
        audio['artist'] = artist
        audio.save()

        # Embed cover art if thumbnail is available
        if thumbnail_url:
            try:
                img_res = requests.get(thumbnail_url, timeout=10)
                if img_res.status_code == 200:
                    id3 = ID3(str(mp3_path))
                    id3.add(APIC(
                        encoding=3, # UTF-8
                        mime='image/jpeg',
                        type=3, # Cover (front)
                        desc='Cover',
                        data=img_res.content
                    ))
                    id3.save()
            except Exception:
                pass

    return mp3_path
