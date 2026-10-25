from __future__ import annotations
import sys
import logging
from django.conf import settings
from telegram import BotCommand, MenuButtonCommands
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from .handlers import (
    start_command,
    help_command,
    report_command,
    handle_text_message,
    handle_callback_query,
)

logger = logging.getLogger(__name__)


async def post_init(application: Application) -> None:
    """Configures bot commands and enables the native Telegram Menu Button."""
    commands = [
        BotCommand("start", "Start bot & welcome menu"),
        BotCommand("help", "Help guide & supported platforms"),
        BotCommand("report", "Report a bug or issue to developer"),
    ]
    try:
        await application.bot.set_my_commands(commands)
        await application.bot.set_chat_menu_button(menu_button=MenuButtonCommands())
        logger.info("Telegram Menu Button and commands successfully registered.")
    except Exception as exc:
        logger.warning("Failed to register Telegram Menu Button or commands: %s", exc)


def run_bot() -> None:
    """Builds and starts the Telegram bot long-polling loop."""
    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
    if not token:
        logger.error(
            "TELEGRAM_BOT_TOKEN is not configured! Please provide your Telegram bot token in the .env file."
        )
        sys.exit(1)

    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

    logger.info("Starting U-Loader Telegram Bot...")

    application = (
        ApplicationBuilder()
        .token(token)
        .post_init(post_init)
        .read_timeout(300)
        .write_timeout(300)
        .connect_timeout(60)
        .pool_timeout(60)
        .build()
    )

    # Command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("report", report_command))

    # Text message handler for media URLs
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))

    # Inline keyboard callback query handler (formats, cancel, 1-click bug reports)
    application.add_handler(CallbackQueryHandler(handle_callback_query))

    logger.info("U-Loader Telegram Bot successfully initialized and polling for updates.")
    application.run_polling(drop_pending_updates=True)
