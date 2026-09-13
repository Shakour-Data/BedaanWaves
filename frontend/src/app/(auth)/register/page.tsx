"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/useAuthStore";
import { InputField } from "@/components/ui/InputField";
import { PrimaryButton } from "@/components/ui/PrimaryButton";

export default function RegisterPage() {
  const router = useRouter();
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const register = useAuthStore((state) => state.register);
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
    const email = (form.elements.namedItem("email") as HTMLInputElement).value;
    const password = (form.elements.namedItem("password") as HTMLInputElement).value;
    const fullName = (form.elements.namedItem("full_name") as HTMLInputElement).value;
    try {
      await register(username, email, password, fullName);
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
          Create Account
        </h1>
        <p className="text-[var(--color-text-secondary)] mb-6">
          Sign up for BedaanWaves
        </p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <InputField
            label="Username"
            name="username"
            placeholder="Choose a username"
            required
          />
          <InputField
            label="Email"
            name="email"
            type="email"
            placeholder="you@example.com"
            required
          />
          <InputField
            label="Full Name"
            name="full_name"
            placeholder="Your full name"
          />
          <InputField
            label="Password"
            name="password"
            type="password"
            placeholder="Create a password"
            required
          />
          {error && (
            <p className="text-sm text-[var(--color-error)]">{error}</p>
          )}
          <PrimaryButton type="submit" className="w-full" disabled={loading}>
            {loading ? "Creating account..." : "Sign Up"}
          </PrimaryButton>
        </form>
        <p className="mt-4 text-center text-sm text-[var(--color-text-secondary)]">
          Already have an account?{" "}
          <button onClick={() => router.push("/login")} className="text-[var(--color-primary)] hover:underline">
            Sign in
          </button>
        </p>
      </div>
    </div>
  );
}