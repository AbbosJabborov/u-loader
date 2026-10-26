import React, { useEffect, useState } from 'react';
import { Download, Loader2, Check, AlertCircle, X } from 'lucide-react';
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
          if (onTaskComplete) {
            onTaskComplete(data);
          }
          // Automatically trigger download
          if (data.download_url) {
            const a = document.createElement('a');
            a.href = data.download_url;
            a.download = data.file_name || 'download';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
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
    pollInterval = setInterval(poll, 1000);

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

  return (
    <div className="w-full max-w-2xl mx-auto mt-4 studio-card rounded-xl p-4 text-xs font-mono">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2.5 min-w-0">
          {task?.status === 'completed' ? (
            <div className="w-5 h-5 rounded-full bg-zinc-100 text-zinc-950 flex items-center justify-center shrink-0">
              <Check className="w-3.5 h-3.5" />
            </div>
          ) : task?.status === 'failed' || error ? (
            <AlertCircle className="w-5 h-5 text-red-400 shrink-0" />
          ) : (
            <Loader2 className="w-5 h-5 text-zinc-400 animate-spin shrink-0" />
          )}

          <div className="min-w-0">
            <p className="font-sans font-medium text-zinc-200 text-xs sm:text-sm truncate">
              {task?.status === 'completed'
                ? (task.file_name || 'Download complete')
                : task?.status === 'failed' || error
                ? 'Download failed'
                : (task?.progress_message || 'Downloading...')}
            </p>
            {task?.file_size ? (
              <span className="text-[11px] text-zinc-500">{formatFileSize(task.file_size)}</span>
            ) : null}
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {task?.status === 'completed' && task?.download_url ? (
            <a
              href={task.download_url}
              download={task.file_name}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white text-zinc-950 font-sans font-semibold text-xs hover:bg-zinc-200 transition-colors"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Save</span>
            </a>
          ) : (
            <span className="text-zinc-400 font-bold">
              {task ? `${Math.round(task.progress)}%` : '0%'}
            </span>
          )}

          <button
            type="button"
            onClick={onClose}
            className="p-1.5 text-zinc-500 hover:text-zinc-300 rounded-md transition-colors"
            title="Dismiss"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Progress Line */}
      {task?.status !== 'completed' && !error && task?.status !== 'failed' && (
        <div className="w-full h-1 bg-zinc-800 rounded-full overflow-hidden mt-3">
          <div
            className="h-full bg-white transition-all duration-300"
            style={{ width: `${task?.progress || 3}%` }}
          />
        </div>
      )}

      {/* Error Message */}
      {(task?.status === 'failed' || error) && (
        <p className="mt-2 text-red-400 text-xs font-sans">
          {error || task?.error_message}
        </p>
      )}
    </div>
  );
}
