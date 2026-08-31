"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { apiClient, getApiErrorMessage } from "@/lib/api";
import { cn } from "@/lib/cn";
import type { DimensionDashboardResponse } from "@/lib/api/dashboard";
import { useUXStore } from "@/store/useUXStore";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { SpiderChart } from "@/components/charts/SpiderChart";
import { ScoreTrendChart } from "@/components/charts/ScoreTrendChart";

interface DimensionDashboardProps {
  dimension: string;
  fetchFn: () => Promise<DimensionDashboardResponse>;
  color: string;
}

function ScoreBadge({ score }: { score: number }) {
  let colorClass = "bg-[var(--color-success)]/20 text-[var(--color-success)]";
  if (score < 40) colorClass = "bg-[var(--color-error)]/20 text-[var(--color-error)]";
  else if (score < 60) colorClass = "bg-[var(--color-warning)]/20 text-[var(--color-warning)]";

  return (
    <span className={cn("px-2 py-1 rounded text-xs font-bold", colorClass)}>
      {score.toFixed(1)}
    </span>
  );
}

export function DimensionDashboard({ dimension, fetchFn, color }: DimensionDashboardProps) {
  const [data, setData] = useState<DimensionDashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const addToast = useUXStore((state) => state.addToast);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchFn();
      setData(result);
    } catch (err) {
      const message = getApiErrorMessage(err);
      setError(message);
      addToast({ type: "error", message });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [fetchFn]);

  const distributionChartData = useMemo(() => {
    if (!data) return [];
    return data.distribution.map((d, i) => ({
      range: d.range,
      count: d.count,
      color: i >= 7 ? "#EF4444" : i >= 4 ? "#F59E0B" : "#10B981",
    }));
  }, [data]);

  const topPerformersChartData = useMemo(() => {
    if (!data) return [];
    return data.top_performers.slice(0, 10).map((p) => ({
      time: p.symbol,
      value: p.score,
    }));
  }, [data]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-[var(--color-primary)] border-t-transparent" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-20 gap-4">
        <ErrorMessage message={error} />
        <button
          onClick={loadData}
          className="rounded-lg bg-[var(--color-primary)] px-4 py-2 text-sm font-medium text-white hover:opacity-90"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-[var(--color-text-primary)] capitalize">{dimension} Dashboard</h1>
        <p className="mt-1 text-[var(--color-text-secondary)]">
          {data.summary.total_symbols.toLocaleString()} symbols analyzed
        </p>
      </div>

      {/* Summary Stats */}
      <div className="grid gap-6 md:grid-cols-4">
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
          <p className="text-sm font-medium text-[var(--color-text-secondary)]">Average Score</p>
          <p className="mt-2 text-3xl font-bold text-[var(--color-text-primary)]">
            {data.summary.avg_score.toFixed(1)}
          </p>
        </div>
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
          <p className="text-sm font-medium text-[var(--color-text-secondary)]">Best Symbol</p>
          <p className="mt-2 text-3xl font-bold text-[var(--color-success)]">
            {data.summary.best_symbol || "—"}
          </p>
          <p className="text-sm text-[var(--color-text-secondary)]">
            Score: {data.summary.best_score.toFixed(1)}
          </p>
        </div>
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
          <p className="text-sm font-medium text-[var(--color-text-secondary)]">Worst Symbol</p>
          <p className="mt-2 text-3xl font-bold text-[var(--color-error)]">
            {data.summary.worst_symbol || "—"}
          </p>
          <p className="text-sm text-[var(--color-text-secondary)]">
            Score: {data.summary.worst_score.toFixed(1)}
          </p>
        </div>
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
          <p className="text-sm font-medium text-[var(--color-text-secondary)]">Total Symbols</p>
          <p className="mt-2 text-3xl font-bold text-[var(--color-text-primary)]">
            {data.summary.total_symbols.toLocaleString()}
          </p>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-[var(--color-text-primary)] mb-4">
            Score Distribution
          </h2>
          <div className="space-y-2">
            {distributionChartData.map((item, i) => (
              <div key={i} className="flex items-center gap-3">
                <span className="w-16 text-xs text-[var(--color-text-secondary)] shrink-0">{item.range}</span>
                <div className="flex-1 h-6 rounded bg-[var(--color-background)] overflow-hidden">
                  <div
                    className="h-full rounded"
                    style={{
                      width: `${Math.max((item.count / Math.max(...distributionChartData.map(d => d.count))) * 100, 2)}%`,
                      backgroundColor: item.color,
                    }}
                  />
                </div>
                <span className="w-8 text-xs text-[var(--color-text-secondary)] text-right shrink-0">{item.count}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-[var(--color-text-primary)] mb-4">
            Top 10 Performers
          </h2>
          <ScoreTrendChart
            series={[
              {
                key: "score",
                label: "Score",
                color: color,
                data: topPerformersChartData,
              },
            ]}
            height={300}
          />
        </div>
      </div>

      {/* Top / Bottom Performers */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-[var(--color-text-primary)] mb-4">Top Performers</h2>
          <div className="space-y-2">
            {data.top_performers.map((stock, i) => (
              <Link
                key={stock.symbol}
                href={`/stocks/${stock.symbol}`}
                className="flex items-center justify-between rounded-lg p-3 transition-all hover:bg-[var(--color-background)]"
              >
                <div className="flex items-center gap-3">
                  <span className="text-sm font-bold text-[var(--color-text-secondary)] w-4">#{i + 1}</span>
                  <div>
                    <span className="font-semibold text-[var(--color-text-primary)]">{stock.symbol}</span>
                    <span className="text-xs text-[var(--color-text-secondary)] ml-2">{stock.name}</span>
                  </div>
                </div>
                <ScoreBadge score={stock.score} />
              </Link>
            ))}
          </div>
        </div>
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-[var(--color-text-primary)] mb-4">Bottom Performers</h2>
          <div className="space-y-2">
            {data.bottom_performers.map((stock, i) => (
              <Link
                key={stock.symbol}
                href={`/stocks/${stock.symbol}`}
                className="flex items-center justify-between rounded-lg p-3 transition-all hover:bg-[var(--color-background)]"
              >
                <div className="flex items-center gap-3">
                  <span className="text-sm font-bold text-[var(--color-text-secondary)] w-4">#{i + 1}</span>
                  <div>
                    <span className="font-semibold text-[var(--color-text-primary)]">{stock.symbol}</span>
                    <span className="text-xs text-[var(--color-text-secondary)] ml-2">{stock.name}</span>
                  </div>
                </div>
                <ScoreBadge score={stock.score} />
              </Link>
            ))}
          </div>
        </div>
      </div>

      {/* Symbols Table */}
      <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] shadow-sm overflow-hidden">
        <div className="p-6 border-b border-[var(--color-border)]">
          <h2 className="text-xl font-semibold text-[var(--color-text-primary)]">
            All {dimension.charAt(0).toUpperCase() + dimension.slice(1)} Scores
          </h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-[var(--color-background)]">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-[var(--color-text-secondary)] uppercase tracking-wider">Symbol</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-[var(--color-text-secondary)] uppercase tracking-wider">Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-[var(--color-text-secondary)] uppercase tracking-wider">Sector</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-[var(--color-text-secondary)] uppercase tracking-wider">Score</th>
                <th className="px-6 py-3 text-center text-xs font-medium text-[var(--color-text-secondary)] uppercase tracking-wider">Grade</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-[var(--color-text-secondary)] uppercase tracking-wider">Sub-Dimensions</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-[var(--color-text-secondary)] uppercase tracking-wider">Aspects</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--color-border)]">
              {data.symbols.map((s) => (
                <tr key={s.symbol} className="hover:bg-[var(--color-background)]">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <Link href={`/stocks/${s.symbol}`} className="font-semibold text-[var(--color-primary)] hover:underline">
                      {s.symbol}
                    </Link>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-[var(--color-text-primary)]">{s.name}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-[var(--color-text-secondary)]">{s.sector || "—"}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-right">
                    <ScoreBadge score={s.score} />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center text-xs text-[var(--color-text-secondary)]">
                    {s.grade || "—"}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-xs text-[var(--color-text-secondary)]">
                    {Object.keys(s.sub_dimensions).length} metrics
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-xs text-[var(--color-text-secondary)]">
                    {Object.keys(s.aspects).length} metrics
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
