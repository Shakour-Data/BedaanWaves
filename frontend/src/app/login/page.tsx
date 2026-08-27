"use client";

import { useState } from "react";
import Link from "next/link";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { useAuthStore } from "@/store/useAuthStore";
import { useAuthT } from "@/i18n/auth";
import { FaEyeIcon, FaEyeSlashIcon } from "@/app/reset-password/icons";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const loginStore = useAuthStore((s) => s.login);
  const t = useAuthT();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await loginStore(email, password);
    } catch (err) {
      const message = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail || t("auth_error_authentication");
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-[#F8FAFC] px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-bold text-[#0F172A]">BedaanWaves</h1>
          <p className="mt-1 text-sm text-[#64748B]">Sign in to your account</p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="rounded-2xl border border-[#E2E8F0] bg-white p-6 shadow-sm"
        >
          {error ? (
            <div className="mb-4 rounded-xl bg-[#EF4444]/10 px-3 py-2 text-sm text-[#EF4444]">
              {error}
            </div>
          ) : null}

          <div className="flex flex-col gap-1">
            <label className="text-sm font-medium text-[#0F172A]">
              {t("login_email")}
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder={t("login_email")}
              disabled={loading}
              className="w-full rounded-xl border border-[#E2E8F0] bg-white px-3 py-2 text-sm outline-none transition focus:border-[#005A9C] focus:ring-2 focus:ring-[#005A9C]/20 disabled:opacity-60"
            />
          </div>

          <div className="mt-4 flex flex-col gap-1">
            <label className="text-sm font-medium text-[#0F172A]">
              {t("login_password")}
            </label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                disabled={loading}
                className="w-full rounded-xl border border-[#E2E8F0] bg-white px-3 py-2 text-sm outline-none transition focus:border-[#005A9C] focus:ring-2 focus:ring-[#005A9C]/20 disabled:opacity-60"
              />
              <button
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                aria-label={showPassword ? t("auth_hide_password") : t("auth_show_password")}
                className="absolute inset-y-0 left-3 flex items-center text-[#64748B] transition hover:text-[#1E293B]"
              >
                {showPassword ? <FaEyeSlashIcon className="h-4 w-4" /> : <FaEyeIcon className="h-4 w-4" />}
              </button>
            </div>
          </div>

          <div className="mt-4 flex items-center justify-between text-xs">
            <label className="flex items-center gap-2 text-[#64748B]">
              <input type="checkbox" className="rounded border-[#E2E8F0]" />
              {t("auth_remember_me")}
            </label>
            <Link href="/forgot-password" className="text-[#005A9C] hover:underline">
              {t("login_forgot_password")}
            </Link>
          </div>

          <PrimaryButton type="submit" disabled={loading} className="mt-5 w-full justify-center">
            {loading ? t("auth_loading") : t("login_submit")}
          </PrimaryButton>

          <p className="mt-4 text-center text-sm text-[#64748B]">
            {t("login_no_account")}{" "}
            <Link href="/register" className="text-[#005A9C] hover:underline">
              {t("signup_login_link")}
            </Link>
          </p>
        </form>
      </div>
    </main>
  );
}
