import { create } from "zustand";
import { persist } from "zustand/middleware";
import { apiClient } from '../lib/api';

type Role = "user" | "admin";

interface AuthState {
  user: { name: string; email: string; role: Role; created_at?: string; isActive?: boolean } | null;
  isAuthenticated: boolean;
  token: string | null;
  refreshToken: string | null;
  currentLang: "en" | "fa";
  loading: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      token: null,
      refreshToken: null,
      currentLang: "en",
      loading: false,
      isLoading: false,
      login: async (email, password) => {
        set({ loading: true });
        try {
          const response = await apiClient.post(`/auth/login`, { email, password });
          const { user, token, refreshToken } = response.data;
          set({
            user,
            isAuthenticated: true,
            token,
            refreshToken });
        } catch (error) {
          throw error;
        } finally {
          set({ loading: false });
        }
      },
      register: async (name, email, password) => {
        set({ loading: true });
        try {
          const response = await apiClient.post(`/auth/register`, { name, email, password });
          const { user, token, refreshToken } = response.data;
          set({
            user,
            isAuthenticated: true,
            token,
            refreshToken });
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
          refreshToken: null });
        if (typeof window !== 'undefined') {
          localStorage.removeItem('token');
          window.location.href = '/login';
        }
      } }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
        token: state.token,
        refreshToken: state.refreshToken,
        currentLang: state.currentLang }) }
  )
);