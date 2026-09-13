"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useSearchParams } from "next/navigation";
import { apiClient } from "@/lib/api";
import { getApiErrorMessage } from "@/lib/api";
import { InputField } from "@/components/ui/InputField";
import { PrimaryButton } from "@/components/ui/PrimaryButton";

function ResetPasswordForm({ token }: { token: string }) {
  const router = useRouter();
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (newPassword !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }
    if (newPassword.length < 8) {
      setError("Password must be at least 8 characters long");
      return;
    }
    setLoading(true);
    try {
      await apiClient.post("/auth/password-reset/confirm", {
        token,
        new_password: newPassword,
      });
      setSuccess(true);
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="text-center">
        <div className="mb-4 inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-[var(--color-success-soft)]">
          <span className="text-3xl font-bold text-[var(--color-success)]">&checkmark;</span>
        </div>
        <h2 className="text-xl font-bold text-[var(--color-text-primary)] mb-2">
          Password reset complete
        </h2>
        <p className="text-[var(--color-text-secondary)] mb-6">
          Your password has been updated. You can now sign in.
        </p>
        <PrimaryButton className="w-full" onClick={() => router.push("/login")}>
          Go to Sign In
        </PrimaryButton>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <InputField
        label="New Password"
        name="new_password"
        type="password"
        placeholder="Create a new password"
        value={newPassword}
        onChange={(e) => setNewPassword(e.target.value)}
        required
      />
      <InputField
        label="Confirm Password"
        name="confirm_password"
        type="password"
        placeholder="Confirm your new password"
        value={confirmPassword}
        onChange={(e) => setConfirmPassword(e.target.value)}
        required
      />
      {error && (
        <p className="text-sm text-[var(--color-error)]">{error}</p>
      )}
      <PrimaryButton type="submit" className="w-full" disabled={loading}>
        {loading ? "Resetting..." : "Reset Password"}
      </PrimaryButton>
    </form>
  );
}

function ResetPasswordDisabled() {
  const router = useRouter();
  return (
    <div className="text-center">
      <div className="mb-4 inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-[var(--color-error-soft)]">
        <span className="text-3xl font-bold text-[var(--color-error)]">&times;</span>
      </div>
      <h2 className="text-xl font-bold text-[var(--color-text-primary)] mb-2">
        Invalid or expired link
      </h2>
      <p className="text-[var(--color-text-secondary)] mb-6">
        This recovery link has expired or is no longer valid. Please request a new link.
      </p>
      <PrimaryButton className="w-full" onClick={() => router.push("/forgot-password")}>
        Request New Link
      </PrimaryButton>
    </div>
  );
}

export default function ResetPasswordPage() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");

  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--color-background)] p-4">
      <div className="w-full max-w-md">
        <div className="mb-6 inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-[var(--color-primary-soft)]">
          <span className="text-3xl font-bold text-[var(--color-primary)]">B</span>
        </div>
        <h1 className="text-2xl font-bold text-[var(--color-text-primary)] mb-2">
          Reset Password
        </h1>
        <p className="text-[var(--color-text-secondary)] mb-6">
          Enter your new password below.
        </p>
        {token ? <ResetPasswordForm token={token} /> : <ResetPasswordDisabled />}
      </div>
    </div>
  );
}