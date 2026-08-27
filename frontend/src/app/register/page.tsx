"use client";

import { useState } from "react";
import Link from "next/link";
import { TarotCard } from "@/components/ui/TarotCard";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { Input } from "@/components/ui/input";
import { useAuthStore } from "@/store/useAuthStore";
import { t } from "@/lib/i18n";

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
      await registerStore(name, email, password);
    } catch (err: any) {
      const message = err.response?.data?.detail || t("auth.error_authentication");
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center p-3 bg-neutral/30">
      <TarotCard icon="" title={t("signup.title")} className="w-full max-w-md shadow-lg border-border/40">
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          {error ? (
            <div className="rounded-xl bg-error/10 px-4 py-3 text-sm text-error border border-error/20 animate-in fade-in slide-in-from-top-2">
              {error}
            </div>
          ) : null}

          <div className="space-y-3">
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

            <div className="flex flex-col gap-1">
              <span className="text-sm font-semibold text-foreground px-1">{t("signup.email")}</span>
              <Input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder={t("signup.email_placeholder") || t("signup.email")}
                disabled={loading}
                className="ps-10"
              />
            </div>

            <div className="flex flex-col gap-1">
              <span className="text-sm font-semibold text-foreground px-1">{t("signup.password")}</span>
              <div className="relative">
                <Input
                  type={showPassword ? "text" : "password"}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder={t("signup.password_placeholder") || t("signup.password")}
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

            <div className="flex flex-col gap-1">
              <span className="text-sm font-semibold text-foreground px-1">{t("signup.confirm_password")}</span>
              <Input
                type={showPassword ? "text" : "password"}
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder={t("signup.confirm_password_placeholder") || t("signup.confirm_password")}
                disabled={loading}
                className="ps-10"
              />
            </div>
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
            ) : t("signup.submit_button")}
          </PrimaryButton>

          <p className="text-center text-sm text-muted-foreground mt-2">
            {t("signup.already_have_account")}{" "}
            <Link href="/login" className="text-primary hover:underline font-bold">
              {t("signup.login_link")}
            </Link>
          </p>
        </form>
      </TarotCard>
    </main>
  );
}
