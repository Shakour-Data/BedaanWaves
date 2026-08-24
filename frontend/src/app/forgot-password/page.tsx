"use client";

import { useState } from "react";
import Link from "next/link";
import { TarotCard } from "@/components/ui/TarotCard";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { useAuthStore } from "@/store/useAuthStore";
import en from "@/i18n/en.json";
import fa from "@/i18n/fa.json";

const t = (key: string) => {
  const lang = typeof window !== "undefined" ? localStorage.getItem("lang") || "en" : "en";
  const dict = lang === "fa" ? fa : en;
  const keys = key.split(".");
  let value: any = dict;
  for (const k of keys) {
    if (value && typeof value === "object") {
      value = value[k];
    } else {
      return key;
    }
  }
  return typeof value === "string" ? value : key;
};

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);
  const currentLang = useAuthStore((s) => s.currentLang);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    await new Promise((r) => setTimeout(r, 600));
    setSent(true);
    setLoading(false);
  };

  return (
    <main className="flex min-h-screen items-center justify-center p-3">
      <TarotCard icon="" title={t("login.forgot_password")} className="w-full max-w-md">
        {sent ? (
          <p className="text-sm text-muted-foreground">
            {t("forgot_password.sent_message") || "اگر ایمیل معتبر باشد، لینک بازیابی ارسال شد."}
          </p>
        ) : (
          <form onSubmit={handleSubmit} className="flex flex-col gap-3">
            <p className="text-sm text-muted-foreground">
              {t("forgot_password.instruction") || "ایمیل خود را وارد کنید تا لینک بازیابی ارسال شود."}
            </p>
            <label className="flex flex-col gap-1">
              <span className="text-sm text-muted-foreground">{t("auth.email")}</span>
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
            <PrimaryButton type="submit" disabled={loading} className="mt-1 w-full justify-center">
              {loading ? t("auth.loading") : (t("forgot_password.submit") || "ارسال لینک بازیابی")}
            </PrimaryButton>
            <p className="text-center text-sm text-muted-foreground">
              <Link href="/login" className="text-secondary hover:underline">
                {t("login.back_to_login") || "بازگشت به ورود"}
              </Link>
            </p>
          </form>
        )}
      </TarotCard>
    </main>
  );
}

