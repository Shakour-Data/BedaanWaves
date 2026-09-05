import Link from "next/link";
import { TarotCard } from "@/components/ui/TarotCard";
import { PrimaryButton } from "@/components/ui/PrimaryButton";

export default function NotFound() {
  return (
    <main className="flex min-h-[60vh] items-center justify-center p-3">
      <TarotCard title="404" className="w-full max-w-md text-center">
        <div className="flex flex-col items-center gap-4">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary/10 text-primary text-2xl font-bold">
            ?
          </div>
          <h1 className="text-4xl font-bold text-foreground">404</h1>
          <p className="text-lg text-muted-foreground">Page Not Found</p>
          <Link href="/">
            <PrimaryButton>Back to Home</PrimaryButton>
          </Link>
        </div>
      </TarotCard>
    </main>
  );
}
