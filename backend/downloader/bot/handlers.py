from __future__ import annotations
import os
import re
import html
import uuid
import time
import asyncio
import logging
from datetime import datetime
from pathlib import Path

from asgiref.sync import sync_to_async
from django.conf import settings
from django.core.cache import cache
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from downloader.models import DownloadTask
from downloader.services.detector import detect_platform
from downloader.services.extractor import extract_media_info
from downloader.services.spotify import download_and_tag_spotify_track, extract_spotify_info
from downloader.services.audio import compress_audio_to_size
from downloader.tasks import process_download_task, dispatch_download_task
from .keyboards import (
    PLATFORM_ICONS,
    build_format_keyboard,
    build_error_keyboard,
    build_reported_keyboard,
    format_duration,
)

logger = logging.getLogger(__name__)

URL_REGEX = re.compile(r'https?://[^\s<>"]+', re.IGNORECASE)
MAX_TELEGRAM_FILE_SIZE = 50 * 1024 * 1024  # 50 MB Telegram Bot API limit


def make_progress_bar(percent: float, length: int = 10) -> str:
    """Generates a visual text progress bar, e.g. [▰▰▰▰▰▱▱▱▱▱]."""
    clamped = max(0.0, min(100.0, percent))
    filled = int(round(length * clamped / 100))
    return "▰" * filled + "▱" * (length - filled)


def cache_session(session_id: str, data: dict, timeout: int = 1800) -> None:
    cache.set(f"tg_session:{session_id}", data, timeout=timeout)


def get_cached_session(session_id: str) -> dict | None:
    return cache.get(f"tg_session:{session_id}")


def delete_cached_session(session_id: str) -> None:
    cache.delete(f"tg_session:{session_id}")


async def notify_admin(context: ContextTypes.DEFAULT_TYPE, message_html: str) -> bool:
    """Sends a notification or report to the bot owner/admin."""
    admin_id = getattr(settings, 'TELEGRAM_ADMIN_CHAT_ID', '')
    if not admin_id:
        logger.warning("TELEGRAM_ADMIN_CHAT_ID is not configured. Bug report logged to stdout:\n%s", message_html)
        return False

    try:
        await context.bot.send_message(
            chat_id=admin_id,
            text=message_html,
            parse_mode=ParseMode.HTML
        )
        return True
    except Exception as exc:
        logger.error("Failed to deliver message to TELEGRAM_ADMIN_CHAT_ID (%s): %s", admin_id, exc)
        return False


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles /start command with an introduction to supported platforms."""
    msg = update.effective_message
    if not msg:
        return

    text = (
        "👋 <b>Welcome to U-Loader Bot!</b>\n\n"
        "Your fast & universal media downloader directly in Telegram.\n\n"
        "✨ <b>Supported Platforms:</b>\n"
        "• 🔴 <b>YouTube</b>: 4K / 1080p / 720p & 320kbps MP3\n"
        "• 🟣 <b>Instagram</b>: Reels, Video Posts & Carousels\n"
        "• 🔷 <b>TikTok</b>: Watermark-free HD videos\n"
        "• 📌 <b>Pinterest</b>: High quality video & image pins\n"
        "• 🟢 <b>Spotify</b>: Tracks, Albums & Playlists with ID3 tags & artwork\n\n"
        "🚀 <b>How to start:</b>\n"
        "Simply send or forward any media link into this chat!\n\n"
        "🚨 <b>Found a bug?</b>\n"
        "Use the <b>/report</b> command or click the report button on error messages."
    )
    await msg.reply_html(text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles /help command."""
    msg = update.effective_message
    if not msg:
        return

    text = (
        "📖 <b>U-Loader Bot Help & Commands</b>\n\n"
        "<b>Available Commands:</b>\n"
        "• /start — Welcome menu & supported services\n"
        "• /help — Show this help message\n"
        "• /report — Report a bug or broken link directly to the developer\n\n"
        "<b>How to Download:</b>\n"
        "1. Send or forward any link from YouTube, Instagram, TikTok, Pinterest, or Spotify.\n"
        "2. Choose your preferred quality or audio format from the inline buttons.\n"
        "3. Watch real-time download & conversion progress.\n"
        "4. The bot will deliver your media directly into this chat!\n\n"
        "ℹ️ <i>Note: Telegram directly accepts bot uploads up to 50 MB. For larger 4K videos or huge Spotify playlist archives, an instant secure download link will be provided automatically.</i>"
    )
    await msg.reply_html(text)


