import React from 'react';
import { Zap, ShieldCheck, Music, Video, RefreshCw, Smartphone } from 'lucide-react';

const FEATURES = [
  {
    icon: Video,
    title: 'Crystal Clear HD & 4K',
    description: 'Extract highest quality video streams up to 4K resolution with original audio remuxed.',
    color: 'text-rose-400',
    bg: 'bg-rose-500/10 border-rose-500/20',
  },
  {
    icon: Music,
    title: 'Spotify Playlists to ZIP',
    description: 'Download entire playlists or choose individual songs with embedded album artwork and ID3 tags.',
    color: 'text-emerald-400',
    bg: 'bg-emerald-500/10 border-emerald-500/20',
  },
  {
    icon: Zap,
    title: 'No Watermark TikToks',
    description: 'Clean HD TikTok videos without any logo or watermark overlay, ready for your offline collection.',
    color: 'text-cyan-400',
    bg: 'bg-cyan-500/10 border-cyan-500/20',
  },
  {
    icon: RefreshCw,
    title: 'Auto-Cleanup System',
    description: 'Temporary files are safely wiped from the server after 60 minutes for privacy and performance.',
    color: 'text-amber-400',
    bg: 'bg-amber-500/10 border-amber-500/20',
  },
  {
    icon: ShieldCheck,
    title: '100% Free & No Ads',
    description: 'Fast, secure, and open-source media downloading without popup ads or intrusive tracking.',
    color: 'text-indigo-400',
    bg: 'bg-indigo-500/10 border-indigo-500/20',
  },
  {
    icon: Smartphone,
    title: 'Mobile & Desktop Ready',
    description: 'Fully responsive glassmorphism web app that works on iPhone, Android, Mac, and Windows.',
    color: 'text-purple-400',
    bg: 'bg-purple-500/10 border-purple-500/20',
  },
];

export default function FeaturesSection() {
  return (
    <div className="w-full max-w-5xl mx-auto mt-20 pt-10 border-t border-white/5">
      <div className="text-center mb-10">
        <h3 className="text-lg sm:text-xl font-bold text-white tracking-tight">
          Engineered for Speed and Simplicity
        </h3>
        <p className="text-xs sm:text-sm text-gray-400 mt-1 max-w-lg mx-auto">
          One universal engine powered by yt-dlp, FFmpeg, and asynchronous Celery workers.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
        {FEATURES.map((feat, idx) => {
          const Icon = feat.icon;
          return (
            <div
              key={idx}
              className="p-5 rounded-2xl glass-panel glass-panel-hover border border-white/5 flex flex-col justify-between"
            >
              <div>
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center border ${feat.bg} mb-3.5`}>
                  <Icon className={`w-5 h-5 ${feat.color}`} />
                </div>
                <h4 className="text-sm font-bold text-gray-200">{feat.title}</h4>
                <p className="text-xs text-gray-400 mt-1.5 leading-relaxed">{feat.description}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
