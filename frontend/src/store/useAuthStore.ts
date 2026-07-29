import { create } from "zustand";
import { apiClient } from '../lib/api';

type Role = "user" | "admin";

interface AuthState {
  user: { name: string; email: string; role: Role } | null;
  isAuthenticated: boolean;
  token: string | null;
  refreshToken: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  token: null,
  refreshToken: null,
  loading: false,
  login: async (email, password) => {
    set({ loading: true });
    try {
      const response = await apiClient.post('/auth/login', { email, password });
      const { user, token, refreshToken } = response.data;
      set({
        user,
        isAuthenticated: true,
        token,
        refreshToken,
      });
    } catch (error) {
      throw error;
    } finally {
      set({ loading: false });
    }
  },
  register: async (name, email, password) => {
    set({ loading: true });
    try {
      const response = await apiClient.post('/auth/register', { name, email, password });
      const { user, token, refreshToken } = response.data;
      set({
        user,
        isAuthenticated: true,
        token,
        refreshToken,
      });
    } catch (error) {
      throw error;
    } finally {
      set({ loading: false });
    }
  },
  logout: () => {
    set({
      user: null,
      isAuthenticated: false,
      token: null,
      refreshToken: null,
    });
    window.location.href = '/login';
  },
}));