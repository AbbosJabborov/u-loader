import React, { useState, useEffect } from 'react';
import UniversalInput from './components/UniversalInput';
import MediaCard from './components/MediaCard';
import SpotifyPlaylistView from './components/SpotifyPlaylistView';
import DownloadProgressModal from './components/DownloadProgressModal';
import RecentHistory from './components/RecentHistory';
import BackgroundCanvas from './components/BackgroundCanvas';
import { fetchMediaInfo, startDownload } from './api/client';
import { AlertCircle } from 'lucide-react';

const STORAGE_KEY = 'uloader_history';

export default function App() {
  const [url, setUrl] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isStarting, setIsStarting] = useState(false);
  const [mediaInfo, setMediaInfo] = useState(null);
  const [activeTaskId, setActiveTaskId] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');
  const [history, setHistory] = useState([]);

  // Load history from localStorage
  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        setHistory(JSON.parse(saved));
      }
    } catch (e) {
      console.warn('Failed to load history');
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
    <div className="relative min-h-screen flex flex-col justify-between selection:bg-zinc-800 selection:text-zinc-100">
      {/* Animated Subtle Background Canvas */}
      <BackgroundCanvas />

      {/* Main Content Area */}
      <div className="relative z-10 flex-1 flex flex-col justify-center px-4 py-12 sm:py-20">
        
        {/* Minimal Top Brand */}
        <div className="w-full max-w-2xl mx-auto flex items-center justify-between mb-8">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span className="font-mono text-sm font-semibold tracking-wider text-zinc-300">
              u-loader
            </span>
          </div>
          <span className="font-mono text-xs text-zinc-600">
            v2.0
          </span>
        </div>

        {/* Focused Input Bar */}
        <UniversalInput
          url={url}
          setUrl={(val) => {
            setUrl(val);
            if (errorMessage) setErrorMessage('');
          }}
          onSubmit={handleFetchInfo}
          isLoading={isLoading}
        />

        {/* Error Alert Box */}
        {errorMessage && (
          <div className="w-full max-w-2xl mx-auto mt-4 p-3 rounded-xl bg-red-950/30 border border-red-900/50 text-red-300 text-xs flex items-start gap-2.5">
            <AlertCircle className="w-4 h-4 shrink-0 text-red-400 mt-0.5" />
            <div className="flex-1">
              <p className="font-medium">Error extracting media</p>
              <p className="text-red-300/80 mt-0.5 break-words font-mono text-[11px]">{errorMessage}</p>
            </div>
          </div>
        )}

        {/* Extracted Media Details */}
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

        {/* Download Task Active Progress */}
        {activeTaskId && (
          <DownloadProgressModal
            taskId={activeTaskId}
            onClose={() => setActiveTaskId(null)}
            onTaskComplete={saveToHistory}
          />
        )}

        {/* Collapsible History */}
        <RecentHistory
          history={history}
          onClearHistory={handleClearHistory}
        />

      </div>

      {/* Minimal Footer */}
      <footer className="relative z-10 py-4 text-center font-mono text-[11px] text-zinc-600">
        u-loader • personal media downloader
      </footer>
    </div>
  );
}
