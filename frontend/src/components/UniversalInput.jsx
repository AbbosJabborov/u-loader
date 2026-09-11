import React, { useState } from 'react';
import { Search, Clipboard, X, Loader2, ArrowRight } from 'lucide-react';
import { detectPlatform, PLATFORM_CONFIG, PLATFORMS } from '../utils/detector';

export default function UniversalInput({ url, setUrl, onSubmit, isLoading, platformHint }) {
  const [isFocused, setIsFocused] = useState(false);
  const detectedPlatform = detectPlatform(url) || platformHint || PLATFORMS.GENERIC;
  const config = PLATFORM_CONFIG[detectedPlatform] || PLATFORM_CONFIG[PLATFORMS.GENERIC];

  const handlePaste = async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text) {
        setUrl(text);
      }
    } catch (err) {
      console.warn('Clipboard paste not supported or denied', err);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !isLoading && url.trim()) {
      onSubmit();
    }
  };

  return (
    <div className="w-full max-w-3xl mx-auto">
      <div
        className={`relative flex items-center rounded-2xl glass-input transition-all duration-300 p-1.5 sm:p-2 ${
          isFocused ? 'ring-2 ring-indigo-500/30 border-indigo-500/60 shadow-2xl shadow-indigo-500/10' : ''
        }`}
      >
        {/* Left Platform Tag */}
        <div className="hidden sm:flex items-center pl-2 pr-1">
          <span
            className={`px-2.5 py-1 rounded-lg text-xs font-semibold uppercase tracking-wider border transition-colors ${config.badgeBg}`}
          >
            {config.name}
          </span>
        </div>

        {/* Text Input */}
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          onKeyDown={handleKeyDown}
          placeholder={config.placeholder}
          className="w-full bg-transparent px-3 py-3 text-sm sm:text-base text-gray-100 placeholder-gray-500 focus:outline-none"
        />

        {/* Clear & Paste Shortcuts */}
        <div className="flex items-center gap-1.5 pr-2">
          {url ? (
            <button
              type="button"
              onClick={() => setUrl('')}
              className="p-2 text-gray-400 hover:text-gray-200 hover:bg-white/5 rounded-lg transition-colors"
              title="Clear input"
            >
              <X className="w-4 h-4" />
            </button>
          ) : (
            <button
              type="button"
              onClick={handlePaste}
              className="hidden sm:flex items-center gap-1 px-2.5 py-1.5 text-xs text-gray-400 hover:text-gray-200 hover:bg-white/5 rounded-lg border border-white/5 transition-colors"
              title="Paste from clipboard"
            >
              <Clipboard className="w-3.5 h-3.5" />
              <span>Paste</span>
            </button>
          )}

          {/* Action Button */}
          <button
            type="button"
            onClick={onSubmit}
            disabled={isLoading || !url.trim()}
            className={`flex items-center gap-2 px-5 py-3 rounded-xl font-semibold text-sm shadow-lg transition-all duration-200 ${
              isLoading || !url.trim()
                ? 'bg-gray-800 text-gray-500 cursor-not-allowed border border-white/5'
                : 'bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 text-white hover:brightness-110 active:scale-95 shadow-indigo-500/25'
            }`}
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span className="hidden sm:inline">Analyzing...</span>
              </>
            ) : (
              <>
                <span>Download</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </div>
      </div>

      {/* Dynamic Hint */}
      <div className="mt-2.5 px-2 flex items-center justify-between text-xs text-gray-400">
        <div className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-indigo-400"></span>
          <span>{config.hint}</span>
        </div>
        <span className="hidden sm:inline text-gray-500">Press Enter ↵</span>
      </div>
    </div>
  );
}
