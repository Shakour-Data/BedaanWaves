"use client";

import { useEffect } from "react";
import type { SVGProps } from "react";
import Link from "next/link";
import { TarotCard } from "@/components/ui/TarotCard";
import { InputField } from "@/components/ui/InputField";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { usePasswordRecoveryFSM } from "@/hooks/usePasswordRecoveryFSM";
import { useAuthStore } from "@/store/useAuthStore";
import en from "@/i18n/en.json";
import fa from "@/i18n/fa.json";
import { getDraftEmail } from "@/lib/password-recovery-api";

function FaEnvelopeIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg className="h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true" {...props}>
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
    </svg>
  );
}

function FaCheckCircleIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg className="h-10 w-10 text-[#10B981]" xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true" {...props}>
      <path fillRule="evenodd" d="M2.25 12c0 5.385 4.365 9.75 9.75 9.75s9.75-4.365 9.75-9.75S17.835 2.25 12 2.25 2.25 6.615 2.25 12zm10.707 3.707a1 1 0 01-1.414 0L8.293 12.414a1 1 0 011.414-1.414l2.546 2.546 4.332-4.332a1 1 0 011.414 1.414l-4.332 4.332z" clipRule="evenodd" />
    </svg>
  );
}

function FaArrowRightIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg className="h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true" {...props}>
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.75 19l-7.5-7 7.5-7" />
    </svg>
  );
}

function useT() {
  const lang = useAuthStore((s) => s.currentLang) ?? "en";
  const dict = lang === "fa" ? fa : en;
  return (key: string): string => {
    const keys = key.split(".");
    let value: unknown = dict;
    for (const k of keys) {
      if (value && typeof value === "object") {
        value = (value as Record<string, unknown>)[k];
      } else {
        return key;
      }
    }
    return typeof value === "string" ? value : key;
  };
}

const STEP_LABELS_EN = ["Welcome", "Enter your email", "Confirm email", "Send recovery link"];
const STEP_LABELS_FA = ["خوش‌آمدید", "ایمیل خود را وارد کنید", "تایید ایمیل", "ارسال لینک بازیابی"];

