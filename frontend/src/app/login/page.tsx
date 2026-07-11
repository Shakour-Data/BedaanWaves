"use client";

import { useState } from "react";
import Link from "next/link";
import { TarotCard } from "@/components/ui/TarotCard";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { useAuthStore } from "@/store/useAuthStore";
import { loginApi } from "@/lib/auth";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const login = useAuthStore((s) => s.login);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await loginApi({ email, password });
      await login(email, password);
    } catch {
      setError("ورود ناموفق بود. لطفاً مجدداً تلاش کنید.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center p-3">
      <TarotCard icon="🔐" title="ورود به حساب کاربری" className="w-full max-w-md">
        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          {error ? (
            <p className="rounded-xl bg-primary/10 px-3 py-2 text-sm text-primary">{error}</p>
          ) : null}

          <label className="flex flex-col gap-1">
            <span className="text-sm text-muted-foreground">ایمیل</span>
            <span className="relative">
              <span className="absolute inset-y-0 right-3 flex items-center text-muted-foreground" aria-hidden="true">
                💧
              </span>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                disabled={loading}
                className="w-full rounded-xl border border-border bg-surface px-3 py-2 ps-10 text-sm outline-none transition duration-fast ease-flow focus:border-secondary focus:ring-2 focus:ring-secondary/20 disabled:opacity-60"
              />
            </span>
          </label>

          <label className="flex flex-col gap-1">
            <span className="text-sm text-muted-foreground">رمز عبور</span>
            <span className="relative">
              <span className="absolute inset-y-0 right-3 flex items-center text-muted-foreground" aria-hidden="true">
                👁️
              </span>
              <input
                type={showPassword ? "text" : "password"}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                disabled={loading}
                className="w-full rounded-xl border border-border bg-surface px-3 py-2 ps-10 text-sm outline-none transition duration-fast ease-flow focus:border-secondary focus:ring-2 focus:ring-secondary/20 disabled:opacity-60"
              />
              <button
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                aria-label={showPassword ? "مخفی کردن رمز" : "نمایش رمز"}
                className="absolute inset-y-0 left-3 flex items-center text-muted-foreground transition hover:text-foreground"
              >
                {showPassword ? "🙈" : "👁️"}
              </button>
            </span>
          </label>

          <div className="flex items-center justify-between text-xs">
            <label className="flex items-center gap-2 text-muted-foreground">
              <input type="checkbox" className="rounded border-border" />
              مرا به خاطر بسپار
            </label>
            <Link href="/forgot-password" className="text-secondary hover:underline">
              فراموشی رمز؟
            </Link>
          </div>

          <PrimaryButton type="submit" disabled={loading} className="mt-1 w-full justify-center">
            {loading ? "در حال ورود…" : "ورود"}
          </PrimaryButton>

          <p className="text-center text-sm text-muted-foreground">
            حساب ندارید؟{" "}
            <Link href="/register" className="text-secondary hover:underline">
              ثبت‌نام
            </Link>
          </p>
        </form>
      </TarotCard>
    </main>
  );
}
