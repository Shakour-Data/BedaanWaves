import { create } from "zustand";
import { persist } from "zustand/middleware";
import { apiClient } from '../lib/api';

type Role = "user" | "admin";

interface AuthState {
  user: { name: string; email: string; role: Role } | null;
  isAuthenticated: boolean;
  token: string | null;
  refreshToken: string | null;
  loading: boolean;
  currentLang: "en" | "fa";
  setLanguage: (lang: "en" | "fa") => void;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
}

const getInitialLang = () => {
  if (typeof window === 'undefined') return 'en';
  const saved = localStorage.getItem('lang');
  return (saved === 'fa' || saved === 'en') ? saved : 'en';
};

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      token: null,
      refreshToken: null,
      loading: false,
      currentLang: getInitialLang(),
      setLanguage: (lang) => set({ currentLang: lang }),
      login: async (email, password) => {
        set({ loading: true });
        try {
          const currentLang = localStorage.getItem('lang') as "en" | "fa" || 'en';
          const response = await apiClient.post(`/auth/login?lang=${currentLang}`, { email, password });
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
          const currentLang = localStorage.getItem('lang') as "en" | "fa" || 'en';
          const response = await apiClient.post(`/auth/register?lang=${currentLang}`, { name, email, password });
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
        if (typeof window !== 'undefined') {
          localStorage.removeItem('token');
          window.location.href = '/login';
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        ...state,
        currentLang: state.currentLang,
      }),
    }
  )
);