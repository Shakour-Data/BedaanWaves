"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { TarotCard } from "@/components/ui/TarotCard";
import { StockCompare } from "@/components/compare/StockCompare";
import { ArrowLeft } from "lucide-react";
import { NewDashboardShell } from "@/components/layout/NewDashboardShell";

const DEFAULT_SYMBOLS = ["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA"];

export default function ComparePage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialSymbols = searchParams.get("symbols")?.split(",").filter(Boolean) || DEFAULT_SYMBOLS;

  const [symbols, setSymbols] = useState<string[]>(initialSymbols);
  const [inputValue, setInputValue] = useState(symbols.join(", "));

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const symList = inputValue
      .split(",")
      .map((s) => s.trim().toUpperCase())
      .filter((s) => s.length >= 1 && s.length <= 6);
    if (symList.length >= 2) {
      setSymbols(symList);
      router.replace(`/compare?symbols=${symList.join(",")}`);
    }
  };

  const handleClearSymbol = (sym: string) => {
    const newSymbols = symbols.filter((s) => s !== sym);
    if (newSymbols.length >= 2) {
      setSymbols(newSymbols);
      setInputValue(newSymbols.join(", "));
      router.replace(`/compare?symbols=${newSymbols.join(",")}`);
    }
  };

  return (
    <NewDashboardShell title="Stock Comparison">
      <div className="space-y-6 animate-in fade-in duration-300">
        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
          <div className="mb-6 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={() => router.back()}
                className="inline-flex items-center justify-center rounded-xl border border-[var(--color-border)] bg-[var(--color-background)] p-2 text-[var(--color-text-secondary)] hover:border-[var(--color-primary)]/30 hover:text-[var(--color-primary)]"
              >
                <ArrowLeft className="h-5 w-5" />
              </button>
              <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">
                Stock Comparison
              </h1>
            </div>
          </div>

          <form onSubmit={handleSearch} className="mb-6 flex gap-3">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Enter symbols (e.g. AAPL, MSFT, GOOGL)"
              className="flex-1 rounded-xl border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-2.5 text-sm text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] focus:border-[var(--color-primary)] focus:outline-none"
            />
            <button
              type="submit"
              className="rounded-xl border border-[var(--color-primary)] bg-[var(--color-primary)] px-6 py-2 text-sm font-semibold text-white"
            >
              Compare
            </button>
          </form>

          <div className="mb-4 flex flex-wrap gap-2">
            {symbols.map((sym) => (
              <span
                key={sym}
                className="inline-flex items-center gap-1.5 rounded-full bg-[var(--color-background)] px-3 py-1 text-xs font-medium text-[var(--color-text-primary)] border border-[var(--color-border)]"
              >
                {sym}
                {symbols.length > 2 && (
                  <button
                    type="button"
                    onClick={() => handleClearSymbol(sym)}
                    className="hover:text-[var(--color-error)]"
                  >
                    ×
                  </button>
                )}
              </span>
            ))}
          </div>

          {symbols.length >= 2 ? (
            <StockCompare symbols={symbols} />
          ) : (
            <TarotCard title="Select at least 2 symbols to compare">
              <div className="p-8 text-center">
                <p className="text-sm text-[var(--color-text-secondary)]">
                  Enter at least 2 stock symbols above to see a comparison.
                </p>
              </div>
            </TarotCard>
          )}
        </div>
      </div>
    </NewDashboardShell>
  );
}
