import os
from datetime import timedelta
from django.utils import timezone
from django.http import FileResponse, Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError

from .models import DownloadTask, MediaInfoCache
from .serializers import (
    DownloadTaskSerializer,
    MediaInfoRequestSerializer,
    DownloadRequestSerializer,
)
from .services.extractor import extract_media_info
from .services.detector import detect_platform
from .tasks import process_download_task

class HealthCheckView(APIView):
    """Health check endpoint for Docker and reverse proxies."""
    def get(self, request):
        return Response({
            "status": "healthy",
            "service": "u-loader-api",
            "timestamp": timezone.now().isoformat()
        })


class MediaInfoView(APIView):
    """Fetches media metadata and available formats for a given URL."""
    def post(self, request):
        serializer = MediaInfoRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        url = serializer.validated_data['url'].strip()

        # Check Cache
        cached = MediaInfoCache.objects.filter(url=url).first()
        if cached and cached.is_valid():
            # Invalidate stale cache if a playlist/album was saved with 0 tracks
            if cached.data.get('is_playlist') and not cached.data.get('tracks'):
                cached.delete()
            else:
                return Response(cached.data)

        try:
            info = extract_media_info(url)
            # Only store in cache if it's not an empty playlist
            if not info.get('is_playlist') or info.get('tracks'):
                MediaInfoCache.objects.update_or_create(
                    url=url,
                    defaults={
                        'platform': info.get('platform', 'generic'),
                        'data': info,
                        'expires_at': timezone.now() + timedelta(hours=1)
                    }
                )
            return Response(info)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class CreateDownloadTaskView(APIView):
    """Enqueues an asynchronous media download job."""
    def post(self, request):
        serializer = DownloadRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        url = serializer.validated_data['url'].strip()
        media_type = serializer.validated_data['media_type']
        format_id = serializer.validated_data.get('format_id', 'best')
        title = serializer.validated_data.get('title', '')
        selected_tracks = serializer.validated_data.get('selected_tracks', [])

        platform = detect_platform(url)

        # Create DownloadTask instance
        task = DownloadTask.objects.create(
            url=url,
            platform=platform,
            media_type=media_type,
            format_id=format_id,
            title=title,
            status='pending',
            progress_message='Task queued'
        )

        # Dispatch async Celery worker task
        process_download_task.delay(str(task.id), selected_tracks=selected_tracks)

        return Response(
            {
                "task_id": str(task.id),
                "status": task.status,
                "message": "Download task queued successfully"
            },
            status=status.HTTP_202_ACCEPTED
        )


class TaskStatusView(APIView):
    """Returns real-time progress and details of a download task."""
    def get(self, request, task_id):
        try:
            task = DownloadTask.objects.get(id=task_id)
        except (DownloadTask.DoesNotExist, ValueError):
            return Response(
                {"error": "Task not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = DownloadTaskSerializer(task, context={'request': request})
        return Response(serializer.data)


class FileDownloadStreamView(APIView):
    """Streams the completed downloaded file directly to the user's browser."""
    def get(self, request, task_id):
        try:
            task = DownloadTask.objects.get(id=task_id)
        except (DownloadTask.DoesNotExist, ValueError):
            raise Http404("Task not found")

        if task.status != 'completed' or not task.file_path:
            return Response(
                {"error": "File is not ready or failed processing."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not os.path.exists(task.file_path):
            return Response(
                {"error": "File has expired or was removed from server."},
                status=status.HTTP_410_GONE
            )

        response = FileResponse(
            open(task.file_path, 'rb'),
            as_attachment=True,
            filename=task.file_name or os.path.basename(task.file_path)
        )
        return response
