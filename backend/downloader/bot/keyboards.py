from __future__ import annotations
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

PLATFORM_ICONS = {
    'youtube': '🔴 YouTube',
    'instagram': '🟣 Instagram',
    'tiktok': '🔷 TikTok',
    'pinterest': '📌 Pinterest',
    'spotify': '🟢 Spotify',
    'generic': '🌐 Media Downloader',
}

def format_duration(seconds: int | float | None) -> str:
    """Converts seconds to HH:MM:SS or MM:SS."""
    if not seconds:
        return ""
    try:
        s = int(seconds)
        hours = s // 3600
        minutes = (s % 3600) // 60
        secs = s % 60
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"
    except (ValueError, TypeError):
        return ""

def build_format_keyboard(session_id: str, formats: list[dict]) -> InlineKeyboardMarkup:
    """
    Constructs an interactive Telegram inline keyboard with available quality options.
    Callback data structure: dl:<session_id>:<format_index> (fits easily under 64-byte Telegram limit)
    """
    keyboard = []
    video_row = []
    audio_row = []
    other_buttons = []

    for idx, fmt in enumerate(formats):
        fmt_type = fmt.get('type', '')
        quality = fmt.get('quality', '')
        ext = fmt.get('ext', '')

        # Button Label Formatting
        if fmt_type == 'video':
            label = f"🎬 {quality}" if quality else f"🎬 Video ({ext.upper()})"
            video_row.append(InlineKeyboardButton(label, callback_data=f"dl:{session_id}:{idx}"))
            if len(video_row) == 2:
                keyboard.append(video_row)
                video_row = []
        elif fmt_type == 'audio':
            label = f"🎵 MP3 ({quality})" if quality and quality != 'original' else f"🎵 Audio ({ext.upper()})"
            audio_row.append(InlineKeyboardButton(label, callback_data=f"dl:{session_id}:{idx}"))
            if len(audio_row) == 2:
                keyboard.append(audio_row)
                audio_row = []
        elif fmt_type == 'playlist_tracks':
            label = fmt.get('label') or "🎶 Send Each Song to Chat"
            other_buttons.append([InlineKeyboardButton(label, callback_data=f"dl:{session_id}:{idx}")])
        elif fmt_type == 'playlist':
            label = fmt.get('label') or (f"📦 Download ZIP ({quality})" if quality else "📦 Download Full ZIP")
            other_buttons.append([InlineKeyboardButton(label, callback_data=f"dl:{session_id}:{idx}")])
        elif fmt_type in ('image', 'carousel'):
            label = fmt.get('label') or "🖼️ Photo / Cover (JPG)"
            other_buttons.append([InlineKeyboardButton(label, callback_data=f"dl:{session_id}:{idx}")])
        else:
            label = fmt.get('label', f"Download {ext}")
            other_buttons.append([InlineKeyboardButton(label, callback_data=f"dl:{session_id}:{idx}")])

    # Flush remaining in rows
    if video_row:
        keyboard.append(video_row)
    if audio_row:
        keyboard.append(audio_row)
    for btn_row in other_buttons:
        keyboard.append(btn_row)

    # Cancel button
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data=f"cancel:{session_id}")])

    return InlineKeyboardMarkup(keyboard)


def build_error_keyboard(err_token: str) -> InlineKeyboardMarkup:
    """Builds inline keyboard with a 1-click Bug Report button for errors."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚨 Report This Bug to Developer", callback_data=f"rep_err:{err_token}")]
    ])


def build_reported_keyboard() -> InlineKeyboardMarkup:
    """Disabled button state confirming the error has been reported."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Bug Reported to Developer", callback_data="none")]
    ])
