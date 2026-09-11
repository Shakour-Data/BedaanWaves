"use client";

import { Suspense } from "react";
import Link from "next/link";

function ResetPasswordDisabled() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--color-background)] p-4">
      <div className="w-full max-w-md text-center">
        <div className="mb-6 inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-[var(--color-primary-soft)]">
          <span className="text-3xl font-bold text-[var(--color-primary)]">🔒</span>
        </div>
        <h1 className="text-2xl font-bold text-[var(--color-text-primary)] mb-2">
          Password Reset Disabled
        </h1>
        <p className="text-[var(--color-text-secondary)] mb-6">
          Password reset functionality is temporarily disabled during development.
        </p>
        <Link
          href="/"
          className="inline-block px-6 py-2.5 rounded-xl bg-[var(--color-primary)] text-white font-medium hover:bg-[var(--color-primary-hover)] transition-colors"
        >
          Go to Home
        </Link>
      </div>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={
      <div className="flex min-h-screen items-center justify-center bg-[var(--color-background)]">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-[var(--color-primary)] border-t-transparent" />
      </div>
    }>
      <ResetPasswordDisabled />
    </Suspense>
  );
}