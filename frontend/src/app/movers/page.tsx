"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { TrendingUp, TrendingDown, ArrowUpRight, Info } from "lucide-react";
import { fetchBiggestMovers, type LeaderboardResponse } from "@/lib/api/dashboard";
import type { Level } from "@/components/leaderboard/LevelSelector";
import { LevelSelector } from "@/components/leaderboard/LevelSelector";
import { LeaderboardCard } from "@/components/leaderboard/LeaderboardCard";
import { StockDetailSkeleton } from "@/components/ux/SkeletonLoaders";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { useUXStore } from "@/store/useUXStore";
import { NewDashboardShell } from "@/components/layout/NewDashboardShell";

const LEVEL_LABELS: Record<Level, string> = {
  overall: "Biggest Movers (Overall)",
  dimension: "Biggest Movers by Dimension",
  sub_dimension: "Biggest Movers by Sub-Dimension",
  aspect: "Biggest Movers by Aspect",
  sub_aspect: "Biggest Movers by Sub-Aspect",
};

const LEVEL_DESCRIPTIONS: Record<Level, string> = {
  overall: "Assets with the largest score changes across all dimensions",
  dimension: "Assets with the largest dimension score changes",
  sub_dimension: "Assets with the largest sub-dimension score changes",
  aspect: "Assets with the largest aspect score changes",
  sub_aspect: "Assets with the largest sub-aspect score changes",
};

const DAYS_OPTIONS = [1, 3, 7, 14, 30];

