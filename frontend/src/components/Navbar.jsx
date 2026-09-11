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
    <header className="sticky top-0 z-40 w-full border-b border-white/[0.06] bg-[#090a10]/85 backdrop-blur-xl">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        
        {/* Brand Logo with User's icon.png */}
        <div className="flex items-center gap-3">
          <div className="relative w-10 h-10 rounded-2xl bg-gradient-to-tr from-[#6355F6] to-[#00E5FF] p-[1.5px] shadow-lg shadow-[#6355F6]/25">
            <div className="w-full h-full bg-[#0e101a] rounded-[14px] flex items-center justify-center overflow-hidden p-1">
              <img
                src="/icon.png"
                alt="U-Loader Logo"
                className="w-full h-full object-contain"
              />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-lg tracking-tight text-white">
                U-Loader
              </span>
              <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded-full bg-[#6355F6]/15 text-[#00E5FF] border border-[#6355F6]/30">
                PRO
              </span>
            </div>
            <p className="text-[11px] text-slate-400 -mt-0.5 hidden sm:block">
              Universal Media Engine
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
