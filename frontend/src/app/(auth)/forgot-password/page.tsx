"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowRight, Mail, CheckCircle2 } from "lucide-react";
import { InputField } from "@/components/ui/InputField";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { useUXStore } from "@/store/useUXStore";
import { requestPasswordReset, isValidEmail, type PasswordRecoveryApiError } from "@/lib/password-recovery-api";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const addToast = useUXStore((state) => state.addToast);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    if (!isValidEmail(email)) {
      setError("Please enter a valid email address.");
      setLoading(false);
      return;
    }

    try {
      const result = await requestPasswordReset(email);
      if (result.success) {
        setSent(true);
        addToast({ type: "success", message: result.message });
      } else {
        const apiError = result.error as PasswordRecoveryApiError | undefined;
        setError(apiError?.message ?? result.message ?? "Failed to send reset link. Please try again.");
        addToast({ type: "error", message: apiError?.message ?? result.message ?? "Failed to send reset link." });
      }
    } catch {
      setError("Network error. Please check your connection and try again.");
      addToast({ type: "error", message: "Network error. Please try again." });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-[var(--color-text-primary)] text-balance">
          Reset your password
        </h1>
        <p className="mt-2 text-sm text-[var(--color-text-secondary)]">
          Enter your email and we&apos;ll send you a reset link
        </p>
      </div>

      {sent ? (
        <div className="rounded-2xl border border-[var(--color-success)]/30 bg-[var(--color-success-light)] p-6 text-center animate-in fade-in zoom-in-95">
          <div className="mx-auto mb-4 inline-flex h-12 w-12 items-center justify-center rounded-full bg-[var(--color-success)]/10">
            <CheckCircle2 className="h-6 w-6 text-[var(--color-success)]" />
          </div>
          <p className="font-semibold text-[var(--color-text-primary)]">Reset link sent!</p>
          <p className="text-sm mt-1 text-[var(--color-text-secondary)]">
            If the email is valid, you will receive a reset link shortly.
          </p>
          <Link href="/login" className="inline-flex items-center gap-2 mt-6 text-sm font-semibold text-[var(--color-primary)] hover:underline">
            Back to Sign in
            <ArrowRight className="h-3 w-3" />
          </Link>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-5">
          {error && (
            <div className="rounded-xl bg-[var(--color-error-light)] px-4 py-3 text-sm text-[var(--color-error)] border border-[var(--color-error)]/20 animate-in fade-in slide-in-from-top-2">
              {error}
            </div>
          )}

          <div className="relative">
            <InputField
              id="email"
              type="email"
              label="Email Address"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="example@email.com"
              disabled={loading}
              validationState={email ? (isValidEmail(email) ? "valid" : "invalid") : "idle"}
              validationMessage={email && !isValidEmail(email) ? "Please enter a valid email address." : undefined}
            />
          </div>

          <PrimaryButton
            type="submit"
            disabled={loading}
            className="w-full justify-center h-11 gap-2"
            size="lg"
          >
            {loading ? "Processing..." : "Send Reset Link"}
            {!loading && <Mail className="h-4 w-4" />}
          </PrimaryButton>

          <p className="text-center text-sm text-[var(--color-text-secondary)] pt-2">
            <Link href="/login" className="text-[var(--color-primary)] hover:underline font-semibold">
              Back to Sign in
            </Link>
          </p>
        </form>
      )}
    </div>
  );
}
