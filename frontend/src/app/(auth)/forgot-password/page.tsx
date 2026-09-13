"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiClient } from "@/lib/api";
import { getApiErrorMessage } from "@/lib/api";
import { InputField } from "@/components/ui/InputField";
import { PrimaryButton } from "@/components/ui/PrimaryButton";

export default function ForgotPasswordPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await apiClient.post("/auth/password-reset/request", { email });
      setSent(true);
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  if (sent) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[var(--color-background)] p-4">
        <div className="w-full max-w-md text-center">
          <div className="mb-6 inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-[var(--color-success-soft)]">
            <span className="text-3xl font-bold text-[var(--color-success)]">✓</span>
          </div>
          <h1 className="text-2xl font-bold text-[var(--color-text-primary)] mb-2">
            Check your email
          </h1>
          <p className="text-[var(--color-text-secondary)] mb-6">
            If an account exists for that email, a recovery link has been sent.
          </p>
          <button onClick={() => router.push("/login")} className="text-[var(--color-primary)] hover:underline">
            Back to Sign In
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--color-background)] p-4">
      <div className="w-full max-w-md">
        <div className="mb-6 inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-[var(--color-primary-soft)]">
          <span className="text-3xl font-bold text-[var(--color-primary)]">🔑</span>
        </div>
        <h1 className="text-2xl font-bold text-[var(--color-text-primary)] mb-2">
          Reset Password
        </h1>
        <p className="text-[var(--color-text-secondary)] mb-6">
          Enter your email and we&#39;ll send you a recovery link.
        </p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <InputField
            label="Email"
            name="email"
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          {error && (
            <p className="text-sm text-[var(--color-error)]">{error}</p>
          )}
          <PrimaryButton type="submit" className="w-full" disabled={loading}>
            {loading ? "Sending..." : "Send Recovery Link"}
          </PrimaryButton>
        </form>
        <p className="mt-4 text-center text-sm text-[var(--color-text-secondary)]">
          <button onClick={() => router.push("/login")} className="text-[var(--color-primary)] hover:underline">
            Back to Sign In
          </button>
        </p>
      </div>
    </div>
  );
}