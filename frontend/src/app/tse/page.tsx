import Link from "next/link";
import { ArrowUpRight } from "lucide-react";

export default function TseIndexPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-[var(--color-text-primary)]">Tehran Stock Exchange</h1>
        <p className="mt-2 text-[var(--color-text-muted)]">
          TSE market data, Neark (نزدک) index constituents, and analysis.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <Link
          href="/tse/nerk"
          className="group rounded-xl border border-[var(--color-border)] p-6 transition-colors hover:border-[var(--color-primary)] hover:shadow-lg"
        >
          <h2 className="text-xl font-semibold text-[var(--color-text-primary)] group-hover:text-[var(--color-primary)]">
            Neark Index (نزدک)
          </h2>
          <p className="mt-2 text-sm text-[var(--color-text-muted)]">
            View Neark index constituents, top gainers, top losers, and market overview.
          </p>
          <span className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-[var(--color-primary)]">
            View Neark <ArrowUpRight className="h-4 w-4" />
          </span>
        </Link>

        <Link
          href="/tse/symbols"
          className="group rounded-xl border border-[var(--color-border)] p-6 transition-colors hover:border-[var(--color-primary)] hover:shadow-lg"
        >
          <h2 className="text-xl font-semibold text-[var(--color-text-primary)] group-hover:text-[var(--color-primary)]">
            All TSE Symbols
          </h2>
          <p className="mt-2 text-sm text-[var(--color-text-muted)]">
            Browse all Tehran Stock Exchange symbols with price history and fundamentals.
          </p>
          <span className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-[var(--color-primary)]">
            Browse symbols <ArrowUpRight className="h-4 w-4" />
          </span>
        </Link>
      </div>
    </div>
  );
}
