import React, { useEffect, useState } from 'react';
import { Download, Loader2, CheckCircle2, AlertCircle, X, ExternalLink, HardDrive } from 'lucide-react';
import confetti from 'canvas-confetti';
import { getTaskStatus } from '../api/client';

export default function DownloadProgressModal({ taskId, onClose, onTaskComplete }) {
  const [task, setTask] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!taskId) return;

    let isMounted = true;
    let pollInterval = null;

    const poll = async () => {
      try {
        const data = await getTaskStatus(taskId);
        if (!isMounted) return;

        setTask(data);

        if (data.status === 'completed') {
          clearInterval(pollInterval);
          // Trigger celebration confetti
          try {
            confetti({
              particleCount: 80,
              spread: 60,
              origin: { y: 0.6 },
            });
          } catch (e) {}

          if (onTaskComplete) {
            onTaskComplete(data);
          }
        } else if (data.status === 'failed') {
          clearInterval(pollInterval);
          setError(data.error_message || 'Download task failed.');
        }
      } catch (err) {
        if (!isMounted) return;
        setError(err.response?.data?.error || err.message || 'Error connecting to server.');
      }
    };

    poll();
    pollInterval = setInterval(poll, 1200);

    return () => {
      isMounted = false;
      if (pollInterval) clearInterval(pollInterval);
    };
  }, [taskId]);

  const formatFileSize = (bytes) => {
    if (!bytes) return '';
    const mb = bytes / (1024 * 1024);
    if (mb > 1024) return `${(mb / 1024).toFixed(2)} GB`;
    return `${mb.toFixed(1)} MB`;
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
      case 'failed':
        return 'text-rose-400 bg-rose-500/10 border-rose-500/20';
      default:
        return 'text-indigo-400 bg-indigo-500/10 border-indigo-500/20';
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-lg glass-panel rounded-3xl p-6 sm:p-8 border border-white/10 shadow-2xl overflow-hidden">
        
        {/* Close Button */}
        <button
          type="button"
          onClick={onClose}
          className="absolute top-5 right-5 p-2 text-gray-400 hover:text-white rounded-xl hover:bg-white/5 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Modal Header */}
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-indigo-600 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/25">
            {task?.status === 'completed' ? (
              <CheckCircle2 className="w-6 h-6 text-white" />
            ) : task?.status === 'failed' || error ? (
              <AlertCircle className="w-6 h-6 text-white" />
            ) : (
              <Loader2 className="w-6 h-6 text-white animate-spin" />
            )}
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">
              {task?.status === 'completed'
                ? 'Download Complete!'
                : task?.status === 'failed' || error
                ? 'Processing Error'
                : 'Downloading Media...'}
            </h3>
            <p className="text-xs text-gray-400 truncate max-w-xs">
              {task?.title || 'Universal Downloader'}
            </p>
          </div>
        </div>

        {/* Progress Display */}
        <div className="mt-6">
          <div className="flex items-center justify-between text-xs mb-2">
            <span className="text-gray-300 font-medium">
              {task?.progress_message || 'Preparing task in background worker...'}
            </span>
            <span className="font-mono text-indigo-300 font-semibold">
              {task ? `${Math.round(task.progress)}%` : '0%'}
            </span>
          </div>

          {/* Progress Bar Container */}
          <div className="w-full h-3 bg-black/40 rounded-full overflow-hidden p-0.5 border border-white/10 shadow-inner">
            <div
              className={`h-full rounded-full transition-all duration-300 ${
                task?.status === 'completed'
                  ? 'bg-gradient-to-r from-emerald-500 to-green-500'
                  : task?.status === 'failed' || error
                  ? 'bg-rose-500'
                  : 'bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500'
              }`}
              style={{ width: `${task?.progress || 5}%` }}
            />
          </div>
        </div>

        {/* Task Details / File Information */}
        {task?.status === 'completed' && (
          <div className="mt-6 p-4 rounded-2xl bg-white/[0.03] border border-white/5 space-y-2 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-gray-400">File Name:</span>
              <span className="font-mono text-white truncate max-w-[200px]" title={task.file_name}>
                {task.file_name}
              </span>
            </div>
            {task.file_size ? (
              <div className="flex items-center justify-between">
                <span className="text-gray-400">File Size:</span>
                <span className="text-gray-200 font-mono">{formatFileSize(task.file_size)}</span>
              </div>
            ) : null}
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Cloud Expiration:</span>
              <span className="text-amber-400/90 font-medium">Expires in 60 mins</span>
            </div>
          </div>
        )}

        {/* Error Details */}
        {(task?.status === 'failed' || error) && (
          <div className="mt-6 p-4 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-xs text-rose-300 space-y-1">
            <p className="font-semibold">Failed to process media:</p>
            <p className="text-rose-200/80 break-words">{error || task?.error_message}</p>
          </div>
        )}

        {/* Actions Footer */}
        <div className="mt-7 flex items-center justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2.5 rounded-xl text-xs font-semibold text-gray-400 hover:text-white hover:bg-white/5 transition-colors"
          >
            Close
          </button>

          {task?.status === 'completed' && task?.download_url && (
            <a
              href={task.download_url}
              download={task.file_name}
              className="flex items-center gap-2 px-6 py-2.5 rounded-xl text-xs font-bold bg-gradient-to-r from-emerald-500 to-green-600 text-white hover:brightness-110 shadow-lg shadow-emerald-500/25 active:scale-95 transition-all"
            >
              <Download className="w-4 h-4" />
              <span>Save to Device</span>
            </a>
          )}
        </div>

      </div>
    </div>
  );
}
