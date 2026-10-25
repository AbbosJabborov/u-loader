import warnings
warnings.filterwarnings("ignore")

try:
    import yt_dlp
    yt_dlp.YoutubeDL.deprecated_feature = lambda *args, **kwargs: None
except Exception:
    pass

from django.core.management.base import BaseCommand
from downloader.bot.runner import run_bot

class Command(BaseCommand):
    help = "Runs the U-Loader Telegram Bot service with long polling"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Launching U-Loader Telegram Bot service..."))
        try:
            run_bot()
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("Telegram Bot terminated gracefully by user."))
