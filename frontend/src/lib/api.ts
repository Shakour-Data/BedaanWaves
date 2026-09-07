import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import { useAuthStore } from '../store/useAuthStore';
import { API_BASE_URL } from './utils';

export function getApiErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    const axiosErr = error as AxiosError<{ detail?: unknown }>;
    const detail = axiosErr.response?.data?.detail;
    if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0] as { msg?: unknown };
      if (typeof first?.msg === 'string') return first.msg;
    }
    if (typeof detail === 'string') return detail;
    return error.message;
  }
  return String(error);
}

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json' } });

// Add request interceptor to attach auth token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    try {
      const state = useAuthStore.getState ? useAuthStore.getState() : null;
      const token = state?.token;
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    } catch {
      // ignore auth header issues in tests / uninitialized store
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

      const refreshToken = useAuthStore.getState ? useAuthStore.getState().refreshToken : null;

      if (!refreshToken) {
        try {
          useAuthStore.getState?.().logout?.();
        } catch {
          // ignore logout failures in tests
        }
        return Promise.reject(error);
      }

      refreshPromise = Promise.race([
        axios.post(`${API_BASE_URL}/auth/refresh?token=${encodeURIComponent(refreshToken)}`).then(
          (response) => response.data.access_token
        ),
        new Promise<never>((_, reject) =>
          setTimeout(() => reject(new Error('Refresh token timeout')), 10000)
        ),
      ]).catch((refreshError) => {
        try {
          useAuthStore.getState?.()?.logout?.();
        } catch {
          // ignore
        }
        throw refreshError;
      });

      try {
        const token = await refreshPromise;

        const currentRefreshToken = useAuthStore.getState ? useAuthStore.getState().refreshToken : null;
        useAuthStore.setState({
          token,
          refreshToken: currentRefreshToken,
        });

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

    if (error.response?.status === 422) {
      const detail = (error.response.data as { detail?: unknown })?.detail;
      let message = "Validation error";
      if (Array.isArray(detail) && detail.length > 0) {
        const first = detail[0] as { msg?: unknown };
        if (typeof first?.msg === 'string' && first.msg.length > 0) message = first.msg;
      } else if (typeof detail === 'string' && detail.length > 0) {
        message = detail;
      }
      return Promise.reject(new Error(message));
    }

    return Promise.reject(error);
  }
);