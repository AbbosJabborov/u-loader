import React, { useState } from 'react';
import { CheckSquare, Square, Download, Search, Archive } from 'lucide-react';

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
    <div className="w-full max-w-2xl mx-auto mt-6 studio-card rounded-xl p-4 sm:p-5">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-zinc-800">
        <div className="flex items-center gap-3">
          {thumbnail && (
            <img src={thumbnail} alt={title} className="w-14 h-14 rounded-lg object-cover bg-zinc-900 border border-zinc-800" />
          )}
          <div>
            <h3 className="text-sm sm:text-base font-semibold text-zinc-100 line-clamp-1">{title}</h3>
            <p className="text-xs text-zinc-500 font-mono mt-0.5">{author || 'Spotify'} • {tracks.length} tracks</p>
          </div>
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          {/* Bitrate Selector */}
          <div className="flex items-center rounded-lg bg-zinc-900 border border-zinc-800 p-0.5 text-xs font-mono">
            <button
              type="button"
              onClick={() => setBitrate('320k')}
              className={`px-2.5 py-1 rounded-md transition-colors ${
                bitrate === '320k' ? 'bg-zinc-100 text-zinc-950 font-semibold' : 'text-zinc-400 hover:text-zinc-200'
              }`}
            >
              320k
            </button>
            <button
              type="button"
              onClick={() => setBitrate('192k')}
              className={`px-2.5 py-1 rounded-md transition-colors ${
                bitrate === '192k' ? 'bg-zinc-100 text-zinc-950 font-semibold' : 'text-zinc-400 hover:text-zinc-200'
              }`}
            >
              192k
            </button>
          </div>

          <button
            type="button"
            onClick={handleDownloadZip}
            disabled={isStarting || selectedIds.size === 0}
            className="flex-1 sm:flex-initial flex items-center justify-center gap-1.5 px-4 py-2 rounded-lg font-medium text-xs sm:text-sm bg-white text-zinc-950 hover:bg-zinc-200 active:scale-95 transition-all disabled:opacity-40"
          >
            <Archive className="w-4 h-4" />
            <span>{isStarting ? 'Preparing...' : `ZIP (${selectedIds.size})`}</span>
          </button>
        </div>
      </div>

      {/* Filter and Select All */}
      <div className="flex items-center justify-between gap-4 py-3 text-xs">
        <button
          type="button"
          onClick={toggleSelectAll}
          className="flex items-center gap-1.5 text-zinc-400 hover:text-zinc-200 font-mono"
        >
          {selectedIds.size === tracks.length ? (
            <CheckSquare className="w-3.5 h-3.5 text-white" />
          ) : (
            <Square className="w-3.5 h-3.5" />
          )}
          <span>{selectedIds.size === tracks.length ? 'Deselect All' : `Select All (${tracks.length})`}</span>
        </button>

        <div className="relative w-40 sm:w-56">
          <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-zinc-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Filter..."
            className="w-full bg-zinc-900 border border-zinc-800 rounded-lg pl-8 pr-2.5 py-1 text-xs text-zinc-200 placeholder-zinc-600 focus:outline-none focus:border-zinc-600 font-mono"
          />
        </div>
      </div>

      {/* Track List */}
      <div className="max-h-80 overflow-y-auto space-y-1 pr-1">
        {filteredTracks.map((track, idx) => {
          const isSelected = selectedIds.has(track.id);
          return (
            <div
              key={track.id || idx}
              className={`flex items-center justify-between p-2 rounded-lg text-xs transition-colors border ${
                isSelected
                  ? 'bg-zinc-900/80 border-zinc-800 text-zinc-200'
                  : 'bg-transparent border-transparent text-zinc-500 hover:bg-zinc-900/30'
              }`}
            >
              <div className="flex items-center gap-2.5 min-w-0">
                <button
                  type="button"
                  onClick={() => toggleTrack(track.id)}
                  className="shrink-0 text-zinc-400 hover:text-white"
                >
                  {isSelected ? (
                    <CheckSquare className="w-3.5 h-3.5 text-white" />
                  ) : (
                    <Square className="w-3.5 h-3.5" />
                  )}
                </button>

                <span className="w-5 text-right text-[11px] text-zinc-600 font-mono shrink-0">
                  {idx + 1}
                </span>

                <div className="min-w-0">
                  <p className="font-medium truncate text-zinc-200">{track.title}</p>
                  <p className="text-[11px] text-zinc-500 truncate">{track.artist}</p>
                </div>
              </div>

              <div className="flex items-center gap-2 shrink-0 ml-2">
                {track.duration && (
                  <span className="text-zinc-600 font-mono text-[11px] hidden sm:inline">
                    {formatDuration(track.duration)}
                  </span>
                )}
                <button
                  type="button"
                  onClick={() => handleSingleTrackDownload(track)}
                  title="Download track"
                  className="p-1.5 rounded-md hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200 transition-colors"
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
