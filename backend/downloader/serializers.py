from rest_framework import serializers
from .models import DownloadTask

class DownloadTaskSerializer(serializers.ModelSerializer):
    download_url = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = DownloadTask
        fields = [
            'id',
            'url',
            'platform',
            'media_type',
            'format_id',
            'title',
            'thumbnail_url',
            'duration',
            'author',
            'status',
            'progress',
            'progress_message',
            'file_name',
            'file_size',
            'error_message',
            'created_at',
            'expires_at',
            'download_url',
            'is_expired',
        ]
        read_only_fields = fields

    def get_download_url(self, obj):
        if obj.status == 'completed' and obj.file_name:
            request = self.context.get('request')
            path = f"/api/files/{obj.id}/"
            if request:
                return request.build_absolute_uri(path)
            return path
        return None

    def get_is_expired(self, obj):
        return obj.is_expired()


class MediaInfoRequestSerializer(serializers.Serializer):
    url = serializers.URLField(required=True)


class DownloadRequestSerializer(serializers.Serializer):
    url = serializers.URLField(required=True)
    media_type = serializers.ChoiceField(choices=['video', 'audio', 'playlist', 'image'], default='video')
    format_id = serializers.CharField(required=False, default='best', allow_blank=True)
    title = serializers.CharField(required=False, default='', allow_blank=True)
    selected_tracks = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )
