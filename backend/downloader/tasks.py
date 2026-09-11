import os
import zipfile
import shutil
import time
from pathlib import Path
from celery import shared_task
from django.utils import timezone
from django.conf import settings
from .models import DownloadTask
from .services.detector import detect_platform
from .services.downloader import execute_media_download
from .services.spotify import is_spotify_url, download_and_tag_spotify_track, extract_spotify_info

@shared_task(bind=True)
def process_download_task(self, task_id: str, selected_tracks: list = None):
    """Asynchronous background Celery task to download media and update database status."""
    try:
        task = DownloadTask.objects.get(id=task_id)
    except DownloadTask.DoesNotExist:
        return {"error": "Task not found"}

    downloads_dir = settings.DOWNLOADS_ROOT / str(task.id)
    downloads_dir.mkdir(parents=True, exist_ok=True)

    def progress_hook(d):
        if d['status'] == 'downloading':
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            downloaded = d.get('downloaded_bytes') or 0
            percent = (downloaded / total_bytes * 100) if total_bytes > 0 else 0
            
            # Throttle DB updates to reduce write pressure
            current_time = time.time()
            if not hasattr(progress_hook, 'last_update') or (current_time - progress_hook.last_update) > 0.8:
                progress_hook.last_update = current_time
                task.status = 'downloading'
                task.progress = round(percent, 1)
                speed = d.get('speed')
                speed_str = f"{round(speed / (1024 * 1024), 1)} MB/s" if speed else ""
                task.progress_message = f"Downloading: {round(percent)}% {speed_str}".strip()
                task.save(update_fields=['status', 'progress', 'progress_message', 'updated_at'])

        elif d['status'] == 'finished':
            task.status = 'processing'
            task.progress = 95.0
            task.progress_message = 'Transcoding & finalizing media...'
            task.save(update_fields=['status', 'progress', 'progress_message', 'updated_at'])

    try:
        task.status = 'downloading'
        task.progress_message = 'Starting download...'
        task.save(update_fields=['status', 'progress_message'])

        platform = task.platform
        if not platform or platform == 'generic':
            platform = detect_platform(task.url)
            task.platform = platform

        # Handle Spotify Playlists / Albums
        if platform == 'spotify' and task.media_type == 'playlist':
            task.progress_message = 'Fetching Spotify playlist metadata...'
            task.save(update_fields=['progress_message'])

            spotify_info = extract_spotify_info(task.url)
            tracks = spotify_info.get('tracks', [])

            # Filter selected tracks if specified
            if selected_tracks:
                tracks = [t for t in tracks if t['id'] in selected_tracks]

            total_tracks = len(tracks)
            if total_tracks == 0:
                raise ValueError("No tracks found to download.")

            track_files = []
            for index, t in enumerate(tracks, start=1):
                task.progress = round((index - 1) / total_tracks * 90, 1)
                task.progress_message = f"Downloading track {index}/{total_tracks}: {t['title']}..."
                task.save(update_fields=['progress', 'progress_message'])

                track_path = download_and_tag_spotify_track(
                    title=t['title'],
                    artist=t['artist'],
                    output_dir=downloads_dir,
                    thumbnail_url=t.get('thumbnail', ''),
                    quality=task.format_id
                )
                if track_path and track_path.exists():
                    track_files.append(track_path)

            task.status = 'processing'
            task.progress = 95.0
            task.progress_message = 'Creating ZIP archive of playlist...'
            task.save(update_fields=['status', 'progress', 'progress_message'])

            # Create ZIP bundle
            zip_name = f"{task.title or 'Spotify_Playlist'}.zip"
            zip_path = downloads_dir / zip_name
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in track_files:
                    zipf.write(file_path, arcname=file_path.name)

            final_file = zip_path

        # Handle single Spotify Track
        elif platform == 'spotify' and task.media_type != 'playlist':
            spotify_info = extract_spotify_info(task.url)
            final_file = download_and_tag_spotify_track(
                title=spotify_info.get('title', 'Unknown Track'),
                artist=spotify_info.get('author', ''),
                output_dir=downloads_dir,
                thumbnail_url=spotify_info.get('thumbnail', ''),
                quality=task.format_id,
                progress_callback=progress_hook
            )

        # Handle YouTube, TikTok, Instagram, Pinterest, Generic
        else:
            final_file = execute_media_download(
                url=task.url,
                output_dir=downloads_dir,
                media_type=task.media_type,
                format_id=task.format_id,
                progress_callback=progress_hook
            )

        # Finalize completed task
        if final_file and final_file.exists():
            task.status = 'completed'
            task.progress = 100.0
            task.progress_message = 'Ready for download!'
            task.file_path = str(final_file)
            task.file_name = final_file.name
            task.file_size = final_file.stat().st_size
            task.save()
            return {"status": "success", "task_id": str(task.id), "file": task.file_name}
        else:
            raise FileNotFoundError("Output file was not generated.")

    except Exception as exc:
        task.status = 'failed'
        task.error_message = str(exc)
        task.progress_message = f"Error: {str(exc)}"
        task.save(update_fields=['status', 'error_message', 'progress_message'])
        return {"status": "error", "task_id": str(task.id), "error": str(exc)}


@shared_task
def cleanup_expired_files_task():
    """Periodic Celery Beat task to delete expired files and keep VPS disk clean."""
    now = timezone.now()
    expired_tasks = DownloadTask.objects.filter(expires_at__lt=now)
    deleted_count = 0

    for task in expired_tasks:
        if task.file_path and os.path.exists(task.file_path):
            task.delete_file()
            # If directory is empty, remove it
            parent_dir = Path(task.file_path).parent
            if parent_dir.exists() and not any(parent_dir.iterdir()):
                try:
                    parent_dir.rmdir()
                except OSError:
                    pass
            deleted_count += 1

    # Clean any orphaned directories older than expiration window
    cutoff = time.time() - (settings.FILE_EXPIRATION_MINUTES * 60)
    for folder in settings.DOWNLOADS_ROOT.iterdir():
        if folder.is_dir() and folder.stat().st_mtime < cutoff:
            try:
                shutil.rmtree(folder)
            except OSError:
                pass

    return f"Cleaned up {deleted_count} expired files."
