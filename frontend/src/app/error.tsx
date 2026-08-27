"use client";

import { TarotCard } from "@/components/ui/TarotCard";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import Link from "next/link";
import { AlertIcon } from "@/components/icons/Icons";

export default function Error({
  error,
  reset }: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="flex min-h-[60vh] items-center justify-center p-3">
      <TarotCard title="خطا" className="w-full max-w-md text-center">
        <div className="flex flex-col items-center gap-4">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-error/10 text-error">
            <AlertIcon className="h-8 w-8" />
          </div>
          <h2 className="text-2xl font-bold text-foreground">Something went wrong!</h2>
          <p className="text-muted-foreground">{error.message}</p>
          <div className="flex gap-3">
            <button
              onClick={reset}
              className="btn btn-primary btn-md"
            >
              Try again
            </button>
            <Link href="/">
              <button className="btn btn-secondary btn-md">
                Go back home
              </button>
            </Link>
          </div>
        </div>
      </TarotCard>
    </main>
  );
}
