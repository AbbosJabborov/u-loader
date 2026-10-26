import React, { useState } from 'react';
import { History, Download, Trash2, ChevronDown, ChevronUp } from 'lucide-react';

export default function RecentHistory({ history = [], onClearHistory }) {
  const [isOpen, setIsOpen] = useState(false);
  if (!history || history.length === 0) return null;

  return (
    <div className="w-full max-w-2xl mx-auto mt-8 studio-card rounded-xl p-3 sm:p-4 text-xs font-mono">
      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center gap-2 text-zinc-400 hover:text-zinc-200 transition-colors"
        >
          <History className="w-3.5 h-3.5 text-zinc-500" />
          <span className="font-sans font-medium text-zinc-300">Recent ({history.length})</span>
          {isOpen ? <ChevronUp className="w-3.5 h-3.5 text-zinc-500" /> : <ChevronDown className="w-3.5 h-3.5 text-zinc-500" />}
        </button>

        <button
          type="button"
          onClick={onClearHistory}
          className="flex items-center gap-1 text-[11px] text-zinc-600 hover:text-red-400 transition-colors"
          title="Clear history"
        >
          <Trash2 className="w-3 h-3" />
          <span>Clear</span>
        </button>
      </div>

      {isOpen && (
        <div className="mt-3 pt-3 border-t border-zinc-800/80 divide-y divide-zinc-800/50 max-h-52 overflow-y-auto pr-1">
          {history.map((item, idx) => (
            <div key={item.id || idx} className="py-2 flex items-center justify-between gap-3">
              <div className="min-w-0">
                <p className="text-zinc-200 font-sans truncate">{item.title || item.file_name}</p>
                <span className="text-[10px] text-zinc-500">{item.time || 'Recently'}</span>
              </div>

              {item.download_url && (
                <a
                  href={item.download_url}
                  download={item.file_name}
                  className="shrink-0 p-1.5 rounded-md hover:bg-zinc-800 text-zinc-400 hover:text-zinc-100 transition-colors"
                  title="Download again"
                >
                  <Download className="w-3.5 h-3.5" />
                </a>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
