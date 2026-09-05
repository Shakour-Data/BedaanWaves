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
    <div className="w-full">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-[var(--color-text-primary)] text-balance">
          Create your account
        </h1>
        <p className="mt-2 text-sm text-[var(--color-text-secondary)]">
          Start your journey with BedaanWaves today
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        {error ? (
          <div className="rounded-xl bg-[var(--color-error-light)] px-4 py-3 text-sm text-[var(--color-error)] border border-[var(--color-error)]/20 animate-in fade-in slide-in-from-top-2">
            {error}
          </div>
        ) : null}

        <div className="space-y-4">
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

          <div className="relative">
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
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-9 text-[10px] font-bold text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)] transition-colors tracking-wide"
              aria-label={showPassword ? "Hide password" : "Show password"}
            >
              {showPassword ? "HIDE" : "SHOW"}
            </button>
          </div>

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
        </div>

        <PrimaryButton
          type="submit"
          disabled={loading}
          className="w-full justify-center h-11 gap-2"
          size="lg"
        >
          {loading ? "Creating account..." : "Sign Up"}
          {!loading && "+"}
        </PrimaryButton>

        <p className="text-center text-sm text-[var(--color-text-secondary)] pt-2">
          Already have an account?{" "}
          <Link href="/login" className="text-[var(--color-primary)] hover:underline font-semibold">
            Sign in
          </Link>
        </p>
      </form>
    </div>
  );
}
