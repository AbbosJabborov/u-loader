import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import PlatformPills from './components/PlatformPills';
import UniversalInput from './components/UniversalInput';
import MediaCard from './components/MediaCard';
import SpotifyPlaylistView from './components/SpotifyPlaylistView';
import DownloadProgressModal from './components/DownloadProgressModal';
import RecentHistory from './components/RecentHistory';
import FeaturesSection from './components/FeaturesSection';
import { fetchMediaInfo, startDownload } from './api/client';
import { detectPlatform, PLATFORM_CONFIG, PLATFORMS } from './utils/detector';
import { AlertCircle, Sparkles } from 'lucide-react';

const STORAGE_KEY = 'uloader_history';

export default function App() {
  const [url, setUrl] = useState('');
  const [activePlatformHint, setActivePlatformHint] = useState(PLATFORMS.GENERIC);
  const [isLoading, setIsLoading] = useState(false);
  const [isStarting, setIsStarting] = useState(false);
  const [mediaInfo, setMediaInfo] = useState(null);
  const [activeTaskId, setActiveTaskId] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');
  const [history, setHistory] = useState([]);

  // Load history from localStorage on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        setHistory(JSON.parse(saved));
      }
    } catch (e) {
      console.warn('Failed to load history from localStorage');
    }
  }, []);

  const saveToHistory = (taskData) => {
    try {
      const entry = {
        id: taskData.id,
        title: taskData.title || mediaInfo?.title || taskData.file_name,
        platform: taskData.platform || mediaInfo?.platform || 'generic',
        file_name: taskData.file_name,
        download_url: taskData.download_url,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      const updated = [entry, ...history.filter((h) => h.id !== taskData.id)].slice(0, 15);
      setHistory(updated);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
    } catch (e) {
      console.warn('Failed to save to localStorage');
    }
  };

  const handleClearHistory = () => {
    setHistory([]);
    localStorage.removeItem(STORAGE_KEY);
  };

  const handleFetchInfo = async () => {
    if (!url.trim()) return;
    setIsLoading(true);
    setErrorMessage('');
    setMediaInfo(null);

    try {
      const data = await fetchMediaInfo(url.trim());
      setMediaInfo(data);
    } catch (err) {
      const msg = err.response?.data?.error || err.message || 'Failed to extract media information.';
      setErrorMessage(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleStartDownload = async (downloadParams) => {
    setIsStarting(true);
    setErrorMessage('');

    try {
      const res = await startDownload(downloadParams);
      if (res.task_id) {
        setActiveTaskId(res.task_id);
      }
    } catch (err) {
      const msg = err.response?.data?.error || err.message || 'Failed to initiate download task.';
      setErrorMessage(msg);
    } finally {
      setIsStarting(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col justify-between selection:bg-indigo-500/30 selection:text-indigo-200">
      <Navbar />

      <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 pt-12 pb-20">
        
        {/* Hero Header */}
        <div className="text-center max-w-3xl mx-auto space-y-4">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/[0.04] border border-white/10 text-xs font-medium text-gray-300 backdrop-blur-md">
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            <span>YouTube, Instagram, TikTok, Pinterest & Spotify in one place</span>
          </div>

          <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-white leading-tight">
            Download Media{' '}
            <span className="bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
              Without Limits
            </span>
          </h1>

          <p className="text-sm sm:text-base text-gray-400 max-w-xl mx-auto">
            High-speed extraction engine for pristine 4K video, 320kbps MP3s, watermark-free reels, and complete Spotify playlists.
          </p>
        </div>

        {/* Platform Quick Selection Pills */}
        <div className="mt-8 mb-4">
          <PlatformPills
            activePlatform={detectPlatform(url) || activePlatformHint}
            onSelectPlatform={(platformId) => {
              setActivePlatformHint(platformId);
            }}
          />
        </div>

        {/* Universal Smart Input */}
        <UniversalInput
          url={url}
          setUrl={(val) => {
            setUrl(val);
            if (errorMessage) setErrorMessage('');
          }}
          onSubmit={handleFetchInfo}
          isLoading={isLoading}
          platformHint={activePlatformHint}
        />

        {/* Error Alert Box */}
        {errorMessage && (
          <div className="w-full max-w-3xl mx-auto mt-4 p-4 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs sm:text-sm flex items-start gap-3 animate-in fade-in">
            <AlertCircle className="w-5 h-5 shrink-0 text-rose-400 mt-0.5" />
            <div className="flex-1">
              <p className="font-semibold">Unable to download media</p>
              <p className="text-rose-200/80 mt-0.5 break-words">{errorMessage}</p>
            </div>
          </div>
        )}

        {/* Media Extracted Preview */}
        {mediaInfo && (
          mediaInfo.is_playlist ? (
            <SpotifyPlaylistView
              playlistData={mediaInfo}
              onDownload={handleStartDownload}
              isStarting={isStarting}
            />
          ) : (
            <MediaCard
              mediaInfo={mediaInfo}
              onDownload={handleStartDownload}
              isStarting={isStarting}
            />
          )
        )}

        {/* Download Task Active Modal */}
        {activeTaskId && (
          <DownloadProgressModal
            taskId={activeTaskId}
            onClose={() => setActiveTaskId(null)}
            onTaskComplete={saveToHistory}
          />
        )}

        {/* Recent Downloads History */}
        <RecentHistory
          history={history}
          onClearHistory={handleClearHistory}
        />

        {/* Features & Architecture Grid */}
        <FeaturesSection />

      </main>

      {/* Footer */}
      <footer className="w-full border-t border-white/5 bg-[#090a0f]/90 py-8 text-xs text-gray-500 text-center">
        <div className="max-w-6xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p>© {new Date().getFullYear()} U-Loader. Free & Open Universal Media Downloader.</p>
          <div className="flex items-center gap-4 text-[11px]">
            <span className="text-gray-400 font-mono">loader.claive.uz</span>
            <span>•</span>
            <span className="text-gray-400 font-mono">api-loader.claive.uz</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