async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Allows users to submit a bug report directly to the bot owner."""
    msg = update.effective_message
    user = update.effective_user
    if not msg or not user:
        return

    report_content = " ".join(context.args).strip() if context.args else ""

    if not report_content:
        guide_text = (
            "📝 <b>Report a Bug / Issue</b>\n\n"
            "If a download failed, gave an error, or a platform is broken, please describe what happened:\n\n"
            "<code>/report &lt;your issue description, link, or error message&gt;</code>\n\n"
            "<b>Example:</b>\n"
            "<code>/report Pinterest download failed for URL https://pin.it/... with error HTTP 403</code>\n\n"
            "💡 <i>Tip: If an error card appeared in the chat, you can tap the error text to copy it, or click the <b>🚨 Report This Bug</b> button for instant 1-click submission!</i>"
        )
        await msg.reply_html(guide_text)
        return

    user_info = f"{user.full_name}" + (f" (@{user.username})" if user.username else "")
    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    admin_report = (
        "🚨 <b>New Bug Report Received!</b>\n\n"
        f"👤 <b>Reporter:</b> {html.escape(user_info)}\n"
        f"🆔 <b>User ID:</b> <code>{user.id}</code>\n"
        f"⏱️ <b>Time:</b> {now_str}\n\n"
        "💬 <b>Report Message:</b>\n"
        f"<pre><code>{html.escape(report_content)}</code></pre>"
    )

    sent = await notify_admin(context, admin_report)
    if sent:
        await msg.reply_html(
            "✅ <b>Thank you!</b> Your bug report has been forwarded directly to the developer. We will investigate and resolve it."
        )
    else:
        await msg.reply_html(
            "✅ <b>Report Received!</b> Your bug report has been logged to the server logs. Thank you for helping us improve U-Loader!"
        )


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Detects URLs in user messages, extracts metadata, and shows format options."""
    msg = update.effective_message
    if not msg or not msg.text:
        return

    match = URL_REGEX.search(msg.text)
    if not match:
        await msg.reply_html(
            "💡 Send or forward a valid media link from <b>YouTube, Instagram, TikTok, Pinterest, or Spotify</b> to download!"
        )
        return

    raw_url = match.group(0).strip()
    status_msg = await msg.reply_html("🔍 <i>Analyzing media link and fetching formats...</i>")

    try:
        # Extract media information in worker thread to prevent blocking asyncio loop
        info = await asyncio.to_thread(extract_media_info, raw_url)
    except Exception as exc:
        logger.exception("Failed to extract media info for URL: %s", raw_url)
        err_str = str(exc)
        err_token = uuid.uuid4().hex[:8]

        cache_session(f"err_{err_token}", {
            'step': 'Metadata Extraction',
            'url': raw_url,
            'error': err_str,
            'user_id': update.effective_user.id if update.effective_user else None,
            'user_name': update.effective_user.full_name if update.effective_user else 'Unknown',
        }, timeout=3600)

        err_escaped = html.escape(err_str)
        report_cmd_hint = html.escape(f"/report Extraction error: {err_str[:80]}")

        fail_card = (
            "❌ <b>Media Extraction Failed</b>\n\n"
            "⚠️ Could not extract downloadable media from this URL.\n\n"
            "<b>Error details (tap to copy):</b>\n"
            f"<pre><code>{err_escaped}</code></pre>\n"
            "💬 <b>Report this bug:</b>\n"
            "Click the button below to notify the developer instantly, or copy the error above and send:\n"
            f"<code>{report_cmd_hint}</code>"
        )

        await status_msg.edit_text(
            fail_card,
            parse_mode=ParseMode.HTML,
            reply_markup=build_error_keyboard(err_token)
        )
        return

    formats = info.get('formats', [])
    if not formats:
        await status_msg.edit_text(
            "⚠️ <b>No downloadable formats found for this URL.</b>",
            parse_mode=ParseMode.HTML
        )
        return

    session_id = uuid.uuid4().hex[:10]
    session_data = {
        'url': raw_url,
        'platform': info.get('platform', detect_platform(raw_url)),
        'title': info.get('title', 'Media'),
        'author': info.get('author', ''),
        'duration': info.get('duration'),
        'thumbnail': info.get('thumbnail', ''),
        'is_playlist': info.get('is_playlist', False),
        'tracks': info.get('tracks', []),
        'formats': formats,
    }
    cache_session(session_id, session_data)

    platform_name = PLATFORM_ICONS.get(session_data['platform'], '🌐 Media')
    title_escaped = html.escape(session_data['title'])
    author_escaped = html.escape(session_data['author']) if session_data['author'] else ""
    duration_str = format_duration(session_data['duration'])

    caption_lines = [
        f"{platform_name} <b>{title_escaped}</b>\n"
    ]
    if author_escaped:
        caption_lines.append(f"👤 <b>Author:</b> {author_escaped}")
    if duration_str:
        caption_lines.append(f"⏱️ <b>Duration:</b> {duration_str}")
    if session_data['is_playlist']:
        track_count = len(session_data['tracks'])
        caption_lines.append(f"🎶 <b>Tracks:</b> {track_count} items")

    caption_lines.append("\n👇 <b>Choose download format:</b>")
    caption_text = "\n".join(caption_lines)

    keyboard = build_format_keyboard(session_id, formats)

    # Attempt to send with photo thumbnail
    thumbnail_url = session_data['thumbnail']
    sent_photo = False
    if thumbnail_url:
        try:
            await msg.reply_photo(
                photo=thumbnail_url,
                caption=caption_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
            sent_photo = True
        except Exception as photo_err:
            logger.warning("Failed to reply with photo thumbnail (%s): %s", thumbnail_url, photo_err)

    if not sent_photo:
        await msg.reply_html(caption_text, reply_markup=keyboard, disable_web_page_preview=True)

    # Clean up temporary status message
    try:
        await status_msg.delete()
    except Exception:
        pass


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Dispatches inline keyboard callbacks (format selection, error reporting, cancel)."""
    query = update.callback_query
    if not query or not query.data:
        return

    data = query.data

    # Handle 1-click Bug Report Button
    if data.startswith("rep_err:"):
        err_token = data.split("rep_err:")[1]
        err_info = get_cached_session(f"err_{err_token}")
        user = update.effective_user
        user_info = f"{user.full_name}" + (f" (@{user.username})" if user.username else "")

        if err_info:
            now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            admin_msg = (
                "🚨 <b>Automated Bug Report (1-Click)</b>\n\n"
                f"👤 <b>User:</b> {html.escape(user_info)} (ID: <code>{user.id}</code>)\n"
                f"⏱️ <b>Time:</b> {now_str}\n"
                f"⚙️ <b>Step:</b> {html.escape(err_info.get('step', 'Download'))}\n"
                f"🔗 <b>URL:</b> {html.escape(err_info.get('url', 'N/A'))}\n"
            )
            if err_info.get('platform'):
                admin_msg += f"🌐 <b>Platform:</b> {html.escape(err_info['platform'])}\n"
            if err_info.get('title'):
                admin_msg += f"🏷️ <b>Title:</b> {html.escape(err_info['title'])}\n"
            if err_info.get('format'):
                admin_msg += f"📦 <b>Format:</b> {html.escape(err_info['format'])}\n"

            admin_msg += (
                f"\n❌ <b>Error:</b>\n"
                f"<pre><code>{html.escape(err_info.get('error', 'Unknown'))}</code></pre>"
            )

            await notify_admin(context, admin_msg)
            await query.answer("✅ Bug report sent directly to developer! Thank you.", show_alert=True)
            try:
                await query.edit_message_reply_markup(reply_markup=build_reported_keyboard())
            except Exception:
                pass
        else:
            await query.answer("✅ Bug report recorded! Thank you.", show_alert=True)
            try:
                await query.edit_message_reply_markup(reply_markup=build_reported_keyboard())
            except Exception:
                pass
        return

    # Handle Cancel button
    if data.startswith("cancel:"):
        session_id = data.split("cancel:")[1]
        delete_cached_session(session_id)
        await query.answer("Download cancelled")
        if query.message.photo:
            await query.edit_message_caption(
                caption="🚫 <i>Download request cancelled.</i>",
                parse_mode=ParseMode.HTML
            )
        else:
            await query.edit_message_text(
                text="🚫 <i>Download request cancelled.</i>",
                parse_mode=ParseMode.HTML
            )
        return

    if not data.startswith("dl:"):
        return

    parts = data.split(":")
    if len(parts) != 3:
        await query.answer("Invalid request", show_alert=True)
        return

    session_id = parts[1]
    format_idx = int(parts[2])

    session_data = get_cached_session(session_id)
    if not session_data:
        await query.answer("⚠️ Session expired. Please send the link again.", show_alert=True)
        return

    formats = session_data.get('formats', [])
    if format_idx >= len(formats):
        await query.answer("⚠️ Invalid format selected.", show_alert=True)
        return

    selected_format = formats[format_idx]
    format_label = selected_format.get('label', selected_format.get('id', 'Selected format'))
    media_type = selected_format.get('type', 'video')
    format_id = selected_format.get('id', 'best')
    direct_url = selected_format.get('direct_url')

    await query.answer("Starting download...")

    # Immediate delivery for direct image formats if provided
    if media_type == 'image' and direct_url:
        try:
            await query.message.reply_photo(
                photo=direct_url,
                caption=f"🖼️ <b>{html.escape(session_data['title'])}</b>",
                parse_mode=ParseMode.HTML
            )
            return
        except Exception as e:
            logger.warning("Direct image send failed: %s", e)

    # Priority mode: Spotify individual track delivery directly to chat
    if media_type == 'playlist_tracks' or format_id == 'spotify_tracks_individual':
        status_card = (
            "🚀 <b>Starting Playlist Delivery!</b>\n\n"
            f"🎶 <b>Album / Playlist:</b> {html.escape(session_data['title'])}\n"
            f"👤 <b>Artist:</b> {html.escape(session_data.get('author') or 'Spotify')}\n"
            f"⏳ <i>Preparing songs for individual delivery to this chat...</i>\n\n"
            f"📊 <b>Progress:</b> [{make_progress_bar(0)}] 0%"
        )
        progress_msg = await query.message.reply_html(status_card)

        asyncio.create_task(
            deliver_spotify_playlist_individual(
                chat_id=query.message.chat_id,
                session_data=session_data,
                progress_msg=progress_msg,
                context=context
            )
        )
        return

    # Create DownloadTask in database
    task = await sync_to_async(DownloadTask.objects.create)(
        url=session_data['url'],
        platform=session_data['platform'],
        media_type=media_type,
        format_id=format_id,
        title=session_data['title'],
        status='pending',
        progress_message='Task queued and worker dispatched'
    )

    status_card = (
        "🚀 <b>Download Started!</b>\n\n"
        f"🏷️ <b>Title:</b> {html.escape(session_data['title'])}\n"
        f"⚙️ <b>Format:</b> {html.escape(format_label)}\n"
        f"⏳ <b>Status:</b> Initializing download & connecting to {html.escape(session_data['platform'].capitalize())}...\n"
        f"📊 <b>Progress:</b> [{make_progress_bar(0)}] 0%"
    )

    progress_msg = await query.message.reply_html(status_card)

    # Safely dispatch download job (Celery worker or fallback thread)
    await sync_to_async(dispatch_download_task)(str(task.id))

    # Monitor download progress asynchronously
    asyncio.create_task(
        poll_and_deliver_task(
            task_id=str(task.id),
            progress_msg=progress_msg,
            chat_id=query.message.chat_id,
            context=context,
            title=session_data['title'],
            format_label=format_label,
            media_type=media_type,
            url=session_data['url'],
            platform=session_data['platform']
        )
    )


async def deliver_spotify_playlist_individual(
    chat_id: int,
    session_data: dict,
    progress_msg,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Downloads each Spotify playlist track individually from YouTube at 320 kbps MP3,
    tags it with ID3 metadata, and delivers each song directly into the user's chat.
    """
    import shutil
    tracks = session_data.get('tracks', [])
    url = session_data.get('url', '')

    if not tracks:
        try:
            info = await asyncio.to_thread(extract_spotify_info, url)
            tracks = info.get('tracks', [])
        except Exception as e:
            logger.warning("Failed to retrieve Spotify playlist tracks: %s", e)

    if not tracks:
        await progress_msg.edit_text(
            "⚠️ <b>No tracks found for this playlist.</b> Please ensure the playlist is public.",
            parse_mode=ParseMode.HTML
        )
        return

    total = len(tracks)
    temp_dir = settings.DOWNLOADS_ROOT / f"spotify_bulk_{uuid.uuid4().hex[:8]}"
    temp_dir.mkdir(parents=True, exist_ok=True)

    sent_count = 0
    failed_count = 0

    try:
        for idx, t in enumerate(tracks, start=1):
            title = t.get('title', 'Unknown Track')
            artist = t.get('artist', 'Unknown Artist')
            duration = t.get('duration', 0)
            thumbnail = t.get('thumbnail', '')
            percent = round((idx - 1) / total * 100)
            bar = make_progress_bar(percent)

            # Update live progress card
            try:
                await progress_msg.edit_text(
                    f"🎶 <b>Delivering Spotify Songs ({idx}/{total})</b>\n\n"
                    f"🏷️ <b>Current:</b> {html.escape(title)}\n"
                    f"👤 <b>Artist:</b> {html.escape(artist)}\n\n"
                    f"📊 <b>Progress:</b> [{bar}] {percent}%\n"
                    f"⚡ <i>Sending tracks one-by-one to this chat...</i>",
                    parse_mode=ParseMode.HTML
                )
            except Exception:
                pass

            # Download and ID3-tag the MP3 track
            track_file = None
            try:
                track_file = await asyncio.to_thread(
                    download_and_tag_spotify_track,
                    title=title,
                    artist=artist,
                    output_dir=temp_dir,
                    thumbnail_url=thumbnail,
                    quality='320k'
                )
            except Exception as dl_err:
                logger.warning("Failed to download Spotify track '%s - %s': %s", artist, title, dl_err)
                failed_count += 1
                continue

            # Send native Telegram Audio to user's chat with 413 size fallback
            if track_file and track_file.exists():
                caption = f"🎵 <b>{html.escape(artist)} - {html.escape(title)}</b>"
                file_to_send = track_file
                cleanup_files = [track_file]

                # Pre-check: If file size is >= 48 MB, compress to lower bitrate before attempting upload
                if file_to_send.stat().st_size >= 48 * 1024 * 1024:
                    logger.info("Track '%s' is %s MB (>= 48MB). Pre-compressing...", title, round(file_to_send.stat().st_size / (1024 * 1024), 1))
                    comp = await asyncio.to_thread(compress_audio_to_size, file_to_send, 48 * 1024 * 1024, ['128k', '96k', '64k'])
                    if comp and comp.exists():
                        file_to_send = comp
                        cleanup_files.append(comp)

                upload_ok = False
                try:
                    with open(file_to_send, 'rb') as audio_fp:
                        await context.bot.send_audio(
                            chat_id=chat_id,
                            audio=audio_fp,
                            title=title,
                            performer=artist,
                            duration=duration,
                            caption=caption,
                            parse_mode=ParseMode.HTML,
                            read_timeout=180,
                            write_timeout=180
                        )
                    upload_ok = True
                    sent_count += 1
                except Exception as send_err:
                    err_str = str(send_err)
                    is_too_large = "413" in err_str or "Too Large" in err_str or "too big" in err_str.lower()
                    if is_too_large:
                        logger.warning("Upload of '%s' failed with 413 (%s). Falling back to lower quality...", title, send_err)
                        # Downsample to lower bitrate (128k, 96k, 64k)
                        comp = await asyncio.to_thread(compress_audio_to_size, track_file, 48 * 1024 * 1024, ['128k', '96k', '64k'])
                        if comp and comp.exists():
                            cleanup_files.append(comp)
                            try:
                                with open(comp, 'rb') as audio_fp:
                                    await context.bot.send_audio(
                                        chat_id=chat_id,
                                        audio=audio_fp,
                                        title=title,
                                        performer=artist,
                                        duration=duration,
                                        caption=caption + "\n<i>(optimized quality for Telegram)</i>",
                                        parse_mode=ParseMode.HTML,
                                        read_timeout=180,
                                        write_timeout=180
                                    )
                                upload_ok = True
                                sent_count += 1
                            except Exception as retry_err:
                                logger.warning("Retry with lower quality failed for '%s': %s", title, retry_err)

                    if not upload_ok:
                        logger.warning("Failed to upload track '%s' to Telegram: %s", title, send_err)
                        failed_count += 1
                finally:
                    for f_obj in cleanup_files:
                        try:
                            f_obj.unlink(missing_ok=True)
                        except Exception:
                            pass

                # Rate-limiting cushion between Telegram uploads
                await asyncio.sleep(0.8)
            else:
                failed_count += 1

        # Final delivery summary card
        if sent_count > 0:
            summary = (
                f"✅ <b>Playlist Delivery Completed!</b>\n\n"
                f"🎶 <b>Delivered:</b> {sent_count}/{total} songs directly to this chat.\n"
            )
            if failed_count > 0:
                summary += f"⚠️ <i>{failed_count} track(s) could not be located or downloaded.</i>\n\n"
            else:
                summary += "\n"
            summary += "🎧 <i>Enjoy your music!</i>"
            await progress_msg.edit_text(summary, parse_mode=ParseMode.HTML)
        else:
            await progress_msg.edit_text(
                "❌ <b>Playlist delivery failed.</b> Tracks could not be downloaded. Please try again.",
                parse_mode=ParseMode.HTML
            )

    except Exception as exc:
        logger.exception("Playlist delivery fatal error: %s", exc)
        err_token = uuid.uuid4().hex[:8]
        cache_session(f"err_{err_token}", {
            'step': 'Playlist Individual Delivery',
            'url': url,
            'title': session_data.get('title'),
            'error': str(exc),
        }, timeout=3600)
        await progress_msg.edit_text(
            f"❌ <b>Playlist Delivery Error</b>\n\n"
            f"<pre><code>{html.escape(str(exc))}</code></pre>",
            parse_mode=ParseMode.HTML,
            reply_markup=build_error_keyboard(err_token)
        )
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


async def poll_and_deliver_task(
    task_id: str,
    progress_msg,
    chat_id: int,
    context: ContextTypes.DEFAULT_TYPE,
    title: str,
    format_label: str,
    media_type: str,
    url: str,
    platform: str,
) -> None:
    """Polls database task status and delivers downloaded media file to Telegram."""
    last_update_time = time.time()
    last_progress = -1.0
    last_status_msg = ""
    timeout_seconds = 1200  # 20 minutes max wait time
    start_time = time.time()
    api_base_url = getattr(settings, 'API_BASE_URL', 'https://api-loader.claive.uz').rstrip('/')

    while time.time() - start_time < timeout_seconds:
        await asyncio.sleep(1.8)

        try:
            task = await sync_to_async(DownloadTask.objects.get)(id=task_id)
        except DownloadTask.DoesNotExist:
            await progress_msg.edit_text("❌ Task was not found.")
            return

        # Update progress card if changed
        if task.status in ('pending', 'downloading', 'processing'):
            now = time.time()
            if (now - last_update_time >= 2.0) and (
                abs(task.progress - last_progress) >= 2.0 or task.progress_message != last_status_msg
            ):
                last_update_time = now
                last_progress = task.progress
                last_status_msg = task.progress_message

                bar = make_progress_bar(task.progress)
                updated_card = (
                    "📥 <b>Downloading Media...</b>\n\n"
                    f"🏷️ <b>Title:</b> {html.escape(title)}\n"
                    f"⚙️ <b>Format:</b> {html.escape(format_label)}\n"
                    f"⏳ <b>Status:</b> {html.escape(task.progress_message or 'Processing...')}\n"
                    f"📊 <b>Progress:</b> [{bar}] {round(task.progress)}%"
                )
                try:
                    await progress_msg.edit_text(updated_card, parse_mode=ParseMode.HTML)
                except Exception:
                    pass

        elif task.status == 'completed':
            file_path = Path(task.file_path) if task.file_path else None
            file_size = task.file_size or (file_path.stat().st_size if file_path and file_path.exists() else 0)

            # Check if file exists on disk
            if not file_path or not file_path.exists():
                download_url = f"{api_base_url}/api/tasks/{task.id}/download/"
                await progress_msg.edit_text(
                    f"✅ <b>Download Ready!</b>\n\n"
                    f"📁 <b>{html.escape(task.file_name or title)}</b>\n\n"
                    f"🔗 <a href='{download_url}'><b>Click here to download your file</b></a>",
                    parse_mode=ParseMode.HTML
                )
                return

            # If audio file is over 50MB, automatically downsample to lower bitrate to deliver directly to Telegram
            if file_size > MAX_TELEGRAM_FILE_SIZE and (media_type == 'audio' or file_path.suffix.lower() in ('.mp3', '.m4a', '.flac', '.wav')):
                comp = await asyncio.to_thread(compress_audio_to_size, file_path, MAX_TELEGRAM_FILE_SIZE, ['128k', '96k', '64k'])
                if comp and comp.exists():
                    file_path = comp
                    file_size = comp.stat().st_size

            # Check file size against Telegram Bot API 50 MB limit
            if file_size <= MAX_TELEGRAM_FILE_SIZE:
                try:
                    await progress_msg.edit_text("🚀 <i>Uploading media to Telegram...</i>", parse_mode=ParseMode.HTML)
                except Exception:
                    pass

                if file_path.suffix.lower() == '.zip':
                    caption = f"📦 <b>{html.escape(title)}</b>"
                elif media_type in ('image', 'carousel') or file_path.suffix.lower() in ('.jpg', '.jpeg', '.png', '.webp'):
                    caption = f"🖼️ <b>{html.escape(title)}</b>"
                elif media_type == 'video' or file_path.suffix.lower() in ('.mp4', '.mkv', '.webm', '.mov'):
                    caption = f"🎬 <b>{html.escape(title)}</b>"
                else:
                    caption = f"🎵 <b>{html.escape(title)}</b>"

                try:
                    with open(file_path, 'rb') as f:
                        if media_type == 'audio' or file_path.suffix.lower() in ('.mp3', '.m4a', '.flac', '.wav'):
                            await context.bot.send_audio(
                                chat_id=chat_id,
                                audio=f,
                                title=title,
                                caption=caption,
                                parse_mode=ParseMode.HTML,
                                read_timeout=300,
                                write_timeout=300
                            )
                        elif file_path.suffix.lower() in ('.jpg', '.jpeg', '.png', '.webp'):
                            try:
                                await context.bot.send_photo(
                                    chat_id=chat_id,
                                    photo=f,
                                    caption=caption,
                                    parse_mode=ParseMode.HTML,
                                    read_timeout=120,
                                    write_timeout=120
                                )
                            except Exception:
                                f.seek(0)
                                await context.bot.send_document(
                                    chat_id=chat_id,
                                    document=f,
                                    caption=caption,
                                    parse_mode=ParseMode.HTML,
                                    read_timeout=300,
                                    write_timeout=300
                                )
                        elif media_type == 'video' or file_path.suffix.lower() in ('.mp4', '.mkv', '.webm', '.mov'):
                            await context.bot.send_video(
                                chat_id=chat_id,
                                video=f,
                                caption=caption,
                                supports_streaming=True,
                                parse_mode=ParseMode.HTML,
                                read_timeout=300,
                                write_timeout=300
                            )
                        else:
                            await context.bot.send_document(
                                chat_id=chat_id,
                                document=f,
                                caption=caption,
                                parse_mode=ParseMode.HTML,
                                read_timeout=300,
                                write_timeout=300
                            )

                    # Update status message upon successful upload
                    await progress_msg.edit_text("✅ <b>Delivered!</b> Enjoy your media.", parse_mode=ParseMode.HTML)
                    return
                except Exception as upload_err:
                    logger.warning("Telegram direct upload failed, falling back to direct link: %s", upload_err)

            # Fallback for > 50 MB files or if Telegram upload had connection errors
            download_url = f"{api_base_url}/api/tasks/{task.id}/download/"
            size_mb = round(file_size / (1024 * 1024), 1)
            expiration_minutes = getattr(settings, 'FILE_EXPIRATION_MINUTES', 60)

            fallback_card = (
                f"✅ <b>Download Ready!</b>\n\n"
                f"📁 <b>{html.escape(task.file_name or title)}</b> ({size_mb} MB)\n\n"
                f"⚠️ <i>File is too large for Telegram upload ({size_mb} MB > 50 MB limit).</i>\n\n"
                f"🔗 <a href='{download_url}'><b>Click here to download directly</b></a>\n\n"
                f"⏳ <i>Secure download link expires in {expiration_minutes} minutes.</i>"
            )
            await progress_msg.edit_text(fallback_card, parse_mode=ParseMode.HTML)
            return

        elif task.status == 'failed':
            err_msg = task.error_message or "An unexpected error occurred during processing."
            err_token = uuid.uuid4().hex[:8]

            # Cache error for 1-click reporting
            cache_session(f"err_{err_token}", {
                'step': 'Download & Processing',
                'task_id': task_id,
                'url': url,
                'platform': platform,
                'title': title,
                'format': format_label,
                'error': err_msg,
            }, timeout=3600)

            err_escaped = html.escape(err_msg)
            report_hint = html.escape(f"/report Download error on {platform}: {err_msg[:80]}")

            fail_card = (
                "❌ <b>Download Failed</b>\n\n"
                f"⚠️ An issue occurred while downloading/converting this media:\n\n"
                "<b>Error details (tap to copy):</b>\n"
                f"<pre><code>{err_escaped}</code></pre>\n"
                "💬 <b>Report this bug:</b>\n"
                "Click the button below to report this instantly, or copy the error above and send:\n"
                f"<code>{report_hint}</code>"
            )

            await progress_msg.edit_text(
                fail_card,
                parse_mode=ParseMode.HTML,
                reply_markup=build_error_keyboard(err_token)
            )
            return

    # If timed out
    await progress_msg.edit_text("⏱️ <b>Download timed out.</b> Please try again.")
