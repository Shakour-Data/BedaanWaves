"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { Trophy, TrendingUp, ArrowUpRight } from "lucide-react";
import { fetchTopPerformers, type LeaderboardResponse, type Level } from "@/lib/api/dashboard";
import { LevelSelector } from "@/components/leaderboard/LevelSelector";
import { LeaderboardCard } from "@/components/leaderboard/LeaderboardCard";
import { StockDetailSkeleton } from "@/components/ux/SkeletonLoaders";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { useUXStore } from "@/store/useUXStore";
import { NewDashboardShell } from "@/components/layout/NewDashboardShell";

const LEVEL_LABELS: Record<Level, string> = {
  overall: "Overall Top Performers",
  dimension: "Top Performers by Dimension",
  sub_dimension: "Top Performers by Sub-Dimension",
  aspect: "Top Performers by Aspect",
  sub_aspect: "Top Performers by Sub-Aspect",
};

const LEVEL_DESCRIPTIONS: Record<Level, string> = {
  overall: "Highest-scoring NASDAQ equities and ETFs across all dimensions",
  dimension: "Top assets ranked by a specific dimension score",
  sub_dimension: "Top assets ranked by a specific sub-dimension score",
  aspect: "Top assets ranked by a specific aspect score",
  sub_aspect: "Top assets ranked by a specific sub-aspect score",
};

export default function LeaderboardPage() {
  const addToast = useUXStore((state) => state.addToast);

  const [level, setLevel] = useState<Level>("overall");
  const [dimension, setDimension] = useState<string>("fundamental");
  const [limit, setLimit] = useState(10);
  const [data, setData] = useState<LeaderboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchTopPerformers({ level, dimension, limit });
      setData(result);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to load leaderboard";
      setError(message);
      addToast({ type: "error", message });
    } finally {
      setLoading(false);
    }
  }, [level, dimension, limit, addToast]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadData();
  }, [loadData]);

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
          actions={[{ label: "Retry", onAction: () => { setError(null); loadData(); } }]}
          moreHelpSteps={["Check your internet connection", "Verify the API service is running"]}
          helpTitle="Troubleshooting steps"
        />
      </div>
    );
  }

  return (
    <NewDashboardShell title="Leaderboard">
      <div className="space-y-6 animate-in fade-in duration-300">
      <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
        <div className="mb-6 flex items-start justify-between">
          <div>
            <div className="mb-2 flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--color-warning)]/15 text-[var(--color-warning)]">
                <Trophy className="h-5 w-5" />
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

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">
                  {level === "overall" ? "Top 10 Overall" : `Top ${limit} ${dimension}`}
                </h2>
                {data?.latest_date && (
                  <p className="text-xs text-[var(--color-text-secondary)] mt-1">
                    Latest data: {new Date(data.latest_date).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
                  </p>
                )}
              </div>
              <div className="text-right">
                <p className="text-xs text-[var(--color-text-secondary)]">
                  {data?.total_universe ?? 0} assets in universe
                </p>
              </div>
            </div>

            <LeaderboardCard
              entries={(data?.entries ?? []).map((entry, idx) => ({
                ...entry,
                rank: idx + 1,
              }))}
              showDimensions={level !== "overall"}
            />
          </div>
        </div>

        <div className="space-y-4">
          <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
            <h3 className="mb-3 text-sm font-semibold text-[var(--color-text-primary)]">About This Leaderboard</h3>
            <div className="space-y-3 text-xs text-[var(--color-text-secondary)]">
              <p>
                Scores are computed from real market data across fundamental, technical, sentiment, risk, macro, and AI dimensions.
              </p>
              <p>
                Each asset receives a score from 0–100. Grades reflect the overall quality:
              </p>
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <span>A+/A/A-</span>
                  <span className="rounded bg-[var(--color-success)]/15 px-2 py-0.5 text-[10px] font-medium text-[var(--color-success)]">Strong (80+)</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>B+/B/B-</span>
                  <span className="rounded bg-[var(--color-primary)]/15 px-2 py-0.5 text-[10px] font-medium text-[var(--color-primary)]">Good (50–79)</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>C+/C/C-</span>
                  <span className="rounded bg-[var(--color-warning)]/15 px-2 py-0.5 text-[10px] font-medium text-[var(--color-warning)]">Neutral</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>D/F</span>
                  <span className="rounded bg-[var(--color-error)]/15 px-2 py-0.5 text-[10px] font-medium text-[var(--color-error)]">Weak (&lt;50)</span>
                </div>
              </div>
            </div>
          </div>

          <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
            <h3 className="mb-3 text-sm font-semibold text-[var(--color-text-primary)]">Quick Links</h3>
            <div className="space-y-2">
              <Link
                href="/movers"
                className="flex items-center gap-2 rounded-lg p-2 text-sm text-[var(--color-text-secondary)] transition-colors hover:bg-[var(--color-background)] hover:text-[var(--color-text-primary)]"
              >
                <TrendingUp className="h-4 w-4" />
                Biggest Movers
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
