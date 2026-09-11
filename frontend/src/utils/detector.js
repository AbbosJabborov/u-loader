export const PLATFORMS = {
  YOUTUBE: 'youtube',
  INSTAGRAM: 'instagram',
  TIKTOK: 'tiktok',
  PINTEREST: 'pinterest',
  SPOTIFY: 'spotify',
  GENERIC: 'generic',
};

export const PLATFORM_CONFIG = {
  [PLATFORMS.YOUTUBE]: {
    id: 'youtube',
    name: 'YouTube',
    color: '#FF0000',
    badgeBg: 'bg-red-500/10 border-red-500/30 text-red-400',
    gradient: 'from-red-500 to-rose-600',
    placeholder: 'Paste YouTube video, Shorts, or audio link...',
    hint: 'Supports up to 4K MP4 & 320kbps MP3 audio extraction',
  },
  [PLATFORMS.INSTAGRAM]: {
    id: 'instagram',
    name: 'Instagram',
    color: '#E1306C',
    badgeBg: 'bg-pink-500/10 border-pink-500/30 text-pink-400',
    gradient: 'from-purple-600 via-pink-600 to-amber-500',
    placeholder: 'Paste Instagram Reel or Post link...',
    hint: 'Supports Reels, Videos, and Carousel posts',
  },
  [PLATFORMS.TIKTOK]: {
    id: 'tiktok',
    name: 'TikTok',
    color: '#00F2FE',
    badgeBg: 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400',
    gradient: 'from-cyan-400 to-emerald-400',
    placeholder: 'Paste TikTok video link (tiktok.com or vm.tiktok.com)...',
    hint: 'Downloads original HD video without watermark',
  },
  [PLATFORMS.PINTEREST]: {
    id: 'pinterest',
    name: 'Pinterest',
    color: '#E60023',
    badgeBg: 'bg-rose-500/10 border-rose-500/30 text-rose-400',
    gradient: 'from-red-600 to-red-800',
    placeholder: 'Paste Pinterest Video Pin or pin.it link...',
    hint: 'Extracts full HD video pins',
  },
  [PLATFORMS.SPOTIFY]: {
    id: 'spotify',
    name: 'Spotify',
    color: '#1DB954',
    badgeBg: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400',
    gradient: 'from-emerald-500 to-green-600',
    placeholder: 'Paste Spotify Track, Playlist, or Album link...',
    hint: 'Extracts tracklist, tags 320kbps MP3 with album artwork & ZIP',
  },
  [PLATFORMS.GENERIC]: {
    id: 'generic',
    name: 'Universal URL',
    color: '#6366F1',
    badgeBg: 'bg-indigo-500/10 border-indigo-500/30 text-indigo-400',
    gradient: 'from-indigo-500 to-violet-600',
    placeholder: 'Paste any video or audio URL...',
    hint: 'Smart detection automatically extracts available streams',
  },
};

export const detectPlatform = (url = '') => {
  const trimmed = url.trim();
  if (!trimmed) return null;

  if (/(?:youtube\.com\/(?:watch\?v=|shorts\/|playlist\?list=)|youtu\.be\/)/i.test(trimmed)) {
    return PLATFORMS.YOUTUBE;
  }
  if (/instagram\.com\/(?:reel|p|tv|stories)\//i.test(trimmed)) {
    return PLATFORMS.INSTAGRAM;
  }
  if (/(?:tiktok\.com\/|vm\.tiktok\.com\/|vt\.tiktok\.com\/)/i.test(trimmed)) {
    return PLATFORMS.TIKTOK;
  }
  if (/(?:pinterest\.[a-z.]+|pin\.it)\//i.test(trimmed)) {
    return PLATFORMS.PINTEREST;
  }
  if (/(?:open\.spotify\.com\/(?:intl-[a-zA-Z0-9_\-]+\/)?(?:track|playlist|album)\/|spotify:(?:track|playlist|album):|spotify\.link\/)/i.test(trimmed)) {
    return PLATFORMS.SPOTIFY;
  }

  return PLATFORMS.GENERIC;
};
