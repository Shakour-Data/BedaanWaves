"use client";

import { useState } from "react";
import Link from "next/link";
import { TarotCard } from "@/components/ui/TarotCard";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { useAuthStore } from "@/store/useAuthStore";
import { registerApi } from "@/lib/auth";

export default function RegisterPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const register = useAuthStore((s) => s.register);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (password.length < 8) {
      setError("رمز عبور باید حداقل ۸ کاراکتر باشد.");
      return;
    }
    if (password !== confirmPassword) {
      setError("رمز عبور و تکرار آن مطابقت ندارند.");
      return;
    }
    setLoading(true);
    try {
      await registerApi({ name, email, password });
      await register(name, email, password);
    } catch {
      setError("ثبت‌نام ناموفق بود. لطفاً مجدداً تلاش کنید.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center p-3">
      <TarotCard icon="🌱" title="ثبت‌نام در BedaanWaves" className="w-full max-w-md">
        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          {error ? (
            <p className="rounded-xl bg-primary/10 px-3 py-2 text-sm text-primary">{error}</p>
          ) : null}

          <label className="flex flex-col gap-1">
            <span className="text-sm text-muted-foreground">نام کامل</span>
            <span className="relative">
              <span className="absolute inset-y-0 right-3 flex items-center text-muted-foreground" aria-hidden="true">
                🌿
              </span>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="نام نمایشی شما"
                disabled={loading}
                className="w-full rounded-xl border border-border bg-surface px-3 py-2 ps-10 text-sm outline-none transition duration-fast ease-flow focus:border-secondary focus:ring-2 focus:ring-secondary/20 disabled:opacity-60"
              />
            </span>
          </label>

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
                🔒
              </span>
              <input
                type={showPassword ? "text" : "password"}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="حداقل ۸ کاراکتر"
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

          <label className="flex flex-col gap-1">
            <span className="text-sm text-muted-foreground">تکرار رمز عبور</span>
            <span className="relative">
              <span className="absolute inset-y-0 right-3 flex items-center text-muted-foreground" aria-hidden="true">
                🔒
              </span>
              <input
                type={showPassword ? "text" : "password"}
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="رمز عبور را دوباره وارد کنید"
                disabled={loading}
                className="w-full rounded-xl border border-border bg-surface px-3 py-2 ps-10 text-sm outline-none transition duration-fast ease-flow focus:border-secondary focus:ring-2 focus:ring-secondary/20 disabled:opacity-60"
              />
            </span>
          </label>

          <PrimaryButton type="submit" disabled={loading} className="mt-1 w-full justify-center">
            {loading ? "در حال ثبت‌نام…" : "ثبت‌نام"}
          </PrimaryButton>

          <p className="text-center text-sm text-muted-foreground">
            قبلاً ثبت‌نام کرده‌اید؟{" "}
            <Link href="/login" className="text-secondary hover:underline">
              ورود
            </Link>
          </p>
        </form>
      </TarotCard>
    </main>
  );
}
