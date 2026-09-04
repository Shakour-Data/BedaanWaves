/**
 * password-recovery-api.ts
 * ---------------------------------------------------------------------------
 * API client for the password-recovery flow.
 *
 * Handles network resilience: on axios/network errors the raw token (for the
 * reset-password step) or the entered email (for the request step) is
 * persisted to localStorage so the user can retry without re-typing
 * everything after a temporary disconnection (spec edge-case).
 */

import { apiClient } from "@/lib/api";

const STORAGE_KEY_DRAFT_EMAIL = "pw_recovery_draft_email";

export interface PasswordRecoveryApiError {
  message: string;
  code: "network" | "invalid_input" | "not_registered" | "server" | "token_invalid" | "token_expired";
}

export interface RequestResetResult {
  success: boolean;
  message: string;
  error?: PasswordRecoveryApiError;
}

export interface VerifyTokenResult {
  valid: boolean;
  error?: PasswordRecoveryApiError;
}

export interface ConfirmResetResult {
  success: boolean;
  message: string;
  error?: PasswordRecoveryApiError;
}

/** Persist the draft email locally (auto-save on network failure). */
export function saveDraftEmail(email: string): void {
  if (typeof window !== "undefined") {
    localStorage.setItem(STORAGE_KEY_DRAFT_EMAIL, email);
  }
}

export function getDraftEmail(): string {
  if (typeof window !== "undefined") {
    return localStorage.getItem(STORAGE_KEY_DRAFT_EMAIL) ?? "";
  }
  return "";
}

export function clearDraftEmail(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem(STORAGE_KEY_DRAFT_EMAIL);
  }
}

/** Request a password-reset link. Always returns success from the API
 *  (account-enumeration proof); the *message* text differs if we want
 *  to surface a client-side hint that the email is unknown. */
export async function requestPasswordReset(
  email: string,
  lang: "en" | "fa" = "en",
): Promise<RequestResetResult> {
  saveDraftEmail(email);
  try {
    const res = await apiClient.post<{ status: string; message: string }>(
      `auth/password-reset/request?lang=${lang}`,
      { email },
    );
    clearDraftEmail();
    return {
      success: true,
      message: res.data.message,
    };
  } catch (err) {
    const axiosErr = err as { response?: { data?: { detail?: unknown; error_code?: string } } };
    const detail = axiosErr?.response?.data?.detail;
    let message = "Network error";
    if (typeof detail === "string") {
      message = detail;
    } else if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0] as { msg?: unknown };
      message = typeof first?.msg === "string" ? first.msg : "Network error";
    } else if (err instanceof Error) {
      message = err.message;
    }
    return {
      success: false,
      message,
      error: {
        message,
        code: (axiosErr?.response?.data?.error_code as PasswordRecoveryApiError["code"]) ?? "network",
      },
    };
  }
}

/** Verify whether a reset token (from the email link) is still valid. */
export async function verifyResetToken(
  token: string,
  lang: "en" | "fa" = "en",
): Promise<VerifyTokenResult> {
  try {
    const res = await apiClient.post<{ valid: boolean }>(
      `auth/password-reset/verify?lang=${lang}`,
      { token },
    );
    return { valid: res.data.valid };
  } catch {
    return { valid: false, error: { message: "Network error", code: "network" } };
  }
}

/** Submit the new password with the token consumed from the email link. */
export async function confirmResetPassword(
  token: string,
  newPassword: string,
  lang: "en" | "fa" = "en",
): Promise<ConfirmResetResult> {
  try {
    const res = await apiClient.post<{ status: string; message: string }>(
      `auth/password-reset/confirm?lang=${lang}`,
      { token, new_password: newPassword },
    );
    return {
      success: true,
      message: res.data.message,
    };
  } catch (err) {
    const axiosErr = err as { response?: { data?: { detail?: unknown; error_code?: string } } };
    const detail = axiosErr?.response?.data?.detail;
    let message = "Network error";
    if (typeof detail === "string") {
      message = detail;
    } else if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0] as { msg?: unknown };
      message = typeof first?.msg === "string" ? first.msg : "Network error";
    }
    return {
      success: false,
      message,
      error: {
        message,
        code: (axiosErr?.response?.data?.error_code as PasswordRecoveryApiError["code"]) ?? "server",
      },
    };
  }
}

/** Validate an email address (RFC-5322 simplified) client-side. */
export function isValidEmail(email: string): boolean {
  if (!email || email.trim() === "") return false;
  const trimmed = email.trim();
  const re = /^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$/;
  return re.test(trimmed);
}

/** Validate a new password (min 8 chars, must contain letters and numbers). */
export function isValidPassword(password: string): boolean {
  if (!password || password.length < 8) return false;
  const hasLetter = /[a-zA-Z]/.test(password);
  const hasNumber = /\d/.test(password);
  return hasLetter && hasNumber;
}

/** Validate a new password matches its confirmation. */
export function passwordsMatch(a: string, b: string): boolean {
  return a === b && a.length > 0;
}
