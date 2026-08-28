"use client";

import { useState } from "react";
import Link from "next/link";
import { InputField } from "@/components/ui/InputField";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { useAuthStore } from "@/store/useAuthStore";
import { t } from "@/lib/i18n";


export default function RegisterPage() {
  const [username, setUsername] = useState("");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const registerStore = useAuthStore((s) => s.register);
  


  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);
    if (password.length < 8) {
      setError(t("signup.error_password_length"));
      return;
    }
    if (password !== confirmPassword) {
      setError(t("signup.error_password_match"));
      return;
    }
    setLoading(true);
    try {
      await registerStore(username, email, password, name);
    } catch (err: any) {
      const message = err.response?.data?.detail || t("auth.error_authentication");
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center p-4 bg-[var(--color-background)]">
      <div className="w-full max-w-md bg-[var(--color-surface)] shadow-md rounded-lg border border-[var(--color-border)] p-8">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">Create Account</h1>
          <p className="text-sm text-[var(--color-text-secondary)] mt-2">Sign up to get started</p>
        </div>
        
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          {error ? (
            <div className="rounded-xl bg-error/10 px-4 py-3 text-sm text-error border border-error/20 animate-in fade-in slide-in-from-top-2">
              {error}
            </div>
          ) : null}

          <div className="space-y-3">
            <div className="flex flex-col gap-1">
              <span className="text-sm font-semibold text-foreground px-1">{t("signup.username")}</span>
              <Input
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder={t("signup.username_placeholder") || t("signup.username")}
                disabled={loading}
                className="ps-10"
              />
            </div>

            <div className="flex flex-col gap-1">
              <span className="text-sm font-semibold text-foreground px-1">{t("signup.name")}</span>
              <Input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder={t("signup.name_placeholder") || t("signup.name")}
                disabled={loading}
                className="ps-10"
              />
            </div>

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

            <InputField
              id="password"
              type={showPassword ? "text" : "password"}
              label="Password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              disabled={loading}
            />

            <InputField
              id="confirmPassword"
              type={showPassword ? "text" : "password"}
              label="Confirm Password"
              required
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="••••••••"
              disabled={loading}
            />
            
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="text-xs text-[var(--color-primary)] hover:underline mt-1 block"
            >
              {showPassword ? "Hide password" : "Show password"}
            </button>
          </div>

          <div className="flex items-center gap-2 px-1 hidden">
          </div>

          <PrimaryButton
            type="submit"
            disabled={loading}
            className="mt-2 w-full justify-center h-11"
            size="lg"
          >
            {loading ? "Processing..." : "Sign Up"}
          </PrimaryButton>

          <p className="text-center text-sm text-[var(--color-text-secondary)] mt-2">
            Already have an account?{" "}
            <Link href="/login" className="text-[var(--color-primary)] hover:underline font-bold">
              Sign in
            </Link>
          </p>
        </form>
      </div>
    </main>
  );
}
