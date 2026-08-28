"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { apiClient } from "@/lib/api";
import { cn } from "@/lib/cn";

// Types
interface Stock {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  volume: string;
  marketCap: string;
  peRatio: number;
  sector: string;
  score?: number;
}

// Mock Data
const mockStocks: Stock[] = [
  { symbol: "NVDA", name: "NVIDIA Corporation", price: 138.25, change: 4.87, changePercent: 3.65, volume: "312.5M", marketCap: "3.39T", peRatio: 62.8, sector: "Technology", score: 96 },
  { symbol: "MSFT", name: "Microsoft Corporation", price: 432.05, change: 5.12, changePercent: 1.20, volume: "21.8M", marketCap: "3.21T", peRatio: 35.1, sector: "Technology", score: 94 },
  { symbol: "AAPL", name: "Apple Inc.", price: 233.67, change: 3.45, changePercent: 1.50, volume: "52.3M", marketCap: "3.56T", peRatio: 32.4, sector: "Technology", score: 92 },
  { symbol: "GOOGL", name: "Alphabet Inc.", price: 178.35, change: 1.25, changePercent: 0.71, volume: "19.2M", marketCap: "2.21T", peRatio: 25.6, sector: "Communication Services", score: 90 },
  { symbol: "AMZN", name: "Amazon.com Inc.", price: 197.83, change: 2.14, changePercent: 1.09, volume: "38.9M", marketCap: "2.05T", peRatio: 58.3, sector: "Consumer Cyclical", score: 88 },
  { symbol: "META", name: "Meta Platforms Inc.", price: 612.77, change: 12.45, changePercent: 2.07, volume: "15.6M", marketCap: "1.56T", peRatio: 28.4, sector: "Communication Services", score: 86 },
  { symbol: "TSLA", name: "Tesla Inc.", price: 248.50, change: -5.25, changePercent: -2.07, volume: "98.7M", marketCap: "793.2B", peRatio: 68.4, sector: "Consumer Cyclical", score: 75 },
  { symbol: "AMD", name: "Advanced Micro Devices", price: 142.88, change: 3.42, changePercent: 2.45, volume: "48.3M", marketCap: "231.2B", peRatio: 42.1, sector: "Technology", score: 82 },
  { symbol: "INTC", name: "Intel Corporation", price: 21.24, change: -0.42, changePercent: -1.85, volume: "52.1M", marketCap: "91.2B", peRatio: 18.5, sector: "Technology", score: 58 },
  { symbol: "NFLX", name: "Netflix Inc.", price: 877.35, change: 15.23, changePercent: 1.77, volume: "4.2M", marketCap: "382.1B", peRatio: 45.2, sector: "Communication Services", score: 84 },
];

// Components
function StockRow({ stock, index }: { stock: Stock; index: number }) {
  const isPositive = stock.change >= 0;
  
  return (
    <Link
      href={`/stocks/${stock.symbol}`}
      className="group flex items-center gap-4 rounded-lg border border-transparent p-4 transition-all duration-200 hover:border-[var(--color-border)] hover:bg-[var(--color-surface)]/50"
    >
      {/* Rank */}
      <div className={cn(
        "flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-sm font-bold",
        index === 0 ? "bg-[var(--color-warning)] text-white" :
        index === 1 ? "bg-gray-400 text-white" :
        index === 2 ? "bg-amber-700 text-white" :
        "bg-[var(--color-border)] text-[var(--color-text-secondary)]"
      )}>
        {index + 1}
      </div>
      
      {/* Logo */}
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[var(--color-primary)]/10 text-sm font-bold text-[var(--color-primary)]">
        {stock.symbol.slice(0, 2)}
      </div>
      
      {/* Info */}
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
      
      {/* Score */}
      {stock.score && (
        <div className="hidden sm:flex shrink-0 items-center gap-1.5 rounded-full bg-[var(--color-primary)]/10 px-2.5 py-1">
          <span className="text-[var(--color-primary)]">Score</span>
          <span className="text-sm font-semibold text-[var(--color-primary)]">{stock.score}</span>
        </div>
      )}
      
      {/* Price & Change */}
      <div className="shrink-0 text-right">
        <p className="font-semibold text-[var(--color-text-primary)]">${stock.price.toFixed(2)}</p>
        <div className={cn(
          "flex items-center justify-end gap-0.5 text-xs font-medium",
          isPositive ? "text-[var(--color-success)]" : "text-[var(--color-error)]"
        )}>
          <span>{isPositive ? "Up" : "Down"}</span>
          <span>{isPositive ? "+" : ""}{stock.changePercent.toFixed(2)}%</span>
        </div>
      </div>
    </Link>
  );
}

