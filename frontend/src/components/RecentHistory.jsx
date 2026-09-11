import React from 'react';
import { History, Download, Trash2, ExternalLink, FileCheck } from 'lucide-react';
import { PLATFORM_CONFIG, PLATFORMS } from '../utils/detector';

export default function RecentHistory({ history = [], onClearHistory }) {
  if (!history || history.length === 0) return null;

  return (
    <div className="w-full max-w-3xl mx-auto mt-12 glass-panel rounded-3xl p-5 sm:p-6 border border-white/5">
      <div className="flex items-center justify-between pb-4 border-b border-white/5">
        <div className="flex items-center gap-2">
          <History className="w-4 h-4 text-[#6355F6]" />
          <h4 className="text-sm font-bold text-white">Recent Downloads</h4>
          <span className="text-[11px] px-2 py-0.5 rounded-full bg-[#6355F6]/10 text-[#00E5FF] border border-[#6355F6]/20">
            {history.length}
          </span>
        </div>

        <button
          type="button"
          onClick={onClearHistory}
          className="flex items-center gap-1 text-[11px] text-slate-500 hover:text-rose-400 transition-colors"
        >
          <Trash2 className="w-3 h-3" />
          <span>Clear</span>
        </button>
      </div>

      <div className="mt-3 divide-y divide-white/5 max-h-60 overflow-y-auto">
        {history.map((item, idx) => {
          const config = PLATFORM_CONFIG[item.platform] || PLATFORM_CONFIG[PLATFORMS.GENERIC];
          return (
            <div key={item.id || idx} className="py-2.5 flex items-center justify-between gap-3 text-xs">
              <div className="min-w-0 flex items-center gap-2.5">
                <FileCheck className="w-4 h-4 text-[#00E5FF] shrink-0" />
                <div className="min-w-0">
                  <p className="text-slate-200 font-medium truncate">{item.title || item.file_name}</p>
                  <div className="flex items-center gap-2 text-[10px] text-slate-500 mt-0.5">
                    <span className="uppercase font-semibold text-[#00E5FF]">
                      {config.name}
                    </span>
                    <span>•</span>
                    <span>{item.time || 'Recently'}</span>
                  </div>
                </div>
              </div>

              {item.download_url && (
                <a
                  href={item.download_url}
                  download={item.file_name}
                  className="shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#6355F6]/15 hover:bg-[#6355F6] text-[#00E5FF] hover:text-white border border-[#6355F6]/30 transition-all text-xs font-semibold"
                >
                  <Download className="w-3 h-3" />
                  <span className="hidden sm:inline">Download</span>
                </a>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
