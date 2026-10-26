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


class TelegramBotTestCase(TestCase):
    def test_duration_formatter(self):
        from .bot.keyboards import format_duration
        self.assertEqual(format_duration(65), "01:05")
        self.assertEqual(format_duration(3665), "01:01:05")
        self.assertEqual(format_duration(None), "")

    def test_keyboard_builder(self):
        from .bot.keyboards import build_format_keyboard
        formats = [
            {'id': 'video_1080p', 'type': 'video', 'quality': '1080p', 'ext': 'mp4'},
            {'id': 'audio_mp3_320k', 'type': 'audio', 'quality': '320k', 'ext': 'mp3'},
            {'id': 'image_cover', 'type': 'image', 'quality': 'original', 'ext': 'jpg'},
        ]
        keyboard = build_format_keyboard("session123", formats)
        self.assertIsNotNone(keyboard)
        # Check that buttons contain callback_data with session id
        button_data = [btn.callback_data for row in keyboard.inline_keyboard for btn in row]
        self.assertIn("dl:session123:0", button_data)
        self.assertIn("dl:session123:1", button_data)
        self.assertIn("dl:session123:2", button_data)
        self.assertIn("cancel:session123", button_data)

    def test_progress_bar_helper(self):
        from .bot.handlers import make_progress_bar
        bar_50 = make_progress_bar(50, length=10)
        self.assertEqual(bar_50, "▰▰▰▰▰▱▱▱▱▱")
        bar_100 = make_progress_bar(100, length=10)
        self.assertEqual(bar_100, "▰▰▰▰▰▰▰▰▰▰")
        bar_0 = make_progress_bar(0, length=10)
        self.assertEqual(bar_0, "▱▱▱▱▱▱▱▱▱▱")

    def test_error_keyboards(self):
        from .bot.keyboards import build_error_keyboard, build_reported_keyboard
        err_kb = build_error_keyboard("err_token_99")
        self.assertEqual(err_kb.inline_keyboard[0][0].callback_data, "rep_err:err_token_99")

        rep_kb = build_reported_keyboard()
        self.assertEqual(rep_kb.inline_keyboard[0][0].callback_data, "none")

    def test_spotify_playlist_keyboard(self):
        from .bot.keyboards import build_format_keyboard
        from .services.spotify import get_spotify_playlist_formats

        formats = get_spotify_playlist_formats()
        self.assertEqual(len(formats), 2)
        self.assertEqual(formats[0]['type'], 'playlist_tracks')
        self.assertEqual(formats[1]['type'], 'playlist')

        kb = build_format_keyboard("spot_sess_1", formats)
        button_labels = [btn.text for row in kb.inline_keyboard for btn in row]
        self.assertTrue(any("Each Song" in label for label in button_labels))
        self.assertTrue(any("ZIP" in label for label in button_labels))

    def test_audio_compressor(self):
        from .services.audio import compress_audio_to_size
        import subprocess
        from pathlib import Path

        test_path = Path("/tmp/test_unit_audio.mp3")
        try:
            # Generate a 2 second silent mp3
            subprocess.run(
                ['ffmpeg', '-y', '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo', '-t', '2', '-b:a', '320k', str(test_path)],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            compressed = compress_audio_to_size(test_path, max_bytes=100000, bitrates=['96k'])
            self.assertIsNotNone(compressed)
            self.assertTrue(compressed.exists())
            self.assertLessEqual(compressed.stat().st_size, 100000)
            compressed.unlink(missing_ok=True)
        finally:
            test_path.unlink(missing_ok=True)

    def test_new_platform_detections(self):
        # Instagram stories, reels, share
        self.assertEqual(detect_platform("https://www.instagram.com/stories/natgeo/31234567890/"), "instagram")
        self.assertEqual(detect_platform("https://www.instagram.com/reels/D123456789/"), "instagram")
        self.assertEqual(detect_platform("https://www.instagram.com/share/p/C123456789/"), "instagram")
        # TikTok photo post
        self.assertEqual(detect_platform("https://www.tiktok.com/@creator/photo/7123456789012345678"), "tiktok")

    def test_serializer_carousel_and_image(self):
        from .serializers import DownloadRequestSerializer
        data_image = {'url': 'https://www.pinterest.com/pin/123/', 'media_type': 'image'}
        s_img = DownloadRequestSerializer(data=data_image)
        self.assertTrue(s_img.is_valid())

        data_carousel = {'url': 'https://www.instagram.com/p/123/', 'media_type': 'carousel', 'format_id': 'carousel_zip'}
        s_car = DownloadRequestSerializer(data=data_carousel)
        self.assertTrue(s_car.is_valid())

    def test_keyboard_carousel_labels(self):
        from .bot.keyboards import build_format_keyboard
        formats = [
            {'id': 'carousel_zip', 'label': '📦 Download All Items (ZIP - 5 items)', 'type': 'image', 'quality': '5 items', 'ext': 'zip'},
            {'id': 'image_original', 'label': '🖼️ Primary Photo / Cover (HD JPG)', 'type': 'image', 'quality': 'original', 'ext': 'jpg'},
        ]
        kb = build_format_keyboard("sess_carousel", formats)
        button_labels = [btn.text for row in kb.inline_keyboard for btn in row]
        self.assertTrue(any("Download All Items (ZIP - 5 items)" in l for l in button_labels))
        self.assertTrue(any("Primary Photo / Cover (HD JPG)" in l for l in button_labels))
