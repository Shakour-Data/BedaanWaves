"use client";

import { useState, useCallback } from "react";
import Link from "next/link";
import { InputField } from "@/components/ui/InputField";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { useAuthStore } from "@/store/useAuthStore";
import { useUXStore } from "@/store/useUXStore";
import { t } from "@/lib/i18n";
import { getApiErrorMessage } from "@/lib/api";

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
  const addToast = useUXStore((state) => state.addToast);

  const validateUsername = useCallback((v: string) => v.trim().length >= 3 ? "valid" : "invalid", []);
  const validateEmail = useCallback((v: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v) ? "valid" : "invalid", []);
  const validatePassword = useCallback((v: string) => v.length >= 8 ? "valid" : "invalid", []);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);

    const uStatus = validateUsername(username);
    const eStatus = validateEmail(email);
    const pStatus = validatePassword(password);
    
    if (uStatus === "invalid") { setError("Username must be at least 3 characters."); return; }
    if (eStatus === "invalid") { setError("Please enter a valid email address."); return; }
    if (pStatus === "invalid") { setError("Password must be at least 8 characters."); return; }
    if (password !== confirmPassword) { setError("Passwords do not match."); return; }

    setLoading(true);
    try {
      await registerStore(username, email, password, name);
      addToast({ type: "success", message: "Account created successfully! Welcome aboard." });
    } catch (err) {
      const message = getApiErrorMessage(err);
      setError(message);
      addToast({ type: "error", message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center p-4 bg-[var(--color-background)]">
      <div className="w-full max-w-md bg-[var(--color-surface)] shadow-md rounded-lg border border-[var(--color-border)] p-8">
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          {error ? (
            <div className="rounded-xl bg-error/10 px-4 py-3 text-sm text-error border border-error/20 animate-in fade-in slide-in-from-top-2">
              {error}
            </div>
          ) : null}

          <div className="space-y-3">
            <InputField
              id="username"
              type="text"
              label={t("signup.username")}
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder={t("signup.username_placeholder") || t("signup.username")}
              disabled={loading}
              validationState={username ? validateUsername(username) : "idle"}
              validationMessage={username && validateUsername(username) === "invalid" ? "Username must be at least 3 characters." : undefined}
            />

            <InputField
              id="name"
              type="text"
              label={t("signup.name")}
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder={t("signup.name_placeholder") || t("signup.name")}
              disabled={loading}
            />

            <InputField
              id="email"
              type="email"
              label="Email Address"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="example@email.com"
              disabled={loading}
              validationState={email ? validateEmail(email) : "idle"}
              validationMessage={email && validateEmail(email) === "invalid" ? "Please enter a valid email address." : undefined}
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
              validationState={password ? validatePassword(password) : "idle"}
              validationMessage={password && validatePassword(password) === "invalid" ? "Password must be at least 8 characters." : undefined}
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
              validationState={confirmPassword && password !== confirmPassword ? "invalid" : confirmPassword ? "valid" : "idle"}
              validationMessage={confirmPassword && password !== confirmPassword ? "Passwords do not match." : undefined}
            />
            
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="text-xs text-[var(--color-primary)] hover:underline mt-1 block"
            >
              {showPassword ? "Hide password" : "Show password"}
            </button>
          </div>

          <PrimaryButton
            type="submit"
            disabled={loading}
            className="mt-2 w-full justify-center h-11"
            size="lg"
          >
            {loading ? "Creating account..." : "Sign Up"}
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