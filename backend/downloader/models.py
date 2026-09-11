import os
import uuid
from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.conf import settings

class DownloadTask(models.Model):
    PLATFORM_CHOICES = [
        ('youtube', 'YouTube'),
        ('instagram', 'Instagram'),
        ('tiktok', 'TikTok'),
        ('pinterest', 'Pinterest'),
        ('spotify', 'Spotify'),
        ('generic', 'Generic / Other'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('downloading', 'Downloading'),
        ('processing', 'Processing / Converting'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    url = models.URLField(max_length=1000)
    platform = models.CharField(max_length=30, choices=PLATFORM_CHOICES, default='generic')
    media_type = models.CharField(max_length=20, default='video') # video, audio, playlist
    format_id = models.CharField(max_length=50, blank=True, default='best')
    
    title = models.CharField(max_length=500, blank=True, default='')
    thumbnail_url = models.URLField(max_length=1500, blank=True, default='')
    duration = models.IntegerField(null=True, blank=True)
    author = models.CharField(max_length=255, blank=True, default='')

    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    progress = models.FloatField(default=0.0)
    progress_message = models.CharField(max_length=255, blank=True, default='Task initialized')
    
    file_path = models.CharField(max_length=1000, blank=True, default='')
    file_name = models.CharField(max_length=500, blank=True, default='')
    file_size = models.BigIntegerField(null=True, blank=True)
    
    error_message = models.TextField(blank=True, default='')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=settings.FILE_EXPIRATION_MINUTES)
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expires_at if self.expires_at else False

    def delete_file(self):
        """Removes the file from disk if it exists."""
        if self.file_path and os.path.exists(self.file_path):
            try:
                os.remove(self.file_path)
            except OSError:
                pass

    def __str__(self):
        return f"{self.platform.upper()} - {self.title or self.url} [{self.status}]"


class MediaInfoCache(models.Model):
    """Caches extracted metadata so repeated queries don't hit yt-dlp repeatedly."""
    url = models.URLField(max_length=1000, unique=True)
    platform = models.CharField(max_length=30)
    data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_valid(self):
        return timezone.now() < self.expires_at

    def __str__(self):
        return f"Cache: {self.platform} - {self.url}"
