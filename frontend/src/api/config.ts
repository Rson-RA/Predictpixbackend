import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true
});

// Add request interceptor to include auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token && config.headers) {
    config.headers['Authorization'] = `Bearer ${token}`;
  }
  return config;
});

let isRefreshing = false;
let failedQueue: any[] = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });

  failedQueue = [];
};

// Add response interceptor to handle common errors
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If the error is not 401 or the request has already been retried, reject it
    if (error.response?.status !== 401 || originalRequest._retry) {
      return Promise.reject(error);
    }

    if (isRefreshing) {
      try {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        });
      } catch (err) {
        return Promise.reject(err);
      }
    }

    originalRequest._retry = true;
    isRefreshing = true;

    try {
      // Clear the current token since it's invalid
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user_data');
      delete axios.defaults.headers.common['Authorization'];

      // Redirect to login page
      window.location.href = '/login';
      
      processQueue(null, null);
      return Promise.reject(error);
    } catch (refreshError) {
      processQueue(refreshError, null);
      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  }
);

export default api; 