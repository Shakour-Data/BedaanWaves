import { create } from "zustand";
import { persist } from "zustand/middleware";
import { apiClient } from '../lib/api';

type Role = "user" | "admin";

export interface UserProfile {
  id: string;
  username: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
}

interface AuthState {
  user: UserProfile | null;
  isAuthenticated: boolean;
  token: string | null;
  refreshToken: string | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, email: string, password: string, full_name: string) => Promise<void>;
  logout: () => void;
}

async function fetchUserProfile(): Promise<UserProfile | null> {
  try {
    const response = await apiClient.get<UserProfile>('users/me');
    return response.data;
  } catch {
    return null;
  }
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      token: null,
      refreshToken: null,
      loading: false,
      login: async (username, password) => {
        set({ loading: true });
        try {
          const response = await apiClient.post('auth/login', { username, password });
          const token = response.data.access_token;
          const refreshToken = response.data.refresh_token;
          set({
            token,
            refreshToken,
            isAuthenticated: true,
          });
          const profile = await fetchUserProfile();
          if (profile) {
            set({ user: profile });
          }
        } catch (error) {
          throw error;
        } finally {
          set({ loading: false });
        }
      },
      register: async (username, email, password, full_name) => {
        set({ loading: true });
        try {
          const response = await apiClient.post('auth/register', { username, email, password, full_name });
          const token = response.data.access_token;
          const refreshToken = response.data.refresh_token;
          set({
            token,
            refreshToken,
            isAuthenticated: true,
          });
          const profile = await fetchUserProfile();
          if (profile) {
            set({ user: profile });
          }
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
          localStorage.removeItem('auth-storage');
          window.location.href = '/login';
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
        token: state.token,
        refreshToken: state.refreshToken,
      }),
    }
  )
);