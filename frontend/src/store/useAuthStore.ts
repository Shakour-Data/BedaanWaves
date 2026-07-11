import { create } from "zustand";

type Role = "user" | "admin";

interface AuthState {
  user: { name: string; email: string; role: Role } | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  login: async (email, _password) => {
    void _password;
    await new Promise((r) => setTimeout(r, 600));
    set({
      user: { name: email.split("@")[0], email, role: "user" },
      isAuthenticated: true,
    });
  },
  register: async (name, email, _password) => {
    void _password;
    await new Promise((r) => setTimeout(r, 600));
    set({
      user: { name, email, role: "user" },
      isAuthenticated: true,
    });
  },
  logout: () => set({ user: null, isAuthenticated: false }),
}));
