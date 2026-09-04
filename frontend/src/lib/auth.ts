/**
 * auth.ts
 * ---------------------------------------------------------------------------
 * Shared authentication type definitions and helpers.
 *
 * Authentication state (login/register/logout) is managed centrally by
 * `useAuthStore` (Zustand) which calls the API client directly. The payload
 * interfaces below are kept here as the single source of truth for the shape
 * of auth requests so that components and stores stay type-consistent.
 */

export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterPayload {
  name: string;
  email: string;
  password: string;
}

export interface AuthUser {
  id: string;
  username: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}
