import React, { useState } from 'react';
import { Link2, Clipboard, X, Loader2, ArrowRight } from 'lucide-react';

export default function UniversalInput({ url, setUrl, onSubmit, isLoading }) {
  const [isFocused, setIsFocused] = useState(false);

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
    <div className="w-full max-w-2xl mx-auto">
      <div
        className={`flex items-center rounded-xl studio-input p-1.5 transition-all ${
          isFocused ? 'border-zinc-500 ring-1 ring-zinc-500/20' : 'border-zinc-800'
        }`}
      >
        <div className="pl-3 pr-2 text-zinc-500">
          <Link2 className="w-4 h-4" />
        </div>

        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          onKeyDown={handleKeyDown}
          placeholder="Paste URL..."
          autoFocus
          className="w-full bg-transparent px-2 py-2.5 text-sm sm:text-base text-zinc-100 placeholder-zinc-600 focus:outline-none font-mono"
        />

        <div className="flex items-center gap-1.5 pr-1">
          {url ? (
            <button
              type="button"
              onClick={() => setUrl('')}
              className="p-1.5 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800 rounded-lg transition-colors"
              title="Clear"
            >
              <X className="w-4 h-4" />
            </button>
          ) : (
            <button
              type="button"
              onClick={handlePaste}
              className="flex items-center gap-1 px-2 py-1 text-xs text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800 rounded-md transition-colors font-mono"
              title="Paste from clipboard"
            >
              <Clipboard className="w-3.5 h-3.5" />
              <span>Paste</span>
            </button>
          )}

          <button
            type="button"
            onClick={onSubmit}
            disabled={isLoading || !url.trim()}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-lg font-medium text-xs sm:text-sm transition-all ${
              isLoading || !url.trim()
                ? 'bg-zinc-800/60 text-zinc-600 cursor-not-allowed'
                : 'bg-white text-black hover:bg-zinc-200 active:scale-95 shadow-sm'
            }`}
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <>
                <span>Fetch</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
