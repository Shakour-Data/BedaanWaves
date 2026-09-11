"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/useAuthStore";

export default function LoginPage() {
  const router = useRouter();
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  useEffect(() => {
    if (isAuthenticated) {
      router.push("/dashboard");
    }
  }, [isAuthenticated, router]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--color-background)] p-4">
      <div className="w-full max-w-md text-center">
        <div className="mb-6 inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-[var(--color-primary-soft)]">
          <span className="text-3xl font-bold text-[var(--color-primary)]">🔒</span>
        </div>
        <h1 className="text-2xl font-bold text-[var(--color-text-primary)] mb-2">
          Authentication Disabled
        </h1>
        <p className="text-[var(--color-text-secondary)] mb-6">
          Login functionality is temporarily disabled during development.
        </p>
        <button
          onClick={() => router.push("/")}
          className="px-6 py-2.5 rounded-xl bg-[var(--color-primary)] text-white font-medium hover:bg-[var(--color-primary-hover)] transition-colors"
        >
          Go to Home
        </button>
      </div>
    </div>
  );
}