export default function StocksPage() {
  const [stocks, setStocks] = useState<Stock[]>(mockStocks);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState<"symbol" | "price" | "change" | "score">("symbol");
  const [viewMode, setViewMode] = useState<"list" | "grid">("list");

  useEffect(() => {
    // Simulate API loading
    const timer = setTimeout(() => {
      setLoading(false);
    }, 1000);

    return () => clearTimeout(timer);
  }, []);

  const filteredStocks = useMemo(() => {
    let filtered = stocks;

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (stock) =>
          stock.symbol.toLowerCase().includes(query) ||
          stock.name.toLowerCase().includes(query) ||
          stock.sector.toLowerCase().includes(query)
      );
    }

    // Sort
    return [...filtered].sort((a, b) => {
      switch (sortBy) {
        case "symbol":
          return a.symbol.localeCompare(b.symbol);
        case "price":
          return b.price - a.price;
        case "change":
          return b.changePercent - a.changePercent;
        case "score":
          return (b.score || 0) - (a.score || 0);
        default:
          return 0;
      }
    });
  }, [stocks, searchQuery, sortBy]);

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
      {/* Header */}
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">NASDAQ Stocks</h1>
          <p className="text-[var(--color-text-secondary)]">Browse and analyze NASDAQ-listed companies</p>
        </div>
        <div className="flex items-center gap-2">
          <button className="flex items-center gap-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-2 text-sm font-medium text-[var(--color-text-primary)] transition-all hover:border-[var(--color-primary)]/50">
            <span>Down</span>
            Export
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col gap-4 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)]/50 p-4 lg:flex-row lg:items-center">
        {/* Search */}
        <div className="relative flex-1">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-text-secondary)]">Search</span>
          <input
            type="text"
            placeholder="Search by symbol, name, or sector..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="h-10 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] pl-10 pr-4 text-sm text-[var(--color-text-primary)] placeholder-[#64748b] transition-colors focus:border-[var(--color-primary)] focus:outline-none"
          />
        </div>

        {/* Sort */}
        <div className="flex items-center gap-2">
          <span className="text-[var(--color-text-secondary)]">Settings</span>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="h-10 rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] px-3 text-sm text-[var(--color-text-primary)] focus:border-[var(--color-primary)] focus:outline-none"
          >
            <option value="symbol">Symbol</option>
            <option value="price">Price</option>
            <option value="change">Change %</option>
            <option value="score">AI Score</option>
          </select>
        </div>

        {/* View Mode */}
        <div className="flex rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] p-1">
          <button
            onClick={() => setViewMode("list")}
            className={cn(
              "rounded-md p-2 transition-colors",
              viewMode === "list" ? "bg-[var(--color-primary)] text-[var(--color-text-primary)]" : "text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]"
            )}
          >
            <span className="text-sm">Menu</span>
          </button>
          <button
            onClick={() => setViewMode("grid")}
            className={cn(
              "rounded-md p-2 transition-colors",
              viewMode === "grid" ? "bg-[var(--color-primary)] text-[var(--color-text-primary)]" : "text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]"
            )}
          >
            <span className="text-sm">Grid</span>
          </button>
        </div>
      </div>

      {/* Results Count */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-[var(--color-text-secondary)]">
          Showing <span className="font-medium text-[var(--color-text-primary)]">{filteredStocks.length}</span> of{" "}
          <span className="font-medium text-[var(--color-text-primary)]">{stocks.length}</span> stocks
        </p>
        {searchQuery && (
          <button
            onClick={() => setSearchQuery("")}
            className="text-sm text-[var(--color-primary)] hover:underline"
          >
            Clear filters
          </button>
        )}
      </div>

      {/* Stocks List */}
      {filteredStocks.length > 0 ? (
        <div className={cn(
          viewMode === "grid" 
            ? "grid gap-4 sm:grid-cols-2 lg:grid-cols-3" 
            : "space-y-2"
        )}>
          {filteredStocks.map((stock, index) => (
            viewMode === "list" ? (
              <StockRow key={stock.symbol} stock={stock} index={index} />
            ) : (
              <StockCard key={stock.symbol} stock={stock} index={index} />
            )
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-[var(--color-border)] bg-[var(--color-surface)]/30 py-16">
          <span className="text-4xl text-[#334155]">Search</span>
          <h3 className="mt-4 text-lg font-medium text-[var(--color-text-primary)]">No stocks found</h3>
          <p className="mt-1 text-sm text-[var(--color-text-secondary)]">Try adjusting your search or filters</p>
        </div>
      )}
    </div>
  );
}

// StockCard component - Grid view card
function StockCard({ stock, index }: { stock: Stock; index: number }) {
  const isPositive = stock.change >= 0;
  
  return (
    <Link
      href={`/stocks/${stock.symbol}`}
      className="group glass-card flex flex-col rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5 transition-all duration-300 hover:border-[var(--color-primary)]/30 hover:shadow-md"
    >
      {/* Header */}
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
      
      {/* Price */}
      <div className="mb-4">
        <p className="text-2xl font-bold text-[var(--color-text-primary)]">${stock.price.toFixed(2)}</p>
        <div className={cn(
          "flex items-center gap-1 text-sm font-medium",
          isPositive ? "text-[var(--color-success)]" : "text-[var(--color-error)]"
        )}>
          <span>{isPositive ? "Up" : "Down"}</span>
          <span>{isPositive ? "+" : ""}{stock.change.toFixed(2)} ({isPositive ? "+" : ""}{stock.changePercent.toFixed(2)}%)</span>
        </div>
      </div>
      
      {/* Stats */}
      <div className="mt-auto grid grid-cols-2 gap-2 border-t border-[var(--color-border)] pt-4">
        <div>
          <p className="text-xs text-[var(--color-text-secondary)]">Market Cap</p>
          <p className="text-sm font-medium text-[var(--color-text-primary)]">{stock.marketCap}</p>
        </div>
        <div>
          <p className="text-xs text-[var(--color-text-secondary)]">Volume</p>
          <p className="text-sm font-medium text-[var(--color-text-primary)]">{stock.volume}</p>
        </div>
      </div>
    </Link>
  );
}
