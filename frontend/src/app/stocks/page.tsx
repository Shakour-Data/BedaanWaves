"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { apiClient } from "@/lib/api";
import { cn } from "@/lib/cn";
import { StockSearchBar } from "@/components/search/StockSearchBar";
import { useRouter } from "next/navigation";
import { useUXStore } from "@/store/useUXStore";

const POPULAR_TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "BRK-B"];

interface Stock {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  marketCap: string;
  peRatio: number;
  sector: string;
  score?: number;
}

function formatMarketCap(value: unknown): string {
  if (typeof value !== "number" || !isFinite(value) || value <= 0) return "-";
  const units = [
    { threshold: 1e12, suffix: "T" },
    { threshold: 1e9, suffix: "B" },
    { threshold: 1e6, suffix: "M" },
  ];
  for (const { threshold, suffix } of units) {
    if (value >= threshold) return `$${(value / threshold).toFixed(2)}${suffix}`;
  }
  return `$${value.toLocaleString()}`;
}

function formatVolume(value: number): string {
  if (!isFinite(value) || value <= 0) return "-";
  if (value >= 1e9) return `${(value / 1e9).toFixed(2)}B`;
  if (value >= 1e6) return `${(value / 1e6).toFixed(2)}M`;
  if (value >= 1e3) return `${(value / 1e3).toFixed(2)}K`;
  return value.toLocaleString();
}

function StockRow({ stock, index }: { stock: Stock; index: number }) {
  const isPositive = stock.change >= 0;
  return (
    <Link
      href={`/stocks/${stock.symbol}`}
      className="group flex items-center gap-4 rounded-lg border border-transparent p-4 transition-all duration-200 hover:border-[var(--color-border)] hover:bg-[var(--color-surface)]/50"
    >
      <div className={cn(
        "flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-sm font-bold",
        index === 0 ? "bg-[var(--color-warning)] text-white" :
        index === 1 ? "bg-gray-400 text-white" :
        index === 2 ? "bg-amber-700 text-white" :
        "bg-[var(--color-border)] text-[var(--color-text-secondary)]"
      )}>
        {index + 1}
      </div>
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[var(--color-primary)]/10 text-sm font-bold text-[var(--color-primary)]">
        {stock.symbol.slice(0, 2)}
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-[var(--color-text-primary)]">{stock.symbol}</span>
          <span className="truncate text-xs text-[var(--color-text-secondary)]">{stock.name}</span>
        </div>
        <div className="flex items-center gap-2 text-xs text-[var(--color-text-secondary)]">
          <span>{stock.sector}</span>
          <span>•</span>
          <span>P/E: {stock.peRatio}</span>
        </div>
      </div>
      {stock.score && (
        <div className="hidden sm:flex shrink-0 items-center gap-1.5 rounded-full bg-[var(--color-primary)]/10 px-2.5 py-1">
          <span className="text-[var(--color-primary)]">Score</span>
          <span className="text-sm font-semibold text-[var(--color-primary)]">{stock.score}</span>
        </div>
      )}
      <div className="shrink-0 text-right">
        <p className="font-semibold text-[var(--color-text-primary)]">${stock.price.toFixed(2)}</p>
        <div className={cn("flex items-center justify-end gap-0.5 text-xs font-medium", isPositive ? "text-[var(--color-success)]" : "text-[var(--color-error)]")}>
          <span>{isPositive ? "Up" : "Down"}</span>
          <span>{isPositive ? "+" : ""}{stock.changePercent.toFixed(2)}%</span>
        </div>
      </div>
    </Link>
  );
}

function StockCard({ stock }: { stock: Stock }) {
  const isPositive = stock.change >= 0;
  return (
    <Link
      href={`/stocks/${stock.symbol}`}
      className="group flex flex-col rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5 transition-all duration-300 hover:border-[var(--color-primary)]/30 hover:shadow-md"
    >
      <div className="mb-4 flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[var(--color-primary)]/10 text-lg font-bold text-[var(--color-primary)]">
            {stock.symbol.slice(0, 2)}
          </div>
          <div>
            <h3 className="font-semibold text-[var(--color-text-primary)]">{stock.symbol}</h3>
            <p className="text-xs text-[var(--color-text-secondary)]">{stock.name}</p>
          </div>
        </div>
        {stock.score && (
          <div className="flex items-center gap-1 rounded-full bg-[var(--color-primary)]/10 px-2 py-1">
            <span className="text-[var(--color-primary)]">Score</span>
            <span className="text-xs font-semibold text-[var(--color-primary)]">{stock.score}</span>
          </div>
        )}
      </div>
      <div className="mb-4">
        <p className="text-2xl font-bold text-[var(--color-text-primary)]">${stock.price.toFixed(2)}</p>
        <div className={cn("flex items-center gap-1 text-sm font-medium", isPositive ? "text-[var(--color-success)]" : "text-[var(--color-error)]")}>
          <span>{isPositive ? "Up" : "Down"}</span>
          <span>{isPositive ? "+" : ""}{stock.change.toFixed(2)} ({isPositive ? "+" : ""}{stock.changePercent.toFixed(2)}%)</span>
        </div>
      </div>
      <div className="mt-auto grid grid-cols-2 gap-2 border-t border-[var(--color-border)] pt-4">
        <div>
          <p className="text-xs text-[var(--color-text-secondary)]">Market Cap</p>
          <p className="text-sm font-medium text-[var(--color-text-primary)]">{stock.marketCap}</p>
        </div>
        <div>
          <p className="text-xs text-[var(--color-text-secondary)]">Volume</p>
          <p className="text-sm font-medium text-[var(--color-text-primary)]">{formatVolume(stock.volume)}</p>
        </div>
      </div>
    </Link>
  );
}

