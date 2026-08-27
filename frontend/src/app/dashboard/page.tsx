"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiClient } from "@/lib/api";
import { cn } from "@/lib/cn";

// Types
interface MarketIndex {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  isOpen: boolean;
}

interface TopStock {
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

interface MarketMover {
  symbol: string;
  name: string;
  changePercent: number;
  type: "gainer" | "loser";
}

// Mock Data (will be replaced with API calls)
const mockIndices: MarketIndex[] = [
  { symbol: "IXIC", name: "NASDAQ Composite", price: 17713.52, change: 125.38, changePercent: 0.71, isOpen: true },
  { symbol: "NDX", name: "NASDAQ-100", price: 20412.18, change: 142.65, changePercent: 0.70, isOpen: true },
  { symbol: "SPX", name: "S&P 500", price: 5980.36, change: 28.44, changePercent: 0.48, isOpen: true },
];

const mockTopStocks: TopStock[] = [
  { symbol: "NVDA", name: "NVIDIA Corporation", price: 138.25, change: 4.87, changePercent: 3.65, volume: "312.5M", marketCap: "3.39T", peRatio: 62.8, sector: "Technology", score: 96 },
  { symbol: "MSFT", name: "Microsoft Corporation", price: 432.05, change: 5.12, changePercent: 1.20, volume: "21.8M", marketCap: "3.21T", peRatio: 35.1, sector: "Technology", score: 94 },
  { symbol: "AAPL", name: "Apple Inc.", price: 233.67, change: 3.45, changePercent: 1.50, volume: "52.3M", marketCap: "3.56T", peRatio: 32.4, sector: "Technology", score: 92 },
  { symbol: "GOOGL", name: "Alphabet Inc.", price: 178.35, change: 1.25, changePercent: 0.71, volume: "19.2M", marketCap: "2.21T", peRatio: 25.6, sector: "Communication Services", score: 90 },
  { symbol: "AMZN", name: "Amazon.com Inc.", price: 197.83, change: 2.14, changePercent: 1.09, volume: "38.9M", marketCap: "2.05T", peRatio: 58.3, sector: "Consumer Cyclical", score: 88 },
];

const mockMarketMovers: MarketMover[] = [
  { symbol: "NVDA", name: "NVIDIA Corporation", changePercent: 3.65, type: "gainer" },
  { symbol: "AMD", name: "Advanced Micro Devices", changePercent: 2.45, type: "gainer" },
  { symbol: "META", name: "Meta Platforms Inc.", changePercent: 2.07, type: "gainer" },
  { symbol: "TSLA", name: "Tesla Inc.", changePercent: -2.07, type: "loser" },
  { symbol: "INTC", name: "Intel Corporation", changePercent: -1.85, type: "loser" },
];

// Components
function StatCard({ title, value, subtitle, trend, trendUp }: { title: string; value: string; subtitle?: string; trend?: string; trendUp?: boolean }) {
  return (
    <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
      <p className="text-sm font-medium text-[var(--color-text-secondary)]">{title}</p>
      <p className="mt-2 text-3xl font-bold text-[var(--color-text-primary)]">{value}</p>
      {subtitle && <p className="mt-1 text-sm text-[var(--color-text-secondary)]">{subtitle}</p>}
      {trend && (
        <p className={cn("mt-2 text-sm font-medium", trendUp ? "text-[var(--color-success)]" : "text-[var(--color-error)]")}>
          {trendUp ? "+" : ""}{trend}
        </p>
      )}
    </div>
  );
}

function MarketIndexCard({ index }: { index: MarketIndex }) {
  const isPositive = index.change >= 0;
  
  return (
    <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-lg font-semibold text-[var(--color-text-primary)]">{index.symbol}</p>
          <p className="text-sm text-[var(--color-text-secondary)]">{index.name}</p>
        </div>
        <span className={cn("rounded px-2 py-1 text-xs font-medium", index.isOpen ? "bg-[var(--color-success)]/10 text-[var(--color-success)]" : "bg-[var(--color-warning)]/10 text-[var(--color-warning)]")}>
          {index.isOpen ? "Open" : "Closed"}
        </span>
      </div>
      <div className="mt-4">
        <p className="text-2xl font-bold text-[var(--color-text-primary)]">{index.price.toLocaleString()}</p>
        <p className={cn("mt-1 text-sm font-medium", isPositive ? "text-[var(--color-success)]" : "text-[var(--color-error)]")}>
          {isPositive ? "+" : ""}{index.change.toFixed(2)} ({isPositive ? "+" : ""}{index.changePercent.toFixed(2)}%)
        </p>
      </div>
    </div>
  );
}

function StockRow({ stock, index }: { stock: TopStock; index: number }) {
  const isPositive = stock.change >= 0;
  
  return (
    <Link
      href={`/stocks/${stock.symbol}`}
      className="flex items-center gap-4 rounded-lg border border-transparent p-4 transition-all hover:border-[var(--color-border)] hover:bg-[var(--color-background)]"
    >
      <div className={cn(
        "flex h-8 w-8 shrink-0 items-center justify-center rounded text-sm font-bold",
        index === 0 ? "bg-[var(--color-warning)] text-white" :
        index === 1 ? "bg-gray-400 text-white" :
        index === 2 ? "bg-amber-700 text-white" :
        "bg-gray-200 text-gray-600 dark:bg-gray-800 dark:text-gray-400"
      )}>
        {index + 1}
      </div>
      
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded bg-[var(--color-primary)]/10 text-sm font-bold text-[var(--color-primary)]">
        {stock.symbol.slice(0, 2)}
      </div>
      
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-[var(--color-text-primary)]">{stock.symbol}</span>
          <span className="truncate text-xs text-[var(--color-text-secondary)]">{stock.name}</span>
        </div>
        <div className="flex items-center gap-2 text-xs text-[var(--color-text-secondary)]">
          <span>{stock.sector}</span>
          <span>|</span>
          <span>P/E: {stock.peRatio}</span>
        </div>
      </div>
      
      {stock.score && (
        <div className="hidden sm:flex shrink-0 items-center gap-1 rounded bg-[var(--color-primary)]/10 px-2 py-1">
          <span className="text-xs font-semibold text-[var(--color-primary)]">{stock.score}</span>
        </div>
      )}
      
      <div className="shrink-0 text-right">
        <p className="font-semibold text-[var(--color-text-primary)]">${stock.price.toFixed(2)}</p>
        <p className={cn("text-xs", isPositive ? "text-[var(--color-success)]" : "text-[var(--color-error)]")}>
          {isPositive ? "+" : ""}{stock.changePercent.toFixed(2)}%
        </p>
      </div>
    </Link>
  );
}

export default function DashboardPage() {
  const [indices, setIndices] = useState<MarketIndex[]>(mockIndices);
  const [topStocks, setTopStocks] = useState<TopStock[]>(mockTopStocks);
  const [marketMovers, setMarketMovers] = useState<MarketMover[]>(mockMarketMovers);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setLoading(false);
    }, 1000);
    return () => clearTimeout(timer);
  }, []);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-[var(--color-text-secondary)]">Loading dashboard...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[var(--color-background)] p-6">
      <div className="mx-auto max-w-7xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-[var(--color-text-primary)]">Dashboard</h1>
          <p className="mt-1 text-[var(--color-text-secondary)]">Overview of NASDAQ market performance</p>
        </div>

        {/* Market Indices */}
        <div className="mb-8 grid gap-6 md:grid-cols-3">
          {indices.map((index) => (
            <MarketIndexCard key={index.symbol} index={index} />
          ))}
        </div>

        {/* Stats Grid */}
        <div className="mb-8 grid gap-6 md:grid-cols-4">
          <StatCard title="Total Volume" value="2.4B" subtitle="Daily trading volume" trend="12%" trendUp={true} />
          <StatCard title="Market Cap" value="$15.2T" subtitle="Total NASDAQ market cap" trend="8%" trendUp={true} />
          <StatCard title="Active Stocks" value="3,745" subtitle="Stocks actively trading" trend="0.5%" trendUp={true} />
          <StatCard title="Avg Score" value="74.2" subtitle="Average AI score" trend="2%" trendUp={true} />
        </div>

        {/* Top Stocks */}
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-xl font-semibold text-[var(--color-text-primary)]">Top NASDAQ Stocks</h2>
            <Link href="/stocks" className="text-sm font-medium text-[var(--color-primary)] hover:underline">
              View All
            </Link>
          </div>
          <div className="space-y-2">
            {topStocks.slice(0, 5).map((stock, index) => (
              <StockRow key={stock.symbol} stock={stock} index={index} />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