export default function MoversPage() {
  const addToast = useUXStore((state) => state.addToast);

  const [level, setLevel] = useState<Level>("overall");
  const [dimension, setDimension] = useState<string>("fundamental");
  const [limit, setLimit] = useState(10);
  const [days, setDays] = useState(1);
  const [data, setData] = useState<LeaderboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  /* eslint-disable react-hooks/set-state-in-effect */
  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);

    async function loadData() {
      try {
        const result = await fetchBiggestMovers({ level, dimension, limit, days });
        if (active) {
          setData(result);
        }
      } catch (err) {
        const message = err instanceof Error ? err.message : "Failed to load movers";
        if (active) {
          setError(message);
          addToast({ type: "error", message });
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    loadData();

    return () => {
      active = false;
    };
  }, [level, dimension, limit, days, addToast]);
  /* eslint-enable react-hooks/set-state-in-effect */

  const handleLevelChange = (newLevel: Level) => {
    setLevel(newLevel);
    if (newLevel !== "overall") {
      setDimension("fundamental");
    }
  };

  const handleDimensionChange = (newDimension: string) => {
    setDimension(newDimension);
  };

  if (loading) {
    return <StockDetailSkeleton />;
  }

  if (error) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <ErrorMessage
          message={error}
          actions={[{ label: "Retry", onAction: () => { setError(null); /* trigger reload */ } }]}
          moreHelpSteps={["Check your internet connection", "Verify the API service is running"]}
          helpTitle="Troubleshooting steps"
        />
      </div>
    );
  }

  const entries = (data?.entries ?? []).map((entry, idx) => ({
    ...entry,
    rank: idx + 1,
  }));

  const topPositive = entries.filter((e) => (e.change || 0) > 0).slice(0, 5);
  const topNegative = entries.filter((e) => (e.change || 0) < 0).slice(0, 5);

  return (
    <NewDashboardShell title="Biggest Movers">
      <div className="space-y-6 animate-in fade-in duration-300">
      <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
        <div className="mb-6 flex items-start justify-between">
          <div>
            <div className="mb-2 flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--color-primary)]/15 text-[var(--color-primary)]">
                <TrendingUp className="h-5 w-5" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">
                  {LEVEL_LABELS[level]}
                </h1>
                <p className="text-xs text-[var(--color-text-secondary)]">
                  {LEVEL_DESCRIPTIONS[level]}
                </p>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <select
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
              className="rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] px-3 py-2 text-sm text-[var(--color-text-primary)] focus:border-[var(--color-primary)] focus:outline-none"
            >
              {DAYS_OPTIONS.map((d) => (
                <option key={d} value={d}>
                  {d === 1 ? "1 Day" : `${d} Days`}
                </option>
              ))}
            </select>
            <select
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value))}
              className="rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] px-3 py-2 text-sm text-[var(--color-text-primary)] focus:border-[var(--color-primary)] focus:outline-none"
            >
              <option value={5}>Top 5</option>
              <option value={10}>Top 10</option>
              <option value={20}>Top 20</option>
              <option value={50}>Top 50</option>
            </select>
          </div>
        </div>

        <LevelSelector
          level={level}
          dimension={dimension}
          onLevelChange={handleLevelChange}
          onDimensionChange={handleDimensionChange}
        />
      </div>

      {data?.previous_date && (
        <div className="flex items-center gap-4 text-xs text-[var(--color-text-secondary)]">
          <span>
            Latest date: <span className="font-medium">{data.latest_date}</span>
          </span>
          <span>
            Previous date: <span className="font-medium">{data.previous_date}</span>
          </span>
          <span>
            Window: <span className="font-medium">{days} day{days > 1 ? "s" : ""}</span>
          </span>
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-6">
          <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
            <h2 className="mb-4 text-lg font-semibold text-[var(--color-text-primary)]">
              All Movers ({data?.total_universe ?? 0} assets)
            </h2>
            <LeaderboardCard entries={entries} showChange />
          </div>
        </div>

        <div className="space-y-4">
          <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
            <div className="mb-3 flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-[var(--color-success)]" />
              <h3 className="text-sm font-semibold text-[var(--color-text-primary)]">Top Gainers</h3>
            </div>
            {topPositive.length > 0 ? (
              <div className="space-y-2">
                {topPositive.map((entry) => (
                  <div
                    key={entry.symbol}
                    className="flex items-center justify-between rounded-lg bg-[var(--color-background)] p-2"
                  >
                    <div>
                      <p className="text-sm font-medium text-[var(--color-text-primary)]">{entry.symbol}</p>
                      <p className="text-[10px] text-[var(--color-text-secondary)] truncate max-w-[120px]">{entry.name}</p>
                    </div>
                    <span className="text-sm font-bold text-[var(--color-success)]">
                      +{(entry.change_pct || 0).toFixed(2)}%
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-[var(--color-text-secondary)]">No positive movers found</p>
            )}
          </div>

          <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
            <div className="mb-3 flex items-center gap-2">
              <TrendingDown className="h-4 w-4 text-[var(--color-error)]" />
              <h3 className="text-sm font-semibold text-[var(--color-text-primary)]">Top Decliners</h3>
            </div>
            {topNegative.length > 0 ? (
              <div className="space-y-2">
                {topNegative.map((entry) => (
                  <div
                    key={entry.symbol}
                    className="flex items-center justify-between rounded-lg bg-[var(--color-background)] p-2"
                  >
                    <div>
                      <p className="text-sm font-medium text-[var(--color-text-primary)]">{entry.symbol}</p>
                      <p className="text-[10px] text-[var(--color-text-secondary)] truncate max-w-[120px]">{entry.name}</p>
                    </div>
                    <span className="text-sm font-bold text-[var(--color-error)]">
                      {(entry.change_pct || 0).toFixed(2)}%
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-[var(--color-text-secondary)]">No negative movers found</p>
            )}
          </div>

          <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
            <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-[var(--color-text-primary)]">
              <Info className="h-4 w-4 text-[var(--color-text-secondary)]" />
              About Movers
            </h3>
            <div className="space-y-2 text-xs text-[var(--color-text-secondary)]">
              <p>
                Biggest movers show assets with the largest absolute score changes over the selected period.
              </p>
              <p>
                Positive changes indicate improving scores, while negative changes indicate declining scores.
              </p>
              <p>
                Use the dimension selector to drill down into specific scoring categories.
              </p>
            </div>
          </div>

          <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
            <h3 className="mb-3 text-sm font-semibold text-[var(--color-text-primary)]">Quick Links</h3>
            <div className="space-y-2">
              <Link
                href="/leaderboard"
                className="flex items-center gap-2 rounded-lg p-2 text-sm text-[var(--color-text-secondary)] transition-colors hover:bg-[var(--color-background)] hover:text-[var(--color-text-primary)]"
              >
                <TrendingUp className="h-4 w-4" />
                Leaderboard
              </Link>
              <Link
                href="/stocks"
                className="flex items-center gap-2 rounded-lg p-2 text-sm text-[var(--color-text-secondary)] transition-colors hover:bg-[var(--color-background)] hover:text-[var(--color-text-primary)]"
              >
                <ArrowUpRight className="h-4 w-4" />
                All Stocks
              </Link>
            </div>
          </div>
        </div>
      </div>
      </div>
    </NewDashboardShell>
  );
}
