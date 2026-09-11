from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from .services.detector import detect_platform
from .models import DownloadTask

class PlatformDetectorTestCase(TestCase):
    def test_detect_youtube(self):
        self.assertEqual(detect_platform("https://www.youtube.com/watch?v=dQw4w9WgXcQ"), "youtube")
        self.assertEqual(detect_platform("https://youtu.be/dQw4w9WgXcQ"), "youtube")
        self.assertEqual(detect_platform("https://youtube.com/shorts/3jWRrafh88M"), "youtube")

    def test_detect_instagram(self):
        self.assertEqual(detect_platform("https://www.instagram.com/reel/C123456789/"), "instagram")
        self.assertEqual(detect_platform("https://instagram.com/p/B123456789/"), "instagram")

    def test_detect_tiktok(self):
        self.assertEqual(detect_platform("https://www.tiktok.com/@user/video/7123456789012345678"), "tiktok")
        self.assertEqual(detect_platform("https://vm.tiktok.com/ZM812345/"), "tiktok")

    def test_detect_pinterest(self):
        self.assertEqual(detect_platform("https://www.pinterest.com/pin/123456789012345678/"), "pinterest")
        self.assertEqual(detect_platform("https://pin.it/7x91234"), "pinterest")

    def test_detect_spotify(self):
        self.assertEqual(detect_platform("https://open.spotify.com/track/4cOdK2wGUTYLY946tQ157V"), "spotify")
        self.assertEqual(detect_platform("https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"), "spotify")


class DownloaderAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_health_check(self):
        res = self.client.get('/api/health/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['status'], 'healthy')
        self.assertEqual(res.data['service'], 'u-loader-api')

    def test_task_status_not_found(self):
        import uuid
        res = self.client.get(f'/api/tasks/{uuid.uuid4()}/')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_download_task_creation_model(self):
        task = DownloadTask.objects.create(
            url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            platform="youtube",
            media_type="video",
            format_id="1080p",
            title="Test Video"
        )
        self.assertIsNotNone(task.id)
        self.assertEqual(task.status, "pending")
        self.assertFalse(task.is_expired())
