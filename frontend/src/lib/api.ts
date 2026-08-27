import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import { useAuthStore } from '../store/useAuthStore';

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:3000/api/v1";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json' } });

// Add request interceptor to attach auth token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = useAuthStore.getState().token;
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Add response interceptor to handle token refresh
let isRefreshing = false;
let refreshPromise: Promise<string | null> | null = null;
let failedQueue: Array<{
  resolve: (value: unknown) => void;
  reject: (reason: unknown) => void;
}> = [];

const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing && refreshPromise) {
        return refreshPromise.then(
          (token) => {
            if (originalRequest.headers && token) {
              originalRequest.headers.Authorization = `Bearer ${token}`;
            }
            return apiClient(originalRequest);
          },
          (refreshError) => Promise.reject(refreshError)
        );
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = useAuthStore.getState().refreshToken;

      if (!refreshToken) {
        useAuthStore.getState().logout();
        return Promise.reject(error);
      }

      refreshPromise = Promise.race([
        axios.post(`${API_BASE_URL}/auth/refresh`, { refreshToken }).then(
          (response) => response.data.token
        ),
        new Promise<never>((_, reject) =>
          setTimeout(() => reject(new Error('Refresh token timeout')), 10000)
        ),
      ]).catch((refreshError) => {
        useAuthStore.getState().logout();
        throw refreshError;
      });

      try {
        const token = await refreshPromise;

        useAuthStore.setState({
          token,
          refreshToken: useAuthStore.getState().refreshToken });

        apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        processQueue(null, token);

        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${token}`;
        }
        return apiClient(originalRequest);
      } finally {
        isRefreshing = false;
        refreshPromise = null;
      }
    }

    return Promise.reject(error);
  }
);