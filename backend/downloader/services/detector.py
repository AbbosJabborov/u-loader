import re

PLATFORM_PATTERNS = [
    (
        'youtube',
        r'^(https?://)?(www\.|m\.)?(youtube\.com/(watch\?v=|shorts/|playlist\?list=)|youtu\.be/)[a-zA-Z0-9_\-]+'
    ),
    (
        'instagram',
        r'^(https?://)?(www\.)?instagram\.com/(reel|p|tv|stories)/.+'
    ),
    (
        'tiktok',
        r'^(https?://)?(www\.|vm\.|vt\.)?tiktok\.com/(@[a-zA-Z0-9_.\-]+/video/\d+|[a-zA-Z0-9]+)'
    ),
    (
        'pinterest',
        r'^(https?://)?([a-zA-Z0-9_.\-]+\.)?(pinterest\.[a-z.]+|pin\.it)/.+'
    ),
    (
        'spotify',
        r'^(https?://)?(open\.spotify\.com/(track|playlist|album)/|spotify:(track|playlist|album):)[a-zA-Z0-9]+'
    ),
]

def detect_platform(url: str) -> str:
    """Detect platform from given URL. Returns platform name or 'generic'."""
    url = url.strip()
    for platform, pattern in PLATFORM_PATTERNS:
        if re.search(pattern, url, re.IGNORECASE):
            return platform
    return 'generic'
