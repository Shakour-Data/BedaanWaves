"use client";

import { useState } from "react";
import Link from "next/link";
import { TarotCard } from "@/components/ui/TarotCard";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { useAuthStore } from "@/store/useAuthStore";
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
      return key;
    }
  }
  return typeof value === "string" ? value : key;
};

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const loginStore = useAuthStore((s) => s.login);
  const setLanguage = useAuthStore((s) => s.setLanguage);
  const currentLang = useAuthStore((s) => s.currentLang);

  const handleLanguageChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const lang = e.target.value as "en" | "fa";
    setLanguage(lang);
    if (typeof window !== "undefined") {
      localStorage.setItem("lang", lang);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await loginStore(email, password);
    } catch (err: any) {
      const message = err.response?.data?.detail || t("auth.error_authentication");
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center p-3">
      <TarotCard icon="" title={t("login.title")} className="w-full max-w-md">
        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          {error ? (
            <p className="rounded-xl bg-primary/10 px-3 py-2 text-sm text-primary">{error}</p>
          ) : null}

          <label className="flex flex-col gap-1">
            <span className="text-sm text-muted-foreground">{t("login.email")}</span>
            <span className="relative">
              <span className="absolute inset-y-0 right-3 flex items-center text-muted-foreground" aria-hidden="true">
                
              </span>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder={t("login.email_placeholder") || t("login.email")}
                disabled={loading}
                className="w-full rounded-xl border border-border bg-surface px-3 py-2 ps-10 text-sm outline-none transition duration-fast ease-focus:border-secondary focus:ring-2 focus:ring-secondary/20 disabled:opacity-60"
              />
            </span>
          </label>

          <label className="flex flex-col gap-1">
            <span className="text-sm text-muted-foreground">{t("login.password")}</span>
            <span className="relative">
              <span className="absolute inset-y-0 right-3 flex items-center text-muted-foreground" aria-hidden="true">
                ️
              </span>
              <input
                type={showPassword ? "text" : "password"}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                disabled={loading}
                className="w-full rounded-xl border border-border bg-surface px-3 py-2 ps-10 text-sm outline-none transition duration-fast ease-focus:border-secondary focus:ring-2 focus:ring-secondary/20 disabled:opacity-60"
              />
              <button
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                aria-label={showPassword ? t("auth.hide_password") : t("auth.show_password")}
                className="absolute inset-y-0 left-3 flex items-center text-muted-foreground transition hover:text-foreground"
              >
                {showPassword ? "" : "️"}
              </button>
            </span>
          </label>

          <div className="flex items-center justify-between text-xs">
            <label className="flex items-center gap-2 text-muted-foreground">
              <input type="checkbox" className="rounded border-border" />
              {t("auth.remember_me")}
            </label>
            <Link href="/forgot-password" className="text-secondary hover:underline">
              {t("login.forgot_password")}
            </Link>
          </div>

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
            {loading ? t("auth.loading") : t("login.submit_button")}
          </PrimaryButton>

          <p className="text-center text-sm text-muted-foreground">
            {t("login.no_account")}{" "}
            <Link href="/register" className="text-secondary hover:underline">
              {t("signup.login_link")}
            </Link>
          </p>
        </form>
      </TarotCard>
    </main>
  );
}
