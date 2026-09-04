"use client";

import { useState, useEffect, useMemo, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { TarotCard } from "@/components/ui/TarotCard";
import { InputField } from "@/components/ui/InputField";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { useAuthStore } from "@/store/useAuthStore";
import {
  verifyResetToken,
  confirmResetPassword,
  isValidPassword,
  passwordsMatch } from "@/lib/password-recovery-api";

type ResetPhase = "verifying" | "enter_password" | "confirming" | "success" | "error";

type PwdValidationState = "idle" | "validating" | "valid" | "invalid";

function ResetPasswordForm() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const token = searchParams?.get("token") ?? "";

  const [phase, setPhase] = useState<ResetPhase>("verifying");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const pwdState: PwdValidationState = useMemo(() => {
    if (!password) return "idle";
    if (password.length < 8) return "invalid";
    if (!confirmPassword) return "valid";
    return password === confirmPassword ? "valid" : "invalid";
  }, [password, confirmPassword]);

  const pwdError: string | null = useMemo(() => {
    if (!password) return null;
    if (password.length < 8) return "Password must be at least 8 characters.";
    if (confirmPassword && password !== confirmPassword) return "Passwords do not match.";
    return null;
  }, [password, confirmPassword]);

  useEffect(() => {
    void (async () => {
      if (!token) {
        setPhase("error");
        setErrorMsg("No recovery token was provided. Please open the link from your email.");
        return;
      }

      const isValid = await verifyResetToken(token);
      if (isValid) {
        setPhase("enter_password");
      } else {
        setPhase("error");
        setErrorMsg(
          "That recovery link has expired or is no longer valid. Please request a new link.",
        );
      }
    })();
  }, [token]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!passwordsMatch(password, confirmPassword) || !isValidPassword(password)) {
      setErrorMsg("Please fix the errors above before continuing.");
      return;
    }
    setErrorMsg(null);
    setPhase("confirming");

    try {
      const result = await confirmResetPassword(token, password);

      if (result.success) {
        setPhase("success");
      } else {
        setPhase("error");
        setErrorMsg(result.message ?? "Unable to reset password. Please try again.");
      }
    } catch {
      setPhase("error");
      setErrorMsg("Network error. Please check your connection and try again.");
    }
  };

  if (phase === "verifying") {
    return (
      <main className="flex min-h-screen items-center justify-center p-4 bg-[var(--color-background)]">
        <div className="w-full max-w-md bg-[var(--color-surface)] shadow-md rounded-lg border border-[var(--color-border)] p-8 text-center">
          <p className="mt-3 text-sm text-[var(--color-text-secondary)]" aria-live="polite">
            Verifying your reset link...
          </p>
        </div>
      </main>
    );
  }

  if (phase === "error") {
    return (
      <main className="flex min-h-screen items-center justify-center p-4 bg-[var(--color-background)]">
        <div className="w-full max-w-md bg-[var(--color-surface)] shadow-md rounded-lg border border-[var(--color-border)] p-8 text-center">
          <h1 className="text-xl font-bold text-[var(--color-error)] mb-2">Error</h1>
          <p className="text-sm text-[var(--color-text-secondary)]">{errorMsg}</p>
          <div className="mt-6 flex justify-center gap-3">
            <Link href="/forgot-password" className="text-sm font-medium text-[var(--color-primary)] hover:underline">
              Request new link
            </Link>
            <span className="text-[var(--color-border)]">|</span>
            <Link href="/login" className="text-sm font-medium text-[var(--color-primary)] hover:underline">
              Back to Sign in
            </Link>
          </div>
        </div>
      </main>
    );
  }

  if (phase === "success") {
    return (
      <main className="flex min-h-screen items-center justify-center p-4 bg-[var(--color-background)]">
        <div className="w-full max-w-md bg-[var(--color-surface)] shadow-md rounded-lg border border-[var(--color-border)] p-8 text-center">
          <h1 className="text-xl font-bold text-[var(--color-success)] mb-2">Success!</h1>
          <p className="text-sm text-[var(--color-text-secondary)]">Your password has been reset successfully. You can now log in with your new password.</p>
          <div className="mt-6">
            <Link href="/login" className="inline-block rounded-md bg-[var(--color-primary)] px-6 py-2.5 text-sm font-medium text-white hover:bg-[var(--color-primary-hover)] transition-colors">
              Sign In
            </Link>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="flex min-h-screen items-center justify-center p-4 bg-[var(--color-background)]">
      <div className="w-full max-w-md bg-[var(--color-surface)] shadow-md rounded-lg border border-[var(--color-border)] p-8">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <InputField
              id="password"
              label="New Password"
              type={showPassword ? "text" : "password"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter new password"
              validationState={pwdState === "invalid" ? "invalid" : "idle"}
              validationMessage={pwdState === "invalid" && pwdError ? pwdError : undefined}
            />
            <p className="mt-1 text-xs text-[var(--color-text-secondary)]">Must be at least 8 characters</p>
          </div>

          <div>
            <InputField
              id="confirmPassword"
              label="Confirm Password"
              type={showPassword ? "text" : "password"}
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Confirm new password"
              validationState={pwdState === "invalid" && confirmPassword ? "invalid" : "idle"}
              validationMessage={pwdState === "invalid" && confirmPassword && pwdError ? pwdError : undefined}
            />
          </div>

          <div className="flex items-center">
            <input
              id="showPassword"
              type="checkbox"
              checked={showPassword}
              onChange={(e) => setShowPassword(e.target.checked)}
              className="h-4 w-4 rounded border-[var(--color-border)] text-[var(--color-primary)] focus:ring-[var(--color-primary)]"
            />
            <label htmlFor="showPassword" className="ml-2 text-sm text-[var(--color-text-secondary)]">Show password</label>
          </div>

          {errorMsg && (
            <ErrorMessage className="mt-4" message={errorMsg} />
          )}

          <button
            type="submit"
            disabled={phase === "confirming"}
            className="w-full rounded-md bg-[var(--color-primary)] px-4 py-2 text-sm font-medium text-white hover:bg-[var(--color-primary-hover)] disabled:opacity-50"
          >
            {phase === "confirming" ? "Processing..." : "Reset Password"}
          </button>
        </form>

        <div className="mt-6 text-center">
          <Link href="/login" className="text-sm text-[var(--color-primary)] hover:underline">
            Back to Sign in
          </Link>
        </div>
      </div>
    </main>
  );
}

// Main export with Suspense boundary
export default function ResetPasswordPage() {
  return (
    <Suspense fallback={
      <main className="flex min-h-screen items-center justify-center p-3">
        <div className="w-full max-w-md rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
          <p className="text-center text-[var(--color-text-secondary)]">Loading...</p>
        </div>
      </main>
    }>
      <ResetPasswordForm />
    </Suspense>
  );
}
