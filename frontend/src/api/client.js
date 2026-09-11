import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://api-loader.claive.uz';

const apiClient = axios.create({
  baseURL: API_BASE_URL.replace(/\/+$/, ''),
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 35000,
});

export const fetchMediaInfo = async (url) => {
  const response = await apiClient.post('/api/info/', { url });
  return response.data;
};

export const startDownload = async ({ url, media_type = 'video', format_id = 'best', title = '', selected_tracks = [] }) => {
  const response = await apiClient.post('/api/download/', {
    url,
    media_type,
    format_id,
    title,
    selected_tracks,
  });
  return response.data;
};

export const getTaskStatus = async (taskId) => {
  const response = await apiClient.get(`/api/tasks/${taskId}/`);
  return response.data;
};

export const checkHealth = async () => {
  try {
    const response = await apiClient.get('/api/health/');
    return response.data;
  } catch (err) {
    return { status: 'offline', error: err.message };
  }
};

export default apiClient;
