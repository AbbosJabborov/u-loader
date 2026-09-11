import React, { useState, useEffect } from 'react';
import { DownloadCloud, ShieldCheck, Wifi, WifiOff, Sparkles } from 'lucide-react';
import { checkHealth } from '../api/client';

export default function Navbar() {
  const [apiStatus, setApiStatus] = useState('checking');

  useEffect(() => {
    let isMounted = true;
    const verify = async () => {
      const res = await checkHealth();
      if (isMounted) {
        setApiStatus(res.status === 'healthy' ? 'online' : 'offline');
      }
    };
    verify();
    const interval = setInterval(verify, 30000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <header className="sticky top-0 z-40 w-full border-b border-white/5 bg-[#090a0f]/80 backdrop-blur-xl">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        
        {/* Brand Logo */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-purple-600 to-pink-500 p-[1px] shadow-lg shadow-indigo-500/20">
            <div className="w-full h-full bg-[#0d0f18] rounded-[11px] flex items-center justify-center">
              <DownloadCloud className="w-5 h-5 text-indigo-400" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-white via-gray-200 to-gray-400 bg-clip-text text-transparent">
                U-Loader
              </span>
              <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                v2.0
              </span>
            </div>
            <p className="text-[11px] text-gray-500 -mt-0.5 hidden sm:block">
              Universal Media Downloader
            </p>
          </div>
        </div>

        {/* Status indicator & features */}
        <div className="flex items-center gap-3 sm:gap-4 text-xs">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/[0.04] border border-white/[0.08]">
            {apiStatus === 'online' ? (
              <>
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                </span>
                <span className="text-gray-300 font-medium hidden sm:inline">Engine Online</span>
              </>
            ) : apiStatus === 'offline' ? (
              <>
                <span className="h-2 w-2 rounded-full bg-amber-500"></span>
                <span className="text-gray-400 font-medium">Connecting...</span>
              </>
            ) : (
              <>
                <span className="h-2 w-2 rounded-full bg-gray-500 animate-pulse"></span>
                <span className="text-gray-400 font-medium">Checking</span>
              </>
            )}
          </div>

          <div className="hidden md:flex items-center gap-1.5 text-gray-400">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>High Quality & Free</span>
          </div>
        </div>

      </div>
    </header>
  );
}
