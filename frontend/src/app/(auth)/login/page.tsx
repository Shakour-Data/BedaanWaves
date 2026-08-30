"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { InputField } from "@/components/ui/InputField";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { useAuthStore } from "@/store/useAuthStore";
import { useUXStore } from "@/store/useUXStore";
import { t } from "@/lib/i18n";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [usernameValid, setUsernameValid] = useState<"idle" | "valid" | "invalid">("idle");
  const [passwordValid, setPasswordValid] = useState<"idle" | "valid" | "invalid">("idle");
  const loginStore = useAuthStore((s) => s.login);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const router = useRouter();
  const addToast = useUXStore((state) => state.addToast);

  useEffect(() => {
    if (isAuthenticated) {
      router.push("/dashboard");
    }
  }, [isAuthenticated, router]);

  const validateUsername = useCallback((value: string) => {
    if (value.length === 0) return "idle";
    if (value.length < 3) return "invalid";
    return "valid";
  }, []);

  const validatePassword = useCallback((value: string) => {
    if (value.length === 0) return "idle";
    if (value.length < 6) return "invalid";
    return "valid";
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const uStatus = validateUsername(username);
    const pStatus = validatePassword(password);
    setUsernameValid(uStatus);
    setPasswordValid(pStatus);

    if (uStatus === "invalid") {
      setError("Username must be at least 3 characters.");
      return;
    }
    if (pStatus === "invalid") {
      setError("Password must be at least 6 characters.");
      return;
    }

    setLoading(true);
    try {
      await loginStore(username, password);
      addToast({ type: "success", message: "Welcome back! Redirecting to dashboard..." });
    } catch (err) {
      const message = err instanceof Error ? err.message : t("auth.error_authentication");
      setError(message);
      addToast({ type: "error", message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center p-4 bg-[var(--color-background)]">
      <div className="w-full max-w-md bg-[var(--color-surface)] shadow-md rounded-lg border border-[var(--color-border)] p-8">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">Welcome Back</h1>
          <p className="text-sm text-[var(--color-text-secondary)] mt-2">Sign in to access your dashboard</p>
        </div>
        
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          {error ? (
            <div className="rounded-xl bg-error/10 px-4 py-3 text-sm text-error border border-error/20 animate-in fade-in slide-in-from-top-2">
              {error}
            </div>
          ) : null}

          <div className="space-y-4">
            <InputField
              id="username"
              type="text"
              label={t("login.username")}
              required
              value={username}
              onChange={(e) => {
                setUsername(e.target.value);
                setUsernameValid(validateUsername(e.target.value));
              }}
              placeholder={t("login.username_placeholder") || t("login.username")}
              disabled={loading}
              validationState={usernameValid}
              validationMessage={usernameValid === "invalid" ? "Username must be at least 3 characters." : undefined}
            />

            <InputField
              id="password"
              type={showPassword ? "text" : "password"}
              label="Password"
              required
              value={password}
              onChange={(e) => {
                setPassword(e.target.value);
                setPasswordValid(validatePassword(e.target.value));
              }}
              placeholder="••••••••"
              disabled={loading}
              validationState={passwordValid}
              validationMessage={passwordValid === "invalid" ? "Password must be at least 6 characters." : undefined}
            />
            
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="text-xs text-[var(--color-primary)] hover:underline mt-1"
            >
              {showPassword ? "Hide password" : "Show password"}
            </button>
          </div>

          <div className="flex items-center justify-between text-xs px-1">
            <label className="flex items-center gap-2 text-[var(--color-text-secondary)] cursor-pointer group">
              <input type="checkbox" className="rounded border-[var(--color-border)] text-[var(--color-primary)] focus:ring-[var(--color-primary)]" />
              <span className="group-hover:text-[var(--color-text-primary)] transition-colors">Remember me</span>
            </label>
            <Link href="/forgot-password" disable-nav="true" className="text-[var(--color-primary)] hover:underline font-medium">
              Forgot password?
            </Link>
          </div>

          <PrimaryButton
            type="submit"
            disabled={loading}
            className="mt-2 w-full justify-center h-11"
            size="lg"
          >
            {loading ? "Signing in..." : "Sign in"}
          </PrimaryButton>

          <p className="text-center text-sm text-[var(--color-text-secondary)] mt-2">
            Don&apos;t have an account?{" "}
            <Link href="/register" className="text-[var(--color-primary)] hover:underline font-bold">
              Sign up
            </Link>
          </p>
        </form>
      </div>
    </main>
  );
}
