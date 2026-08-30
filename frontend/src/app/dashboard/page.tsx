"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { apiClient, getApiErrorMessage } from "@/lib/api";
import { cn } from "@/lib/cn";
import { fetchDashboardData } from "@/lib/api/dashboard";
import type { AssetRow, MarketStat, SignalRow, NewsItem } from "@/lib/dashboard-data";
import { NewDashboardShell } from "@/components/layout/NewDashboardShell";
import { StockDetailSkeleton } from "@/components/ux/SkeletonLoaders";
import { useUXStore } from "@/store/useUXStore";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import type { BreadcrumbItem } from "@/components/ux/Breadcrumbs";

interface MarketIndex {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  isOpen: boolean;
}

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

function StockRow({ stock, index }: { stock: AssetRow; index: number }) {
  const isPositive = stock.changePct >= 0;
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
      </div>
      <div className="shrink-0 text-right">
        <p className="font-semibold text-[var(--color-text-primary)]">${stock.price.toFixed(2)}</p>
        <p className={cn("text-xs", isPositive ? "text-[var(--color-success)]" : "text-[var(--color-error)]")}>
          {isPositive ? "+" : ""}{stock.changePct.toFixed(2)}%
        </p>
      </div>
    </Link>
  );
}

export default function DashboardPage() {
  const [indices, setIndices] = useState<MarketIndex[]>([]);
  const [topStocks, setTopStocks] = useState<AssetRow[]>([]);
  const [marketStats, setMarketStats] = useState<MarketStat[]>([]);
  const [signals, setSignals] = useState<SignalRow[]>([]);
  const [news, setNews] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const addToast = useUXStore((state) => state.addToast);

  const loadDashboard = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await fetchDashboardData();

      setMarketStats(data.marketStats);
      setTopStocks(data.topMovers.slice(0, 5));
      setSignals(data.signals);
      setNews(data.news);

      try {
        const indicesRes = await apiClient.get<Record<string, unknown>>("/market/market-overview?market=NASDAQ");
        if ((indicesRes.data as Record<string, unknown>)?.status === "success") {
          setIndices([
            { symbol: "IXIC", name: "NASDAQ Composite", price: 0, change: 0, changePercent: ((indicesRes.data as Record<string, unknown>).average_change_pct as number) || 0, isOpen: true },
          ]);
        }
      } catch {
        // Indices fetch failed, continue without them
      }
    } catch (err) {
      const message = getApiErrorMessage(err);
      setError(message);
      addToast({ type: "error", message });
    } finally {
      setLoading(false);
    }
  }, [addToast]);

  useEffect(() => {
    loadDashboard(); // eslint-disable-line react-hooks/set-state-in-effect
  }, [loadDashboard]);

  const breadcrumbs: BreadcrumbItem[] = [
    { label: "Dashboard" },
  ];

  if (loading) {
    return (
      <NewDashboardShell title="Dashboard" breadcrumbs={breadcrumbs}>
        <StockDetailSkeleton />
      </NewDashboardShell>
    );
  }

  if (error) {
    return (
      <NewDashboardShell title="Dashboard" breadcrumbs={breadcrumbs}>
        <div className="flex min-h-[40vh] items-center justify-center">
          <ErrorMessage
            message={error}
            actions={[{ label: "Retry", onAction: () => { setError(null); loadDashboard(); } }]}
            moreHelpSteps={["Check your internet connection", "Verify the API service is running"]}
            helpTitle="Troubleshooting steps"
          />
        </div>
      </NewDashboardShell>
    );
  }

  return (
    <NewDashboardShell title="Dashboard" breadcrumbs={breadcrumbs}>
      <div className="space-y-6 animate-in fade-in duration-300">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-[var(--color-text-primary)]">Dashboard</h1>
          <p className="mt-1 text-[var(--color-text-secondary)]">Overview of NASDAQ market performance</p>
        </div>

        {indices.length > 0 && (
          <div className="mb-8 grid gap-6 md:grid-cols-3">
            {indices.map((index) => (
              <MarketIndexCard key={index.symbol} index={index} />
            ))}
          </div>
        )}

        <div className="mb-8 grid gap-6 md:grid-cols-4">
          {marketStats.length > 0 ? (
            marketStats.map((stat, i) => (
              <StatCard
                key={i}
                title={stat.label}
                value={stat.value}
                trend={stat.changePct !== undefined ? `${stat.changePct >= 0 ? "+" : ""}${stat.changePct.toFixed(2)}%` : undefined}
                trendUp={stat.changePct !== undefined ? stat.changePct >= 0 : undefined}
              />
            ))
          ) : (
            <>
              <StatCard title="Nasdaq Composite" value="—" />
              <StatCard title="Active Symbols" value="—" />
              <StatCard title="Top Gainer" value="—" />
              <StatCard title="Top Loser" value="—" />
            </>
          )}
        </div>

        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-xl font-semibold text-[var(--color-text-primary)]">Top NASDAQ Stocks</h2>
            <Link href="/stocks" className="text-sm font-medium text-[var(--color-primary)] hover:underline">
              View All
            </Link>
          </div>
          <div className="space-y-2">
            {topStocks.length > 0 ? (
              topStocks.map((stock, index) => (
                <StockRow key={stock.symbol} stock={stock} index={index} />
              ))
            ) : (
              <p className="text-center text-[var(--color-text-secondary)] py-8">No stock data available</p>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
            <h2 className="text-xl font-semibold text-[var(--color-text-primary)] mb-4">Trading Signals</h2>
            {signals.length > 0 ? (
              <div className="space-y-3">
                {signals.slice(0, 5).map((signal, i) => (
                  <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-[var(--color-background)]">
                    <div className="flex items-center gap-3">
                      <span className={cn(
                        "px-2 py-1 rounded text-xs font-bold",
                        signal.type === "BUY" || signal.type === "STRONG_BUY" ? "bg-[var(--color-success)]/20 text-[var(--color-success)]" :
                        signal.type === "SELL" || signal.type === "STRONG_SELL" ? "bg-[var(--color-error)]/20 text-[var(--color-error)]" :
                        "bg-[var(--color-warning)]/20 text-[var(--color-warning)]"
                      )}>
                        {signal.type}
                      </span>
                      <span className="font-medium text-[var(--color-text-primary)]">{signal.symbol}</span>
                    </div>
                    <span className="text-sm text-[var(--color-text-secondary)]">{signal.confidence}%</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-center text-[var(--color-text-secondary)] py-8">No active signals</p>
            )}
          </div>

          <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
            <h2 className="text-xl font-semibold text-[var(--color-text-primary)] mb-4">Market News</h2>
            {news.length > 0 ? (
              <div className="space-y-3">
                {news.slice(0, 5).map((item, i) => (
                  <div key={i} className="p-3 rounded-lg bg-[var(--color-background)]">
                    <p className="font-medium text-[var(--color-text-primary)] text-sm">{item.title}</p>
                    <div className="flex items-center gap-2 mt-1 text-xs text-[var(--color-text-secondary)]">
                      <span>{item.source}</span>
                      <span>•</span>
                      <span>{item.time}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-center text-[var(--color-text-secondary)] py-8">No news available</p>
            )}
          </div>
        </div>
      </div>
    </NewDashboardShell>
  );
}
