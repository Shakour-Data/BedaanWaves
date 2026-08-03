"use client";

import { useState } from "react";
import Link from "next/link";
import { TarotCard } from "@/components/ui/TarotCard";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { useAuthStore } from "@/store/useAuthStore";
import { registerApi } from "@/lib/auth";
import en from "@/i18n/en.json";
import fa from "@/i18n/fa.json";

// Simple translation function
const t = (key: string) => {
  const lang = typeof window !== "undefined" ? localStorage.getItem("lang") || "en" : "en";
  const dict = lang === "fa" ? fa : en;
  const keys = key.split(".");
  let value: any = dict;
  for (const k of keys) {
    if (value && typeof value === "object") {
      value = (value as any)[k];
    } else {
      return key; // fallback to key if not found
    }
  }
  return typeof value === "string" ? value : key;
};

export default function RegisterPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const registerStore = useAuthStore((s) => s.register);
  const setLanguage = useAuthStore((s) => s.setLanguage);
  const currentLang = useAuthStore((s) => s.currentLang);

  const handleLanguageChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const lang = e.target.value as "en" | "fa";
    setLanguage(lang);
    // Also update localStorage for immediate use in t()
    if (typeof window !== "undefined") {
      localStorage.setItem("lang", lang);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
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
      await registerApi({ name, email, password });
      await registerStore(name, email, password);
    } catch (err: any) {
      // Try to get error message from response, fallback to generic
      const message = err.response?.data?.detail || t("auth.error_authentication");
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center p-3">
      <TarotCard icon="🌱" title={t("signup.title")} className="w-full max-w-md">
        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          {error ? (
            <p className="rounded-xl bg-primary/10 px-3 py-2 text-sm text-primary">{error}</p>
          ) : null}

          <label className="flex flex-col gap-1">
            <span className="text-sm text-muted-foreground">{t("signup.name")}</span>
            <span className="relative">
              <span className="absolute inset-y-0 right-3 flex items-center text-muted-foreground" aria-hidden="true">
                🌿
              </span>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder={t("signup.name_placeholder") || t("signup.name")}
                disabled={loading}
                className="w-full rounded-xl border border-border bg-surface px-3 py-2 ps-10 text-sm outline-none transition duration-fast ease-focus:border-secondary focus:ring-2 focus:ring-secondary/20 disabled:opacity-60"
              />
            </span>
          </label>

          <label className="flex flex-col gap-1">
            <span className="text-sm text-muted-foreground">{t("signup.email")}</span>
            <span className="relative">
              <span className="absolute inset-y-0 right-3 flex items-center text-muted-foreground" aria-hidden="true">
                💧
              </span>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder={t("signup.email_placeholder") || t("signup.email")}
                disabled={loading}
                className="w-full rounded-xl border border-border bg-surface px-3 py-2 ps-10 text-sm outline-none transition duration-fast ease-focus:border-secondary focus:ring-2 focus:ring-secondary/20 disabled:opacity-60"
              />
            </span>
          </label>

          <label className="flex flex-col gap-1">
            <span className="text-sm text-muted-foreground">{t("signup.password")}</span>
            <span className="relative">
              <span className="absolute inset-y-0 right-3 flex items-center text-muted-foreground" aria-hidden="true">
                🔒
              </span>
              <input
                type={showPassword ? "text" : "password"}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder={t("signup.password_placeholder") || t("signup.password")}
                disabled={loading}
                className="w-full rounded-xl border border-border bg-surface px-3 py-2 ps-10 text-sm outline-none transition duration-fast ease-focus:border-secondary focus:ring-2 focus:ring-secondary/20 disabled:opacity-60"
              />
              <button
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                aria-label={showPassword ? t("auth.hide_password") : t("auth.show_password")}
                className="absolute inset-y-0 left-3 flex items-center text-muted-foreground transition hover:text-foreground"
              >
                {showPassword ? "🙈" : "👁️"}
              </button>
            </span>
          </label>

          <label className="flex flex-col gap-1">
            <span className="text-sm text-muted-foreground">{t("signup.confirm_password")}</span>
            <span className="relative">
              <span className="absolute inset-y-0 right-3 flex items-center text-muted-foreground" aria-hidden="true">
                🔒
              </span>
              <input
                type={showPassword ? "text" : "password"}
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder={t("signup.confirm_password_placeholder") || t("signup.confirm_password")}
                disabled={loading}
                className="w-full rounded-xl border border-border bg-surface px-3 py-2 ps-10 text-sm outline-none transition duration-fast ease-focus:border-secondary focus:ring-2 focus:ring-secondary/20 disabled:opacity-60"
              />
            </span>
          </label>

          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">{t("auth.language")}:</span>
            <select
              value={currentLang}
              onChange={handleLanguageChange}
              className="border border-border rounded px-2 py-1 text-sm bg-surface"
            >
              <option value="en">English</option>
              <option value="fa">فارسی</option>
            </select>
          </div>

          <PrimaryButton type="submit" disabled={loading} className="mt-1 w-full justify-center">
            {loading ? t("auth.loading") : t("signup.submit_button")}
          </PrimaryButton>

          <p className="text-center text-sm text-muted-foreground">
            {t("signup.already_have_account")}{" "}
            <Link href="/login" className="text-secondary hover:underline">
              {t("signup.login_link")}
            </Link>
          </p>
        </form>
      </TarotCard>
    </main>
  );
}