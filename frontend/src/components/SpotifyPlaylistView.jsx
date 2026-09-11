import React, { useState } from 'react';
import { Music, CheckSquare, Square, Download, Search, Archive, Play, Clock, Sparkles } from 'lucide-react';

export default function SpotifyPlaylistView({ playlistData, onDownload, isStarting }) {
  if (!playlistData || !playlistData.is_playlist) return null;

  const { title, author, thumbnail, tracks = [], url } = playlistData;
  const [selectedIds, setSelectedIds] = useState(new Set(tracks.map((t) => t.id)));
  const [searchQuery, setSearchQuery] = useState('');
  const [bitrate, setBitrate] = useState('320k');

  const filteredTracks = tracks.filter((t) => {
    const q = searchQuery.toLowerCase();
    return t.title.toLowerCase().includes(q) || t.artist.toLowerCase().includes(q);
  });

  const toggleSelectAll = () => {
    if (selectedIds.size === tracks.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(tracks.map((t) => t.id)));
    }
  };

  const toggleTrack = (id) => {
    const next = new Set(selectedIds);
    if (next.has(id)) {
      next.delete(id);
    } else {
      next.add(id);
    }
    setSelectedIds(next);
  };

  const formatDuration = (secs) => {
    if (!secs) return '';
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  const handleDownloadZip = () => {
    const trackIds = Array.from(selectedIds);
    if (trackIds.length === 0) return;
    onDownload({
      url,
      media_type: 'playlist',
      format_id: bitrate,
      title: title,
      selected_tracks: trackIds,
    });
  };

  const handleSingleTrackDownload = (track) => {
    onDownload({
      url: `https://open.spotify.com/track/${track.id}`,
      media_type: 'audio',
      format_id: bitrate,
      title: `${track.artist} - ${track.title}`,
    });
  };

  return (
    <div className="w-full max-w-4xl mx-auto mt-8 glass-panel rounded-3xl p-5 sm:p-7 border border-white/10 shadow-2xl">
      
      {/* Playlist Header */}
      <div className="flex flex-col sm:flex-row items-center gap-6 pb-6 border-b border-white/10">
        <div className="relative w-36 h-36 shrink-0 rounded-2xl overflow-hidden bg-black/40 border border-white/10 shadow-lg">
          {thumbnail ? (
            <img src={thumbnail} alt={title} className="w-full h-full object-cover" />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-emerald-500">
              <Music className="w-12 h-12" />
            </div>
          )}
        </div>

        <div className="flex-1 text-center sm:text-left">
          <div className="flex items-center justify-center sm:justify-start gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[#6355F6]/15 text-[#00E5FF] border border-[#6355F6]/30">
              Spotify Playlist
            </span>
            <span className="text-xs text-slate-400">{tracks.length} tracks</span>
          </div>

          <h3 className="text-xl sm:text-2xl font-bold text-white mt-1.5">{title}</h3>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">Curated by {author || 'Spotify'}</p>

          {/* Audio Bitrate Selector */}
          <div className="flex items-center justify-center sm:justify-start gap-2 mt-4 text-xs">
            <span className="text-slate-400">Audio Quality:</span>
            <button
              type="button"
              onClick={() => setBitrate('320k')}
              className={`px-2.5 py-1 rounded-lg border font-medium transition-all ${
                bitrate === '320k'
                  ? 'bg-[#6355F6]/25 border-[#6355F6] text-[#00E5FF]'
                  : 'bg-white/5 border-white/5 text-slate-400 hover:text-white'
              }`}
            >
              320 kbps (HQ)
            </button>
            <button
              type="button"
              onClick={() => setBitrate('192k')}
              className={`px-2.5 py-1 rounded-lg border font-medium transition-all ${
                bitrate === '192k'
                  ? 'bg-[#6355F6]/25 border-[#6355F6] text-[#00E5FF]'
                  : 'bg-white/5 border-white/5 text-slate-400 hover:text-white'
              }`}
            >
              192 kbps (Normal)
            </button>
          </div>
        </div>

        {/* Global Download Action */}
        <div className="shrink-0 w-full sm:w-auto flex flex-col items-center gap-2">
          <button
            type="button"
            onClick={handleDownloadZip}
            disabled={isStarting || selectedIds.size === 0}
            className={`w-full sm:w-auto flex items-center justify-center gap-2 px-6 py-3.5 rounded-2xl font-bold text-sm shadow-xl transition-all ${
              selectedIds.size === 0 || isStarting
                ? 'bg-white/[0.04] text-slate-500 cursor-not-allowed'
                : 'duotone-btn text-white active:scale-95'
            }`}
          >
            <Archive className="w-4 h-4" />
            <span>
              {isStarting ? 'Preparing ZIP...' : `Download ZIP (${selectedIds.size})`}
            </span>
          </button>
          <span className="text-[11px] text-slate-400">Auto-tagged with ID3 & Album Art</span>
        </div>
      </div>

      {/* Track Controls (Select All & Filter) */}
      <div className="flex items-center justify-between gap-4 py-4">
        <button
          type="button"
          onClick={toggleSelectAll}
          className="flex items-center gap-2 text-xs font-medium text-slate-300 hover:text-white transition-colors"
        >
          {selectedIds.size === tracks.length ? (
            <CheckSquare className="w-4 h-4 text-[#00E5FF]" />
          ) : (
            <Square className="w-4 h-4 text-slate-500" />
          )}
          <span>
            {selectedIds.size === tracks.length ? 'Deselect All' : `Select All (${tracks.length})`}
          </span>
        </button>

        <div className="relative w-48 sm:w-64">
          <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Filter tracks..."
            className="w-full bg-black/30 border border-white/10 rounded-xl pl-8 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-[#6355F6]"
          />
        </div>
      </div>

      {/* Tracks List */}
      <div className="max-h-96 overflow-y-auto space-y-1.5 pr-1">
        {filteredTracks.map((track, idx) => {
          const isSelected = selectedIds.has(track.id);
          return (
            <div
              key={track.id || idx}
              className={`flex items-center justify-between p-2.5 rounded-xl text-xs transition-all border ${
                isSelected
                  ? 'bg-white/[0.04] border-white/10 text-white'
                  : 'bg-transparent border-transparent text-gray-500 hover:bg-white/[0.02]'
              }`}
            >
              <div className="flex items-center gap-3 min-w-0">
                <button
                  type="button"
                  onClick={() => toggleTrack(track.id)}
                  className="shrink-0 text-slate-400 hover:text-[#00E5FF] transition-colors"
                >
                  {isSelected ? (
                    <CheckSquare className="w-4 h-4 text-[#00E5FF]" />
                  ) : (
                    <Square className="w-4 h-4" />
                  )}
                </button>

                <span className="w-5 text-center text-[11px] text-slate-500 font-mono">
                  {idx + 1}
                </span>

                {track.thumbnail && (
                  <img
                    src={track.thumbnail}
                    alt=""
                    className="w-8 h-8 rounded-lg object-cover shrink-0"
                  />
                )}

                <div className="min-w-0">
                  <p className="font-medium truncate text-slate-200">{track.title}</p>
                  <p className="text-[11px] text-slate-400 truncate">{track.artist}</p>
                </div>
              </div>

              <div className="flex items-center gap-3 shrink-0 ml-3">
                {track.duration ? (
                  <span className="text-slate-500 font-mono text-[11px] hidden sm:inline">
                    {formatDuration(track.duration)}
                  </span>
                ) : null}

                <button
                  type="button"
                  onClick={() => handleSingleTrackDownload(track)}
                  title="Download this single track"
                  className="p-1.5 rounded-lg bg-white/5 hover:bg-[#6355F6] hover:text-white text-slate-400 transition-colors"
                >
                  <Download className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          );
        })}
      </div>

    </div>
  );
}
