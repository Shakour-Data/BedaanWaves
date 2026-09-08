"use client";

import { useEffect, useMemo, useRef, useState, useCallback } from "react";
import Link from "next/link";
import {
  TrendingUp,
  TrendingDown,
  RefreshCw,
  Globe,
} from "lucide-react";
import { NewDashboardShell } from "@/components/layout/NewDashboardShell";
import { PageLoading } from "@/components/ui/PageLoading";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { Card } from "@/components/ui/Card";
import { cn } from "@/lib/cn";
import {
  fetchNerkConstituents,
  fetchNerkOverview,
  fetchTseMarketOverview,
  type TseConstituent,
  type TseOverviewResponse,
} from "@/lib/api/tse";
import { useUXStore } from "@/store/useUXStore";

interface MoversRow {
  symbol: string;
  name: string;
  market: "TSE";
  price: number;
  changePct: number;
}

export default function TseNerekPage() {
  const addToast = useUXStore((s) => s.addToast);
  const [overview, setOverview] = useState<TseOverviewResponse | null>(null);
  const [marketOverview, setMarketOverview] = useState<{
    total_symbols: number;
    active_symbols: number;
    currency: string;
    timezone: string;
    index: string;
    last_updated: string;
  } | null>(null);
  const [constituents, setConstituents] = useState<TseConstituent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async (mode: "initial" | "refresh") => {
    if (mode === "initial") setLoading(true);
    else setRefreshing(true);
    setError(null);
    try {
      const [overviewData, marketData, constituentsData] = await Promise.allSettled([
        fetchNerkOverview(),
        fetchTseMarketOverview(),
        fetchNerkConstituents(),
      ]);

      if (overviewData.status === "rejected" && marketData.status === "rejected") {
        const msg =
          (overviewData.reason instanceof Error && overviewData.reason.message) ||
          (marketData.reason instanceof Error && marketData.reason.message) ||
          "Failed to load TSE data";
        setError(msg);
        if (mode === "initial") {
          addToast({ type: "error", message: msg });
        }
        return;
      }

      if (overviewData.status === "fulfilled") {
        setOverview(overviewData.value);
      }
      if (marketData.status === "fulfilled") {
        setMarketOverview(marketData.value.data);
      }
      if (constituentsData.status === "fulfilled") {
        setConstituents(constituentsData.value);
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to load TSE data";
      setError(msg);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [addToast]);

  const initialLoadRef = useRef(true);
  useEffect(() => {
    if (initialLoadRef.current) {
      initialLoadRef.current = false;
      void load("initial");
    }
  }, [load]);

  const topGainers = useMemo<MoversRow[]>(
    () =>
      (overview?.top_gainers ?? []).map((g) => ({
        symbol: g.symbol,
        name: g.name,
        market: "TSE" as const,
        price: g.price,
        changePct: g.change_pct,
      })),
    [overview]
  );

  const topLosers = useMemo<MoversRow[]>(
    () =>
      (overview?.top_losers ?? []).map((g) => ({
        symbol: g.symbol,
        name: g.name,
        market: "TSE" as const,
        price: g.price,
        changePct: g.change_pct,
      })),
    [overview]
  );

  const stats = useMemo(
    () => [
      { label: "Nerek Constituents", value: String(overview?.constituents_count ?? constituents.length ?? "—") },
      { label: "Avg Change", value: overview ? `${overview.avg_change_pct.toFixed(2)}%` : "—" },
      { label: "Active Symbols", value: String(marketOverview?.active_symbols ?? "—") },
      { label: "Currency", value: marketOverview?.currency ?? "IRR" },
    ],
    [overview, constituents.length, marketOverview]
  );

  if (loading) {
    return (
      <NewDashboardShell title="TSE / Neark Index">
        <PageLoading />
      </NewDashboardShell>
    );
  }

  if (error && !overview) {
    return (
      <NewDashboardShell title="TSE / Neark Index">
        <ErrorMessage
          message={error}
          actions={[
            { label: "Retry", onAction: () => load("initial") },
          ]}
        />
      </NewDashboardShell>
    );
  }

  return (
    <NewDashboardShell title="TSE / Neark Index">
      <div className="mb-6 flex items-center justify-between">
        <p className="text-[var(--color-text-muted)]">
          Tehran Stock Exchange Neark (نزدک) constituents and market overview
        </p>
        <button
          onClick={() => load("refresh")}
          disabled={refreshing}
          className={cn(
            "inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors",
            refreshing
              ? "bg-[var(--color-muted)] text-[var(--color-text-muted)]"
              : "bg-[var(--color-primary)] text-white hover:bg-[var(--color-primary-dark)]"
          )}
        >
          <RefreshCw className={cn("h-4 w-4", refreshing && "animate-spin")} />
          {refreshing ? "Refreshing..." : "Refresh"}
        </button>
      </div>
      <div className="space-y-6">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {stats.map((stat) => (
            <Card key={stat.label} className="p-4">
              <p className="text-xs font-medium uppercase tracking-wider text-[var(--color-text-muted)]">
                {stat.label}
              </p>
              <p className="mt-2 text-2xl font-bold text-[var(--color-text-primary)]">{stat.value}</p>
            </Card>
          ))}
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <Card className="p-6">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">Top Gainers</h2>
              <TrendingUp className="h-5 w-5 text-emerald-500" />
            </div>
            <div className="mt-4 space-y-3">
              {topGainers.length === 0 ? (
                <p className="text-sm text-[var(--color-text-muted)]">No gainers available</p>
              ) : (
                topGainers.map((item) => (
                  <Link
                    key={item.symbol}
                    href={`/stocks/${item.symbol}`}
                    className="flex items-center justify-between rounded-lg border border-[var(--color-border)] p-3 transition-colors hover:bg-[var(--color-muted)]"
                  >
                    <div>
                      <p className="font-mono text-sm font-semibold text-[var(--color-text-primary)]">
                        {item.symbol}
                      </p>
                      <p className="text-xs text-[var(--color-text-muted)]">{item.name}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-semibold text-emerald-600">
                        +{item.changePct.toFixed(2)}%
                      </p>
                      <p className="text-xs text-[var(--color-text-muted)]">
                        {item.price.toLocaleString()} {marketOverview?.currency ?? "IRR"}
                      </p>
                    </div>
                  </Link>
                ))
              )}
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">Top Losers</h2>
              <TrendingDown className="h-5 w-5 text-rose-500" />
            </div>
            <div className="mt-4 space-y-3">
              {topLosers.length === 0 ? (
                <p className="text-sm text-[var(--color-text-muted)]">No losers available</p>
              ) : (
                topLosers.map((item) => (
                  <Link
                    key={item.symbol}
                    href={`/stocks/${item.symbol}`}
                    className="flex items-center justify-between rounded-lg border border-[var(--color-border)] p-3 transition-colors hover:bg-[var(--color-muted)]"
                  >
                    <div>
                      <p className="font-mono text-sm font-semibold text-[var(--color-text-primary)]">
                        {item.symbol}
                      </p>
                      <p className="text-xs text-[var(--color-text-muted)]">{item.name}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-semibold text-rose-600">
                        {item.changePct.toFixed(2)}%
                      </p>
                      <p className="text-xs text-[var(--color-text-muted)]">
                        {item.price.toLocaleString()} {marketOverview?.currency ?? "IRR"}
                      </p>
                    </div>
                  </Link>
                ))
              )}
            </div>
          </Card>
        </div>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">Constituents</h2>
            <Globe className="h-5 w-5 text-[var(--color-primary)]" />
          </div>
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead>
                <tr className="border-b border-[var(--color-border)]">
                  <th className="pb-2 font-medium text-[var(--color-text-muted)]">Symbol</th>
                  <th className="pb-2 font-medium text-[var(--color-text-muted)]">Name</th>
                  <th className="pb-2 font-medium text-[var(--color-text-muted)]">Sector</th>
                  <th className="pb-2 font-medium text-[var(--color-text-muted)]">Class</th>
                  <th className="pb-2 font-medium text-[var(--color-text-muted)]">Status</th>
                </tr>
              </thead>
              <tbody>
                {constituents.slice(0, 50).map((item) => (
                  <tr key={item.symbol} className="border-b border-[var(--color-border)] last:border-0">
                    <td className="py-2">
                      <Link
                        href={`/stocks/${item.symbol}`}
                        className="font-mono font-semibold text-[var(--color-primary)] hover:underline"
                      >
                        {item.symbol}
                      </Link>
                    </td>
                    <td className="py-2 text-[var(--color-text-primary)]">{item.name}</td>
                    <td className="py-2 text-[var(--color-text-muted)]">{item.sector ?? "—"}</td>
                    <td className="py-2 text-[var(--color-text-muted)]">{item.asset_class}</td>
                    <td className="py-2">
                      <span
                        className={cn(
                          "inline-flex rounded-full px-2 py-0.5 text-xs font-medium",
                          item.active
                            ? "bg-emerald-50 text-emerald-700"
                            : "bg-gray-100 text-gray-600"
                        )}
                      >
                        {item.active ? "Active" : "Inactive"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {constituents.length > 50 && (
              <p className="mt-3 text-xs text-[var(--color-text-muted)]">
                Showing 50 of {constituents.length} constituents
              </p>
            )}
          </div>
        </Card>
      </div>
    </NewDashboardShell>
  );
}
