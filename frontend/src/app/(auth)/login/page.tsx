"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/useAuthStore";
import { InputField } from "@/components/ui/InputField";
import { PrimaryButton } from "@/components/ui/PrimaryButton";

export default function LoginPage() {
  const router = useRouter();
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const login = useAuthStore((state) => state.login);
  const loading = useAuthStore((state) => state.loading);
  const error = useAuthStore((state) => state.error);

  useEffect(() => {
    if (isAuthenticated) {
      router.push("/dashboard");
    }
  }, [isAuthenticated, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const form = e.target as HTMLFormElement;
    const username = (form.elements.namedItem("username") as HTMLInputElement).value;
    const password = (form.elements.namedItem("password") as HTMLInputElement).value;
    try {
      await login(username, password);
      router.push("/dashboard");
    } catch {
      // Error handled by store
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--color-background)] p-4">
      <div className="w-full max-w-md">
        <div className="mb-6 inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-[var(--color-primary-soft)]">
          <span className="text-3xl font-bold text-[var(--color-primary)]">B</span>
        </div>
        <h1 className="text-2xl font-bold text-[var(--color-text-primary)] mb-2">
          Sign In
        </h1>
        <p className="text-[var(--color-text-secondary)] mb-6">
          Welcome back to BedaanWaves
        </p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <InputField
            label="Username"
            name="username"
            placeholder="Enter your username"
            required
          />
          <InputField
            label="Password"
            name="password"
            type="password"
            placeholder="Enter your password"
            required
          />
          {error && (
            <p className="text-sm text-[var(--color-error)]">{error}</p>
          )}
          <PrimaryButton type="submit" className="w-full" disabled={loading}>
            {loading ? "Signing in..." : "Sign In"}
          </PrimaryButton>
        </form>
        <p className="mt-4 text-center text-sm text-[var(--color-text-secondary)]">
          Don&#39;t have an account?{" "}
          <button onClick={() => router.push("/register")} className="text-[var(--color-primary)] hover:underline">
            Sign up
          </button>
        </p>
      </div>
    </div>
  );
}