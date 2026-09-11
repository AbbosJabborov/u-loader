import React, { useState } from 'react';
import { Download, Film, Music, Clock, User, CheckCircle2, Sparkles } from 'lucide-react';
import { PLATFORM_CONFIG, PLATFORMS } from '../utils/detector';

export default function MediaCard({ mediaInfo, onDownload, isStarting }) {
  if (!mediaInfo) return null;

  const { title, thumbnail, duration, author, platform, formats = [] } = mediaInfo;
  const config = PLATFORM_CONFIG[platform] || PLATFORM_CONFIG[PLATFORMS.GENERIC];

  // Group formats into video and audio
  const videoFormats = formats.filter((f) => f.type === 'video');
  const audioFormats = formats.filter((f) => f.type === 'audio');

  const [activeTab, setActiveTab] = useState(videoFormats.length > 0 ? 'video' : 'audio');
  const [selectedFormat, setSelectedFormat] = useState(
    videoFormats.length > 0 ? videoFormats[0].id : (audioFormats[0]?.id || 'best')
  );

  const formatDuration = (secs) => {
    if (!secs) return '';
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  const handleStart = () => {
    const chosen = formats.find((f) => f.id === selectedFormat);
    onDownload({
      url: mediaInfo.url,
      media_type: activeTab,
      format_id: selectedFormat,
      title: title,
    });
  };

  return (
    <div className="w-full max-w-3xl mx-auto mt-8 glass-panel rounded-3xl p-5 sm:p-7 transition-all border border-white/10 shadow-2xl">
      <div className="flex flex-col md:flex-row gap-6">
        
        {/* Media Thumbnail */}
        <div className="relative w-full md:w-72 shrink-0 aspect-video md:aspect-[4/3] rounded-2xl overflow-hidden bg-black/40 border border-white/10 shadow-inner group">
          {thumbnail ? (
            <img
              src={thumbnail}
              alt={title}
              className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-gray-600">
              <Film className="w-12 h-12" />
            </div>
          )}

          {/* Platform badge overlay */}
          <div className="absolute top-3 left-3">
            <span className={`px-2.5 py-1 rounded-lg text-xs font-semibold uppercase backdrop-blur-md border ${config.badgeBg}`}>
              {config.name}
            </span>
          </div>

          {/* Duration overlay */}
          {duration ? (
            <div className="absolute bottom-3 right-3 flex items-center gap-1 px-2 py-0.5 rounded-md bg-black/70 backdrop-blur-md text-[11px] font-mono text-gray-200">
              <Clock className="w-3 h-3" />
              <span>{formatDuration(duration)}</span>
            </div>
          ) : null}
        </div>

        {/* Media Info & Download Formats */}
        <div className="flex-1 flex flex-col justify-between">
          <div>
            <h3 className="text-lg sm:text-xl font-bold text-white line-clamp-2 leading-snug">
              {title}
            </h3>

            {author && (
              <div className="flex items-center gap-1.5 text-xs text-gray-400 mt-2">
                <User className="w-3.5 h-3.5 text-gray-500" />
                <span className="font-medium">{author}</span>
              </div>
            )}

            {/* Video / Audio Switcher */}
            <div className="flex items-center gap-2 mt-5 p-1 rounded-xl bg-black/40 border border-white/5 w-fit">
              {videoFormats.length > 0 && (
                <button
                  type="button"
                  onClick={() => {
                    setActiveTab('video');
                    setSelectedFormat(videoFormats[0].id);
                  }}
                  className={`flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                    activeTab === 'video'
                      ? 'bg-indigo-600 text-white shadow-md'
                      : 'text-gray-400 hover:text-white'
                  }`}
                >
                  <Film className="w-3.5 h-3.5" />
                  <span>Video (MP4)</span>
                </button>
              )}
              {audioFormats.length > 0 && (
                <button
                  type="button"
                  onClick={() => {
                    setActiveTab('audio');
                    setSelectedFormat(audioFormats[0].id);
                  }}
                  className={`flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                    activeTab === 'audio'
                      ? 'bg-indigo-600 text-white shadow-md'
                      : 'text-gray-400 hover:text-white'
                  }`}
                >
                  <Music className="w-3.5 h-3.5" />
                  <span>Audio (MP3)</span>
                </button>
              )}
            </div>

            {/* Format Pills */}
            <div className="grid grid-cols-2 sm:grid-cols-2 gap-2 mt-4">
              {(activeTab === 'video' ? videoFormats : audioFormats).map((fmt) => {
                const isSelected = selectedFormat === fmt.id;
                return (
                  <button
                    key={fmt.id}
                    type="button"
                    onClick={() => setSelectedFormat(fmt.id)}
                    className={`flex items-center justify-between px-3 py-2 rounded-xl text-xs font-medium border transition-all ${
                      isSelected
                        ? 'bg-indigo-500/15 border-indigo-500 text-white shadow-sm'
                        : 'bg-white/[0.03] border-white/[0.08] text-gray-400 hover:bg-white/[0.06] hover:text-gray-200'
                    }`}
                  >
                    <span>{fmt.label}</span>
                    {isSelected && <CheckCircle2 className="w-3.5 h-3.5 text-indigo-400" />}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Trigger Download */}
          <div className="mt-6 pt-4 border-t border-white/5 flex items-center justify-end">
            <button
              type="button"
              onClick={handleStart}
              disabled={isStarting}
              className="w-full sm:w-auto flex items-center justify-center gap-2 px-6 py-3 rounded-xl font-semibold text-sm bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 text-white shadow-lg shadow-indigo-600/30 hover:brightness-110 active:scale-95 transition-all"
            >
              <Download className="w-4 h-4" />
              <span>{isStarting ? 'Preparing Task...' : 'Download File'}</span>
            </button>
          </div>

        </div>

      </div>
    </div>
  );
}