export default function StocksPage() {
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState<"symbol" | "price" | "change" | "score">("symbol");
  const [viewMode, setViewMode] = useState<"list" | "grid">("list");
  const searchParams = useSearchParams();
  const searchQuery = searchParams.get("search") || "";
  const router = useRouter();
  const addToast = useUXStore((state) => state.addToast);

  useEffect(() => {
    async function loadStocks() {
      try {
        let raw: unknown[] = [];
        if (searchQuery.trim()) {
          const res = await apiClient.get(`/stocks/search?q=${encodeURIComponent(searchQuery)}&limit=100`);
          raw = res.data?.data ?? [];
        } else {
          // Browse view: fetch a default set of popular stocks. Use the batch
          // endpoint (POST) so an empty query never triggers a 422 from
          // backends that require a non-empty `q`.
          const res = await apiClient.post(`/stocks/batch`, POPULAR_TICKERS);
          const payload = res.data?.data ?? {};
          raw = Array.isArray(payload) ? payload : Object.values(payload);
        }
        setStocks(
          (raw as Record<string, unknown>[])
            .filter((item) => item && !("error" in item))
            .map((item) => ({
              symbol: (item.symbol ?? item.ticker ?? "") as string,
              name: (item.name ?? item.security_name ?? "") as string,
              price: typeof item.price === "number" ? item.price : 0,
              change: typeof item.change === "number" ? item.change : 0,
              changePercent: typeof item.change_percent === "number" ? item.change_percent : 0,
              volume: typeof item.volume === "number" ? item.volume : 0,
              marketCap: formatMarketCap(item.market_cap),
              peRatio: typeof item.pe_ratio === "number" ? item.pe_ratio : 0,
              sector: (item.sector ?? "-") as string,
              score: typeof item.score === "number" ? item.score : undefined,
            }))
        );
      } catch (err) {
        console.error("Failed to load stocks:", err);
        addToast({ type: "error", message: "Failed to load stocks. Please try again." });
      } finally {
        setLoading(false);
      }
    }
    loadStocks();
  }, [addToast]);

  useEffect(() => {
    if (searchQuery) {
      addToast({ type: "info", message: `Showing results for "${searchQuery}"` });
    }
  }, [searchQuery, addToast]);

  const filteredStocks = useMemo(() => {
    let result = [...stocks];
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter(s => s.symbol.toLowerCase().includes(q) || s.name.toLowerCase().includes(q));
    }
    result.sort((a, b) => {
      switch (sortBy) {
        case "symbol": return a.symbol.localeCompare(b.symbol);
        case "price": return b.price - a.price;
        case "change": return b.changePercent - a.changePercent;
        case "score": return (b.score || 0) - (a.score || 0);
        default: return 0;
      }
    });
    return result;
  }, [stocks, sortBy, searchQuery]);

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="h-12 w-12 animate-spin rounded-full border-4 border-[var(--color-border)] border-t-[#00d4ff]" />
          <p className="text-[var(--color-text-secondary)]">Loading stocks...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--color-text-primary)] tracking-tight">NASDAQ Stocks</h1>
          <p className="text-sm text-[var(--color-text-secondary)]">Browse and analyze NASDAQ-listed companies</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] p-1">
            <button onClick={() => setViewMode("list")} className={cn("rounded-md px-3 py-1.5 text-sm font-medium transition-all", viewMode === "list" ? "bg-[var(--color-primary)] text-white shadow-sm" : "text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]")}>List</button>
            <button onClick={() => setViewMode("grid")} className={cn("rounded-md px-3 py-1.5 text-sm font-medium transition-all", viewMode === "grid" ? "bg-[var(--color-primary)] text-white shadow-sm" : "text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]")}>Grid</button>
          </div>
        </div>
      </div>

      <StockSearchBar
        placeholder="Search stocks, tickers..."
        onSelect={(stock) => router.push(`/stocks/${stock.symbol}`)}
      />

      <div className="flex flex-col gap-4 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)]/50 p-4 lg:flex-row lg:items-center">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-[var(--color-text-secondary)]">Sort by</span>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as "symbol" | "price" | "change" | "score")}
            className="h-10 rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] px-3 text-sm text-[var(--color-text-primary)] focus:border-[var(--color-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]/20 transition-all"
          >
            <option value="symbol">Symbol</option>
            <option value="price">Price</option>
            <option value="change">Change %</option>
            <option value="score">AI Score</option>
          </select>
        </div>
      </div>

      <div className="flex items-center justify-between">
        <p className="text-sm text-[var(--color-text-secondary)]">
          Showing <span className="font-medium text-[var(--color-text-primary)]">{filteredStocks.length}</span> of{" "}
          <span className="font-medium text-[var(--color-text-primary)]">{stocks.length}</span> stocks
        </p>
      </div>

      {filteredStocks.length > 0 ? (
        <div className={cn(viewMode === "grid" ? "grid gap-4 sm:grid-cols-2 lg:grid-cols-3" : "space-y-2")}>
          {filteredStocks.map((stock, index) => viewMode === "list" ? <StockRow key={stock.symbol} stock={stock} index={index} /> : <StockCard key={stock.symbol} stock={stock} />)}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-[var(--color-border)] bg-[var(--color-surface)]/30 py-16">
          <span className="text-4xl text-[#334155]">🔍</span>
          <h3 className="mt-4 text-lg font-medium text-[var(--color-text-primary)]">No stocks found</h3>
          <p className="mt-1 text-sm text-[var(--color-text-secondary)]">Try adjusting your search or filters</p>
        </div>
      )}
    </div>
  );
}