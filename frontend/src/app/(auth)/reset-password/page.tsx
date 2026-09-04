"use client";

import { useState, useEffect, useMemo, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { InputField } from "@/components/ui/InputField";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { Eye, EyeOff, ArrowRight, CheckCircle2, Lock } from "lucide-react";
import {
  verifyResetToken,
  confirmResetPassword,
  isValidPassword,
  passwordsMatch } from "@/lib/password-recovery-api";

type ResetPhase = "verifying" | "enter_password" | "confirming" | "success" | "error";

type PwdValidationState = "idle" | "validating" | "valid" | "invalid";

function ResetPasswordForm() {
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
      <div className="w-full">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-[var(--color-text-primary)] text-balance">
            Verifying your link
          </h1>
          <p className="mt-2 text-sm text-[var(--color-text-secondary)]">
            Please wait while we verify your reset link...
          </p>
        </div>
        <div className="flex items-center justify-center py-8">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-[var(--color-primary)] border-t-transparent" />
        </div>
      </div>
    );
  }

  if (phase === "error") {
    return (
      <div className="w-full">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 inline-flex h-12 w-12 items-center justify-center rounded-full bg-[var(--color-error-light)]">
            <Lock className="h-6 w-6 text-[var(--color-error)]" />
          </div>
          <h1 className="text-2xl font-bold text-[var(--color-error)]">Error</h1>
          <p className="text-sm text-[var(--color-text-secondary)] mt-2">{errorMsg}</p>
        </div>
        <div className="flex justify-center gap-3">
          <Link href="/forgot-password" className="text-sm font-medium text-[var(--color-primary)] hover:underline">
            Request new link
          </Link>
          <span className="text-[var(--color-border)]">|</span>
          <Link href="/login" className="text-sm font-medium text-[var(--color-primary)] hover:underline">
            Back to Sign in
          </Link>
        </div>
      </div>
    );
  }

  if (phase === "success") {
    return (
      <div className="w-full text-center">
        <div className="mb-8">
          <div className="mx-auto mb-4 inline-flex h-12 w-12 items-center justify-center rounded-full bg-[var(--color-success-light)]">
            <CheckCircle2 className="h-6 w-6 text-[var(--color-success)]" />
          </div>
          <h1 className="text-2xl font-bold text-[var(--color-success)]">Success!</h1>
          <p className="text-sm text-[var(--color-text-secondary)] mt-2">Your password has been reset successfully. You can now log in with your new password.</p>
        </div>
        <Link href="/login" className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-primary-hover)] px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-[var(--color-primary)]/25 transition-all hover:shadow-xl hover:-translate-y-0.5">
          Sign In
          <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    );
  }

  return (
    <div className="w-full">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-[var(--color-text-primary)] text-balance">
          Set new password
        </h1>
        <p className="mt-2 text-sm text-[var(--color-text-secondary)]">
          Create a strong password for your account
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        {errorMsg && (
          <ErrorMessage className="mt-4" message={errorMsg} />
        )}

        <div className="space-y-4">
          <div className="relative">
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
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-9 text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)] transition-colors"
              aria-label={showPassword ? "Hide password" : "Show password"}
            >
              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>

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

        <PrimaryButton
          type="submit"
          disabled={phase === "confirming"}
          className="w-full justify-center h-11 gap-2"
          size="lg"
        >
          {phase === "confirming" ? "Processing..." : "Reset Password"}
          {phase !== "confirming" && <ArrowRight className="h-4 w-4" />}
        </PrimaryButton>

        <p className="text-center text-sm text-[var(--color-text-secondary)] pt-2">
          <Link href="/login" className="text-[var(--color-primary)] hover:underline font-semibold">
            Back to Sign in
          </Link>
        </p>
      </form>
    </div>
  );
}

// Main export with Suspense boundary
export default function ResetPasswordPage() {
  return (
    <Suspense fallback={
      <div className="w-full">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">Loading...</h1>
        </div>
        <div className="flex items-center justify-center py-8">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-[var(--color-primary)] border-t-transparent" />
        </div>
      </div>
    }>
      <ResetPasswordForm />
    </Suspense>
  );
}
