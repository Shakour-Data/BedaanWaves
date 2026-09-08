import Link from "next/link";
import { ArrowUpRight } from "lucide-react";

export default function NerkIndexPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-[var(--color-text-primary)]">Nerek Index</h1>
        <p className="mt-2 text-[var(--color-text-muted)]">
          Neark (نزدک) index constituents and market overview.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <Link
          href="/nerk/constituents"
          className="group rounded-xl border border-[var(--color-border)] p-6 transition-colors hover:border-[var(--color-primary)] hover:shadow-lg"
        >
          <h2 className="text-xl font-semibold text-[var(--color-text-primary)] group-hover:text-[var(--color-primary)]">
            Neark Constituents
          </h2>
          <p className="mt-2 text-sm text-[var(--color-text-muted)]">
            View all Neark index constituents with price history and fundamentals.
          </p>
          <span className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-[var(--color-primary)]">
            View constituents <ArrowUpRight className="h-4 w-4" />
          </span>
        </Link>

        <Link
          href="/stocks"
          className="group rounded-xl border border-[var(--color-border)] p-6 transition-colors hover:border-[var(--color-primary)] hover:shadow-lg"
        >
          <h2 className="text-xl font-semibold text-[var(--color-text-primary)] group-hover:text-[var(--color-primary)]">
            All Stocks
          </h2>
          <p className="mt-2 text-sm text-[var(--color-text-muted)]">
            Browse all available symbols with analysis and screening tools.
          </p>
          <span className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-[var(--color-primary)]">
            Browse stocks <ArrowUpRight className="h-4 w-4" />
          </span>
        </Link>
      </div>
    </div>
  );
}
