"use client";

import { TarotCard } from "@/components/ui/TarotCard";
import { Button } from "@/components/ui/Button";
import Link from "next/link";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="flex min-h-[60vh] items-center justify-center p-3">
      <TarotCard title="Error" className="w-full max-w-md text-center">
        <div className="flex flex-col items-center gap-4">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-error/10 text-error text-3xl font-bold">
            !
          </div>
          <h2 className="text-2xl font-bold text-foreground">Something went wrong!</h2>
          <p className="text-muted-foreground">{error.message}</p>
          <div className="flex gap-3">
            <Button variant="primary" size="md" onClick={reset}>
              Try again
            </Button>
            <Link href="/">
              <Button variant="secondary" size="md">
                Go back home
              </Button>
            </Link>
          </div>
        </div>
      </TarotCard>
    </main>
  );
}