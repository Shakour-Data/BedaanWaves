"use client";

import { StockSearchBar } from "@/components/search/StockSearchBar";
import { useRecentSearches } from "@/hooks/useRecentSearches";

export default function SearchDemoPage() {
  const { recent, addRecent } = useRecentSearches();

  return (
    <div className="mx-auto max-w-2xl space-y-6 p-8">
      <div>
        <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">Stock Search</h1>
        <p className="text-sm text-[var(--color-text-secondary)]">
          Search by ticker symbol or company name. Try typing &ldquo;apple&rdquo;, &ldquo;AAPL&rdquo;,
          or even a typo like &ldquo;GOOG&rdquo; to find Alphabet.
        </p>
      </div>

      <StockSearchBar
        placeholder="Search stocks, tickers..."
        recentSearches={recent.length > 0 ? recent : ["AAPL", "TSLA", "NVDA", "MSFT", "GOOGL", "AMZN"]}
        onRecent={addRecent}
        onSelect={(stock) => {
          console.log("Selected stock:", stock);
        }}
        minQueryLength={1}
      />

      <div className="rounded-xl border border-dashed border-[var(--color-border)] bg-[var(--color-surface)]/30 p-6">
        <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">Integration Example</h2>
        <pre className="mt-3 overflow-x-auto rounded-lg bg-[var(--color-background)] p-4 text-xs text-[var(--color-text-secondary)]">
{`import { StockSearchBar } from "@/components/search/StockSearchBar";
import { useRecentSearches } from "@/hooks/useRecentSearches";

export default function MyPage() {
  const { recent, addRecent } = useRecentSearches();
  return (
    <StockSearchBar
      placeholder="Search stocks..."
      recentSearches={recent}
      onRecent={addRecent}
      onSelect={(stock) => { console.log("Selected:", stock); }}
    />
  );
}`}
        </pre>
      </div>
    </div>
  );
}
