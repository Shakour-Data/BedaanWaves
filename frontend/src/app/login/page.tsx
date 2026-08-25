"use client";

import { useState } from "react";
import Link from "next/link";
import { TarotCard } from "@/components/ui/TarotCard";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { Input } from "@/components/ui/input";
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
    <main className="flex min-h-screen items-center justify-center p-3 bg-neutral/30">
      <TarotCard icon="" title={t("login.title")} className="w-full max-w-md shadow-lg border-border/40">
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          {error ? (
            <div className="rounded-xl bg-error/10 px-4 py-3 text-sm text-error border border-error/20 animate-in fade-in slide-in-from-top-2">
              {error}
            </div>
          ) : null}

          <div className="space-y-4">
            <div className="flex flex-col gap-1">
              <span className="text-sm font-semibold text-foreground px-1">{t("login.email")}</span>
              <Input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder={t("login.email_placeholder") || t("login.email")}
                disabled={loading}
                className="ps-10"
              />
            </div>

            <div className="flex flex-col gap-1">
              <span className="text-sm font-semibold text-foreground px-1">{t("login.password")}</span>
              <div className="relative">
                <Input
                  type={showPassword ? "text" : "password"}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  disabled={loading}
                  className="ps-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  aria-label={showPassword ? t("auth.hide_password") : t("auth.show_password")}
                  className="absolute inset-y-0 left-3 flex items-center text-muted-foreground transition hover:text-foreground focus:outline-none"
                >
                  {showPassword ? "" : "️"}
                </button>
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between text-xs px-1">
            <label className="flex items-center gap-2 text-muted-foreground cursor-pointer group">
              <input type="checkbox" className="rounded border-border text-primary focus:ring-primary/20" />
              <span className="group-hover:text-foreground transition-colors">{t("auth.remember_me")}</span>
            </label>
            <Link href="/forgot-password" disable-nav="true" className="text-primary hover:underline font-medium">
              {t("login.forgot_password")}
            </Link>
          </div>

          <div className="flex items-center gap-2 px-1">
            <span className="text-xs text-muted-foreground">{t("auth.language")}:</span>
            <select
              value={currentLang}
              onChange={handleLanguageChange}
              className="border border-border rounded-lg px-2 py-1 text-xs bg-surface focus:outline-none focus:ring-2 focus:ring-primary/20"
            >
              <option value="en">English</option>
              <option value="fa">فارسی</option>
            </select>
          </div>

          <PrimaryButton 
            type="submit" 
            disabled={loading} 
            className="mt-2 w-full justify-center h-11"
            size="lg"
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                {t("auth.loading")}
              </span>
            ) : t("login.submit_button")}
          </PrimaryButton>

          <p className="text-center text-sm text-muted-foreground mt-2">
            {t("login.no_account")}{" "}
            <Link href="/register" className="text-primary hover:underline font-bold">
              {t("signup.login_link")}
            </Link>
          </p>
        </form>
      </TarotCard>
    </main>
  );
}
