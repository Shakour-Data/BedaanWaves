"use client";

import { useState, useEffect, useMemo } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { TarotCard } from "@/components/ui/TarotCard";
import { InputField } from "@/components/ui/InputField";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { useAuthStore } from "@/store/useAuthStore";
import {
  verifyResetToken,
  confirmResetPassword,
  isValidPassword,
  passwordsMatch,
  type ConfirmResetResult,
} from "@/lib/password-recovery-api";
import { FaCheckCircleIcon, FaExclamationCircleIcon } from "./icons";
import { useAuthT } from "@/i18n/auth";

type ResetPhase = "verifying" | "enter_password" | "confirming" | "success" | "error";

type PwdValidationState = "idle" | "validating" | "valid" | "invalid";

export default function ResetPasswordPage() {
  const t = useAuthT();
  const router = useRouter();
  const searchParams = useSearchParams();

  const token = searchParams?.get("token") ?? "";

  const [phase, setPhase] = useState<ResetPhase>("verifying");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const pwdState: PwdValidationState = useMemo(() => {
    if (!password) return "idle";
    if (password.length < 8) return "invalid";
    if (!confirmPassword) return "valid";
    return password === confirmPassword ? "valid" : "invalid";
  }, [password, confirmPassword]);

  const pwdError: string | null = useMemo(() => {
    if (!password) return null;
    if (password.length < 8) return "Password must be at least 8 characters.";
    if (confirmPassword && password !== confirmPassword) return "Passwords do not match.";
    return null;
  }, [password, confirmPassword]);

  useEffect(() => {
    void (async () => {
      if (!token) {
        setPhase("error");
        setErrorMsg("No recovery token was provided. Please open the link from your email.");
        return;
      }

      const result = await verifyResetToken(token);
      if (result.valid) {
        setPhase("enter_password");
      } else {
        setPhase("error");
        setErrorMsg(
          "That recovery link has expired or is no longer valid. Please request a new link.",
        );
      }
    })();
  }, [token]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!passwordsMatch(password, confirmPassword) || !isValidPassword(password)) {
      setErrorMsg("Please fix the errors above before continuing.");
      return;
    }
    setErrorMsg(null);
    setPhase("confirming");

    try {
      const result: ConfirmResetResult = await confirmResetPassword(token, password);

      if (result.success) {
        setPhase("success");
      } else {
        setPhase("error");
        setErrorMsg(result.error?.message ?? "Unable to reset password. Please try again.");
      }
    } catch {
      setPhase("error");
      setErrorMsg("Network error. Please check your connection and try again.");
    }
  };

  if (phase === "verifying" || phase === "confirming") {
    return (
      <main className="flex min-h-screen items-center justify-center p-3">
        <TarotCard className="w-full max-w-md">
          <div className="text-center">
            <svg
              className="mx-auto h-6 w-6 animate-spin text-[#005A9C]"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <p className="mt-3 text-sm text-[#64748B]" aria-live="polite">
              {phase === "verifying"
                ? (t("login_loading"))
                : (t("login_loading"))}
            </p>
          </div>
        </TarotCard>
      </main>
    );
  }

  if (phase === "error") {
    return (
      <main className="flex min-h-screen items-center justify-center p-3">
        <TarotCard className="w-full max-w-md">
          <div className="text-center">
            <FaExclamationCircleIcon className="mx-auto h-8 w-8 text-[#EF4444]" />
            <h2 className="mt-3 text-xl font-semibold text-[#1E293B]">{t("auth_error_authentication")}</h2>
            <p className="mt-2 text-sm text-[#64748B]">{errorMsg}</p>
            <div className="mt-4">
              <ErrorMessage
                message={errorMsg ?? "An error occurred."}
                actions={[
                  {
                    label: t("login_forgot_password"),
                    onAction: () => router.push("/forgot-password"),
                  },
                  {
                    label: t("login_back_to_login"),
                    onAction: () => router.push("/login"),
                  },
                ]}
                moreHelpSteps={[
                  "1. " + t("login_forgot_password"),
                  "2. " + t("login_forgot_password"),
                  "3. " + t("auth_show_password"),
                ]}
              />
            </div>
          </div>
        </TarotCard>
      </main>
    );
  }

  if (phase === "success") {
    return (
      <main className="flex min-h-screen items-center justify-center p-3">
        <TarotCard className="w-full max-w-md">
          <div className="text-center">
            <FaCheckCircleIcon className="mx-auto h-10 w-10 text-[#10B981]" />
            <h2 className="mt-3 text-xl font-semibold text-[#1E293B]">{t("login_submit")}</h2>
            <p className="mt-2 text-sm text-[#64748B]">
              {t("auth_loading")}
            </p>
            <Link
              href="/login"
              className="btn-primary-brand mt-5 w-full justify-center"
              aria-label={t("login_back_to_login")}
            >
              {t("login_back_to_login")}
            </Link>
          </div>
        </TarotCard>
      </main>
    );
  }

  return (
    <main className="flex min-h-screen items-center justify-center p-3">
      <div className="relative w-full max-w-md">
        <button
          type="button"
          onClick={() => router.push("/login")}
          aria-label={t("login_back_to_login")}
          className="absolute top-4 text-[#64748B] hover:text-[#005A9C] focus:outline-none focus:ring-2 focus:ring-[#005A9C]/30 rounded"
          style={{ left: "1rem" }}
        >
          <svg className="h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.75 19l-7.5-7 7.5-7" />
          </svg>
          <span className="sr-only">{t("login_back_to_login")}</span>
        </button>

        <TarotCard className="w-full">
          <div className="mb-4">
            <ProgressBar currentStep={2} totalSteps={3} stepLabels={[t("login_email"), t("login_password"), t("login_submit")]} />
          </div>

          <h2 className="text-xl font-semibold text-[#1E293B]" id="reset-title">
            {t("signup_password")}
          </h2>
          <p className="mt-1 text-sm text-[#64748B]">
            {t("signup_password")}
          </p>

          <form onSubmit={handleSubmit} className="mt-4 flex flex-col gap-4">
            <div className="relative">
              <InputField
                label={t("signup_password")}
                example="At least 8 characters"
                placeholder={t("signup_password")}
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                validationState={pwdState}
                validationMessage={pwdError ?? undefined}
                autoComplete="new-password"
                aria-label={t("signup_password")}
              />
              <button
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                aria-label={showPassword ? (t("auth_hide_password") || "Hide password") : (t("auth_show_password") || "Show password")}
                className="absolute inset-y-0 right-3 flex items-center text-[#64748B] hover:text-[#1E293B]"
              >
                {showPassword ? (
                  <svg className="h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.98 6.22l9.82 9.82m0 0A9.24 9.24 0 0112 20.25c-4.33-1.5-6.97-5.55-6.97-10.21 0-1.06.23-2.07.63-3l9.74 9.74z" />
                  </svg>
                ) : (
                  <svg className="h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.03 12.32a9.67 9.67 0 012.83-6.05 1 1 0 011.41.22l.03.03a1 1 0 01-.03 1.41 4.5 4.5 0 006.71 6.71 1 1 0 01.22 1.41 9.67 9.67 0 01-6.05 2.83c-.48.08-.98.13-1.5.15a1 1 0 01-.98-1.22z" />
                  </svg>
                )}
              </button>
            </div>

            <InputField
              label={t("signup_confirm_password")}
              example="Repeat your password"
              placeholder={t("signup_confirm_password")}
              type={showPassword ? "text" : "password"}
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              validationState={pwdState}
              autoComplete="new-password"
              aria-label={t("signup_confirm_password")}
            />

            <button
              type="submit"
              disabled={pwdState !== "valid"}
              aria-label={t("signup_submit")}
              className="btn-primary-brand mt-2 w-full justify-center"
            >
              {t("signup_submit")}
            </button>
          </form>
        </TarotCard>
      </div>
    </main>
  );
}