export default function ForgotPasswordPage() {
  const t = useT();
  const lang = useAuthStore((s) => s.currentLang) ?? "en";
  const dir = lang === "fa" ? "rtl" : "ltr";
  const stepLabels = lang === "fa" ? STEP_LABELS_FA : STEP_LABELS_EN;

  const fsm = usePasswordRecoveryFSM(lang);
  const {
    state,
    data,
    emailError,
    errorMessage,
    isProcessing,
    start,
    setEmail,
    validateAndProceed,
    confirm,
    edit,
    retry,
    back,
  } = fsm;

  /* Restore any auto-saved draft email on mount (network resilience). */
  useEffect(() => {
    const draft = getDraftEmail();
    if (draft && !data.email) {
      setEmail(draft);
    }
  }, [data.email, setEmail]);

  /* ---- Render helpers -------------------------------------------- */

  const renderBackButton = () =>
    state !== "Welcome" && (
      <button
        type="button"
        onClick={back}
        aria-label={t("forgot_password.back")}
        className="absolute top-4 text-[#64748B] hover:text-[#005A9C] focus:outline-none focus:ring-2 focus:ring-[#005A9C]/30 rounded"
        style={{ [dir === "rtl" ? "left" : "right"]: "1rem" }}
      >
        <FaArrowRightIcon className="h-4 w-4" />
        <span className="sr-only">{t("forgot_password.back")}</span>
      </button>
    );

  const renderState = () => {
    switch (state) {
      /* -------------------------------------------------- Welcome */
      case "Welcome":
        return (
          <div className="text-center">
            <h1 className="text-2xl font-bold text-[#1E293B]" id="welcome-title">
              {t("forgot_password.title") || "Reset your password"}
            </h1>
            <p className="mt-3 text-sm text-[#64748B]">
              {t("forgot_password.welcome_description") ||
                "Enter your email and we'll send you a recovery link."}
            </p>
            <button
              type="button"
              onClick={start}
              aria-label={t("forgot_password.start_button") || "Start recovery"}
              className="btn-primary-brand mt-6 w-full justify-center"
            >
              {t("forgot_password.start_button") || "Start recovery"}
            </button>
          </div>
        );

      /* -------------------------------------------------- Data_Entry */
      case "Data_Entry":
        return (
          <div>
            <h2 className="text-xl font-semibold text-[#1E293B]" id="data-entry-title">
              {t("forgot_password.data_entry_title") || "Enter your email"}
            </h2>
            <p className="mt-1 text-sm text-[#64748B]">
              {t("forgot_password.instruction") ||
                "Enter your email to receive a password reset link."}
            </p>

            <div className="mt-4">
              <InputField
                label={t("auth.email") || "Email"}
                example="you@example.com"
                placeholder={t("login.email_placeholder") || "you@example.com"}
                type="email"
                value={data.email}
                onChange={(e) => setEmail(e.target.value)}
                validationState={emailError ? "invalid" : "idle"}
                validationMessage={emailError ?? undefined}
                icon={<FaEnvelopeIcon />}
                autoComplete="email"
                aria-label={t("auth.email") || "Email"}
              />
            </div>

            <button
              type="button"
              onClick={validateAndProceed}
              aria-label={t("forgot_password.next_button") || "Continue"}
              className="btn-primary-brand mt-5 w-full justify-center"
            >
              {t("forgot_password.next_button") || "Continue"}
            </button>

            <p className="mt-3 text-center text-xs text-[#64748B]">
              <Link href="/login" className="text-[#005A9C] hover:underline">
                {t("login.back_to_login") || "Back to login"}
              </Link>
            </p>
          </div>
        );

      /* -------------------------------------------------- Confirmation */
      case "Confirmation":
        return (
          <div>
            <h2 className="text-xl font-semibold text-[#1E293B]" id="confirmation-title">
              {t("forgot_password.confirmation_title") || "Confirm your email"}
            </h2>
            <p className="mt-1 text-sm text-[#64748B]">
              {t("forgot_password.confirmation_description") ||
                "Please confirm the email address below."}
            </p>

            <div className="mt-4 rounded-lg bg-[#F8FAFC] px-3 py-2 text-sm">
              <span className="font-medium text-[#1E293B]">{data.email}</span>
            </div>

            <div className="mt-5 flex gap-3">
              <button
                type="button"
                onClick={edit}
                aria-label={t("forgot_password.edit_button") || "Edit"}
                className="flex-1 rounded-xl border border-[#005A9C] px-4 py-2 text-sm font-medium text-[#005A9C] hover:bg-[#005A9C]/5 focus:outline-none focus:ring-2 focus:ring-[#005A9C]/30"
              >
                {t("forgot_password.edit_button") || "Edit"}
              </button>
              <button
                type="button"
                onClick={confirm}
                disabled={isProcessing}
                aria-label={t("forgot_password.send_button") || "Send recovery link"}
                className="btn-primary-brand flex-1 justify-center"
              >
                {t("forgot_password.send_button") || "Send recovery link"}
              </button>
            </div>
          </div>
        );

      /* -------------------------------------------------- Processing */
      case "Processing":
        return (
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
              {t("forgot_password.processing") || "Sending your recovery link…"}
            </p>
          </div>
        );

      /* -------------------------------------------------- Result */
      case "Result":
        return (
          <div className="text-center">
            <FaCheckCircleIcon className="mx-auto" aria-hidden="true" />
            <h2 className="mt-3 text-xl font-semibold text-[#1E293B]" id="result-title">
              {t("forgot_password.result_title") || "Check your email"}
            </h2>
            <p className="mt-2 text-sm text-[#1E293B]">
              {t("forgot_password.sent_message") || "Recovery link sent to your email"}
            </p>
            <p className="mt-1 text-xs text-[#64748B]">
              {t("forgot_password.result_hint") ||
                "The link will expire in 1 hour. If you don't see it, check your spam folder."}
            </p>
            <Link href="/login" className="btn-primary-brand mt-5 w-full justify-center">
              {t("forgot_password.to_login") || "Back to login"}
            </Link>
          </div>
        );

      /* -------------------------------------------------- Error_Recovery */
      case "Error_Recovery":
        return (
          <div>
            <h2 className="text-xl font-semibold text-[#1E293B]" id="error-title">
              {t("forgot_password.error_title") || "Something went wrong"}
            </h2>

            <div className="mt-4">
              <ErrorMessage
                message={errorMessage?.message ?? t("forgot_password.error_default") ?? "An error occurred."}
                actions={[
                  { label: t("forgot_password.retry_button") || "Retry", onAction: retry },
                  { label: t("forgot_password.back_to_start") || "Back to start", onAction: back },
                ]}
                moreHelpSteps={[
                  "1. " + (t("forgot_password.help_step1") || "Check your email address for typos"),
                  "2. " + (t("forgot_password.help_step2") || "Ensure your device is connected to the internet"),
                  "3. " + (t("forgot_password.help_step3") || "If problems persist, contact support"),
                ]}
              />
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center p-3" dir={dir}>
      <div className="relative w-full max-w-md">
        {renderBackButton()}
        <TarotCard
          title={state === "Welcome" ? t("forgot_password.title") || "Reset your password" : undefined}
          className="w-full"
        >
          {state !== "Welcome" && state !== "Result" && state !== "Error_Recovery" && (
            <div className="mb-4">
              <ProgressBar
                currentStep={state === "Data_Entry" ? 2 : state === "Confirmation" ? 3 : 4}
                totalSteps={4}
                stepLabels={stepLabels}
              />
            </div>
          )}

          {renderState()}
        </TarotCard>
      </div>
    </main>
  );
}
