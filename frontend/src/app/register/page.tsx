"use client";

import { useState } from "react";
import Link from "next/link";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { useAuthStore } from "@/store/useAuthStore";
import { useAuthT } from "@/i18n/auth";
import { FaEyeIcon, FaEyeSlashIcon } from "@/app/reset-password/icons";

export default function RegisterPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const registerStore = useAuthStore((s) => s.register);
  const t = useAuthT();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (password.length < 8) {
      setError(t("signup_error_password_length"));
      return;
    }
    if (password !== confirmPassword) {
      setError(t("signup_error_password_match"));
      return;
    }
    setLoading(true);
    try {
      await registerStore(name, email, password);
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
          <p className="mt-1 text-sm text-[#64748B]">Create your account</p>
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
              {t("signup_name")}
            </label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder={t("signup_name")}
              disabled={loading}
              className="w-full rounded-xl border border-[#E2E8F0] bg-white px-3 py-2 text-sm outline-none transition focus:border-[#005A9C] focus:ring-2 focus:ring-[#005A9C]/20 disabled:opacity-60"
            />
          </div>

          <div className="mt-4 flex flex-col gap-1">
            <label className="text-sm font-medium text-[#0F172A]">
              {t("signup_email")}
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder={t("signup_email")}
              disabled={loading}
              className="w-full rounded-xl border border-[#E2E8F0] bg-white px-3 py-2 text-sm outline-none transition focus:border-[#005A9C] focus:ring-2 focus:ring-[#005A9C]/20 disabled:opacity-60"
            />
          </div>

          <div className="mt-4 flex flex-col gap-1">
            <label className="text-sm font-medium text-[#0F172A]">
              {t("signup_password")}
            </label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder={t("signup_password")}
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

          <div className="mt-4 flex flex-col gap-1">
            <label className="text-sm font-medium text-[#0F172A]">
              {t("signup_confirm_password")}
            </label>
            <input
              type={showPassword ? "text" : "password"}
              required
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder={t("signup_confirm_password")}
              disabled={loading}
              className="w-full rounded-xl border border-[#E2E8F0] bg-white px-3 py-2 text-sm outline-none transition focus:border-[#005A9C] focus:ring-2 focus:ring-[#005A9C]/20 disabled:opacity-60"
            />
          </div>

          <PrimaryButton type="submit" disabled={loading} className="mt-5 w-full justify-center">
            {loading ? t("auth_loading") : t("signup_submit")}
          </PrimaryButton>

          <p className="mt-4 text-center text-sm text-[#64748B]">
            {t("signup_already_have_account")}{" "}
            <Link href="/login" className="text-[#005A9C] hover:underline">
              {t("signup_login_link")}
            </Link>
          </p>
        </form>
      </div>
    </main>
  );
}
