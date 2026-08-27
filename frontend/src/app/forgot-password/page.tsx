"use client";

import { useState } from "react";
import Link from "next/link";
import { InputField } from "@/components/ui/InputField";
import { useAuthStore } from "@/store/useAuthStore";
import { t } from "@/lib/i18n";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);
  

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    await new Promise((r) => setTimeout(r, 600));
    setSent(true);
    setLoading(false);
  };

  return (
    <main className="flex min-h-screen items-center justify-center p-4 bg-[var(--color-background)]">
      <div className="w-full max-w-md bg-[var(--color-surface)] shadow-md rounded-lg border border-[var(--color-border)] p-8">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">Reset Password</h1>
          <p className="text-sm text-[var(--color-text-secondary)] mt-2">Enter your email to receive a reset link</p>
        </div>
        
        {sent ? (
          <div className="bg-[var(--color-success)]/10 border border-[var(--color-success)] text-[var(--color-success)] px-4 py-3 rounded-md text-center">
            <p className="font-medium">Reset link sent!</p>
            <p className="text-sm mt-1">If the email is valid, you will receive a reset link shortly.</p>
            <Link href="/login" className="block mt-4 text-[var(--color-primary)] hover:underline font-bold text-sm">
              Back to Sign in
            </Link>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <div className="space-y-4">
              <InputField
                id="email"
                type="email"
                label="Email Address"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="example@email.com"
                disabled={loading}
              />
            </div>

            <button 
              type="submit" 
              disabled={loading} 
              className="h-10 px-4 mt-2 w-full bg-[var(--color-primary)] text-white font-medium rounded-md hover:bg-[var(--color-primary-hover)] transition-colors duration-150 ease-out focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)] focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? "Processing..." : "Send Reset Link"}
            </button>
            <p className="text-center text-sm text-[var(--color-text-secondary)] mt-2">
              <Link href="/login" className="text-[var(--color-primary)] hover:underline font-bold">
                Back to Sign in
              </Link>
            </p>
          </form>
        )}
      </div>
    </main>
  );
}

