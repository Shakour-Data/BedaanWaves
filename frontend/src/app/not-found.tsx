import Link from "next/link";
import { TarotCard } from "@/components/ui/TarotCard";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { SearchIcon } from "@/components/icons/Icons";

export default function NotFound() {
  return (
    <main className="flex min-h-[60vh] items-center justify-center p-3">
      <TarotCard title="۴۰۴" className="w-full max-w-md text-center">
        <div className="flex flex-col items-center gap-4">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary/10 text-primary">
            <SearchIcon className="h-8 w-8" />
          </div>
          <h1 className="text-4xl font-bold text-foreground">۴۰۴</h1>
          <p className="text-lg text-muted-foreground">صفحه مورد نظر یافت نشد</p>
          <Link href="/">
            <PrimaryButton>بازگشت به خانه</PrimaryButton>
          </Link>
        </div>
      </TarotCard>
    </main>
  );
}
