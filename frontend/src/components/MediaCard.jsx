import React, { useState } from 'react';
import { Download, Film, Music, Image as ImageIcon, Check } from 'lucide-react';

export default function MediaCard({ mediaInfo, onDownload, isStarting }) {
  if (!mediaInfo) return null;

  const { title, thumbnail, duration, author, formats = [] } = mediaInfo;

  // Group formats into video, audio, and image/carousel
  const videoFormats = formats.filter((f) => f.type === 'video');
  const audioFormats = formats.filter((f) => f.type === 'audio');
  const imageFormats = formats.filter((f) => f.type === 'image' || f.type === 'carousel');

  const initialTab =
    imageFormats.length > 0 && videoFormats.length === 0
      ? 'image'
      : videoFormats.length > 0
      ? 'video'
      : audioFormats.length > 0
      ? 'audio'
      : 'image';

  const [activeTab, setActiveTab] = useState(initialTab);

  const getFormatList = () => {
    if (activeTab === 'video') return videoFormats;
    if (activeTab === 'image') return imageFormats;
    return audioFormats;
  };

  const currentFormats = getFormatList();
  const [selectedFormat, setSelectedFormat] = useState(
    currentFormats[0]?.id || formats[0]?.id || 'best'
  );

  const formatDuration = (secs) => {
    if (!secs) return '';
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  const handleStart = () => {
    const selectedFmtObj = formats.find((f) => f.id === selectedFormat);
    onDownload({
      url: mediaInfo.url,
      media_type: selectedFmtObj?.type || activeTab,
      format_id: selectedFormat,
      title: title,
    });
  };

  return (
    <div className="w-full max-w-2xl mx-auto mt-6 studio-card rounded-xl p-4 sm:p-5">
      <div className="flex flex-col sm:flex-row gap-4 items-start">
        
        {/* Compact Thumbnail */}
        {thumbnail ? (
          <div className="w-full sm:w-36 aspect-video sm:aspect-square shrink-0 rounded-lg overflow-hidden bg-zinc-900 border border-zinc-800">
            <img
              src={thumbnail}
              alt={title}
              className="w-full h-full object-cover"
            />
          </div>
        ) : null}

        {/* Content Details */}
        <div className="flex-1 w-full min-w-0">
          <h3 className="text-sm sm:text-base font-semibold text-zinc-100 line-clamp-2 leading-snug">
            {title}
          </h3>

          <div className="flex items-center gap-2 text-xs text-zinc-500 mt-1 font-mono">
            {author && <span className="truncate max-w-[200px]">{author}</span>}
            {author && duration && <span>•</span>}
            {duration && <span>{formatDuration(duration)}</span>}
          </div>

          {/* Type Switcher Tabs */}
          <div className="flex items-center gap-1.5 mt-3 pt-3 border-t border-zinc-800/80">
            {videoFormats.length > 0 && (
              <button
                type="button"
                onClick={() => {
                  setActiveTab('video');
                  setSelectedFormat(videoFormats[0].id);
                }}
                className={`flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-medium transition-colors ${
                  activeTab === 'video'
                    ? 'bg-zinc-100 text-zinc-950 font-semibold'
                    : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50'
                }`}
              >
                <Film className="w-3.5 h-3.5" />
                <span>Video</span>
              </button>
            )}

            {imageFormats.length > 0 && (
              <button
                type="button"
                onClick={() => {
                  setActiveTab('image');
                  setSelectedFormat(imageFormats[0].id);
                }}
                className={`flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-medium transition-colors ${
                  activeTab === 'image'
                    ? 'bg-zinc-100 text-zinc-950 font-semibold'
                    : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50'
                }`}
              >
                <ImageIcon className="w-3.5 h-3.5" />
                <span>Photos</span>
              </button>
            )}

            {audioFormats.length > 0 && (
              <button
                type="button"
                onClick={() => {
                  setActiveTab('audio');
                  setSelectedFormat(audioFormats[0].id);
                }}
                className={`flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-medium transition-colors ${
                  activeTab === 'audio'
                    ? 'bg-zinc-100 text-zinc-950 font-semibold'
                    : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50'
                }`}
              >
                <Music className="w-3.5 h-3.5" />
                <span>Audio</span>
              </button>
            )}
          </div>

          {/* Format Selection Chips */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5 mt-3">
            {currentFormats.map((fmt) => {
              const isSelected = selectedFormat === fmt.id;
              return (
                <button
                  key={fmt.id}
                  type="button"
                  onClick={() => setSelectedFormat(fmt.id)}
                  className={`flex items-center justify-between px-3 py-2 rounded-lg text-xs font-mono transition-all text-left ${
                    isSelected
                      ? 'bg-zinc-800 text-white border border-zinc-600'
                      : 'bg-zinc-900/60 text-zinc-400 hover:bg-zinc-800/60 hover:text-zinc-200 border border-zinc-800/80'
                  }`}
                >
                  <span className="truncate pr-2">{fmt.label}</span>
                  {isSelected && <Check className="w-3.5 h-3.5 shrink-0 text-zinc-200" />}
                </button>
              );
            })}
          </div>

          {/* Action Trigger */}
          <div className="mt-4 pt-3 border-t border-zinc-800/80 flex justify-end">
            <button
              type="button"
              onClick={handleStart}
              disabled={isStarting}
              className="w-full sm:w-auto flex items-center justify-center gap-2 px-5 py-2 rounded-lg font-medium text-xs sm:text-sm bg-white text-zinc-950 hover:bg-zinc-200 active:scale-95 transition-all disabled:opacity-50"
            >
              <Download className="w-4 h-4" />
              <span>{isStarting ? 'Preparing...' : 'Download'}</span>
            </button>
          </div>

        </div>
      </div>
    </div>
  );
}
