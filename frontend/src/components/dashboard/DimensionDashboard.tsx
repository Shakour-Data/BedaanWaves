"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { apiClient, getApiErrorMessage } from "@/lib/api";
import { cn } from "@/lib/cn";
import type { DimensionDashboardResponse } from "@/lib/api/dashboard";
import { SUB_DIMENSIONS } from "@/lib/api/scoring";
import { useUXStore } from "@/store/useUXStore";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { SpiderChart } from "@/components/charts/SpiderChart";
import { ScoreTrendChart } from "@/components/charts/ScoreTrendChart";

interface DimensionDashboardProps {
  dimension: string;
  fetchFn: () => Promise<DimensionDashboardResponse>;
  color: string;
  activeSub?: string | null;
  onSubChange: (sub: string | null) => void;
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

function SubDimensionCard({
  subInfo,
  subStats,
  color,
}: {
  subInfo: { key: string; label: string; weight: number };
  subStats: {
    avgScore: number;
    distribution: Array<{ range: string; count: number; color: string }>;
    topPerformers: Array<{ symbol: string; name: string; score: number; grade: string; link: string }>;
    bottomPerformers: Array<{ symbol: string; name: string; score: number; grade: string; link: string }>;
  };
  color: string;
}) {
  const maxDist = Math.max(...subStats.distribution.map((d) => d.count));
  const subPerformersChartData = subStats.topPerformers.slice(0, 10).map((p) => ({
    time: p.symbol,
    value: p.score,
  }));

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      <div className="mb-6">
        <div className="flex items-center gap-3">
          <span className="h-2 w-2 rounded-full" style={{ backgroundColor: color }} />
          <h2 className="text-2xl font-bold text-[var(--color-text-primary)]">{subInfo.label}</h2>
        </div>
        <p className="mt-1 text-[var(--color-text-secondary)]">
          Average: {subStats.avgScore.toFixed(1)} &bull; Weight: {(subInfo.weight * 100).toFixed(0)}%
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
          <p className="text-sm font-medium text-[var(--color-text-secondary)]">Avg Score</p>
          <p className="mt-2 text-3xl font-bold" style={{ color }}>{subStats.avgScore.toFixed(1)}</p>
        </div>
        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
          <p className="text-sm font-medium text-[var(--color-text-secondary)]">Best Symbol</p>
          <p className="mt-2 text-2xl font-bold text-[var(--color-success)]">
            {subStats.topPerformers[0]?.symbol || "—"}
          </p>
          <p className="text-sm text-[var(--color-text-secondary)]">
            Score: {subStats.topPerformers[0]?.score.toFixed(1) ?? "—"}
          </p>
        </div>
        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
          <p className="text-sm font-medium text-[var(--color-text-secondary)]">Worst Symbol</p>
          <p className="mt-2 text-2xl font-bold text-[var(--color-error)]">
            {subStats.bottomPerformers[0]?.symbol || "—"}
          </p>
          <p className="text-sm text-[var(--color-text-secondary)]">
            Score: {subStats.bottomPerformers[0]?.score.toFixed(1) ?? "—"}
          </p>
        </div>
        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
          <p className="text-sm font-medium text-[var(--color-text-secondary)]">Symbols Scored</p>
          <p className="mt-2 text-3xl font-bold text-[var(--color-text-primary)]">
            {subStats.topPerformers.length + subStats.bottomPerformers.length}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-4">Score Distribution</h3>
          <div className="space-y-3">
            {subStats.distribution.map((bin) => (
              <div key={bin.range} className="flex items-center gap-3 group">
                <span className="w-16 text-xs text-[var(--color-text-secondary)] shrink-0">{bin.range}</span>
                <div className="relative flex-1 h-7 rounded bg-[var(--color-background)] overflow-hidden">
                  <div
                    className="h-full rounded transition-all group-hover:brightness-110"
                    style={{
                      width: `${Math.max((bin.count / Math.max(maxDist, 1)) * 100, 2)}%`,
                      backgroundColor: bin.color,
                    }}
                  />
                  <span className="absolute inset-0 flex items-center justify-end pr-2 text-xs font-medium text-[var(--color-text-primary)] opacity-0 group-hover:opacity-100 transition-opacity">
                    {bin.count}
                  </span>
                </div>
                <span className="w-8 text-xs text-[var(--color-text-secondary)] text-right shrink-0">{bin.count}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-4">
            Top 10 &mdash; {subInfo.label}
          </h3>
          <ScoreTrendChart
            series={[
              {
                key: "score",
                label: "Score",
                color: color,
                data: subPerformersChartData,
              },
            ]}
            height={300}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-4">Top Performers</h3>
          <div className="space-y-2">
            {subStats.topPerformers.map((stock, i) => (
              <Link
                key={stock.symbol}
                href={stock.link}
                className="flex items-center justify-between rounded-lg p-3 transition-all hover:bg-[var(--color-background)]"
              >
                <div className="flex items-center gap-3">
                  <span className="text-sm font-bold text-[var(--color-text-secondary)] w-6">#{i + 1}</span>
                  <span className="font-semibold text-[var(--color-text-primary)]">{stock.symbol}</span>
                </div>
                <ScoreBadge score={stock.score} />
              </Link>
            ))}
          </div>
        </div>

        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-4">Bottom Performers</h3>
          <div className="space-y-2">
            {subStats.bottomPerformers.map((stock, i) => (
              <Link
                key={stock.symbol}
                href={stock.link}
                className="flex items-center justify-between rounded-lg p-3 transition-all hover:bg-[var(--color-background)]"
              >
                <div className="flex items-center gap-3">
                  <span className="text-sm font-bold text-[var(--color-text-secondary)] w-6">#{i + 1}</span>
                  <span className="font-semibold text-[var(--color-text-primary)]">{stock.symbol}</span>
                </div>
                <ScoreBadge score={stock.score} />
              </Link>
            ))}
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-sm overflow-hidden">
        <div className="p-6 border-b border-[var(--color-border)]">
          <h3 className="text-lg font-semibold text-[var(--color-text-primary)]">
            All {subInfo.label} Scores
          </h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-[var(--color-background)]">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-[var(--color-text-secondary)] uppercase">Rank</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-[var(--color-text-secondary)] uppercase">Symbol</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-[var(--color-text-secondary)] uppercase">Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-[var(--color-text-secondary)] uppercase">Sector</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-[var(--color-text-secondary)] uppercase">Score</th>
                <th className="px-6 py-3 text-center text-xs font-medium text-[var(--color-text-secondary)] uppercase">Grade</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--color-border)]">
              {[...subStats.topPerformers, ...subStats.bottomPerformers].reduce(
                (acc, s) => (acc.some((a) => a.symbol === s.symbol) ? acc : [...acc, s]),
                [] as typeof subStats.topPerformers
              ).sort((a, b) => b.score - a.score).map((s, idx) => (
                <tr key={s.symbol} className="hover:bg-[var(--color-background)]">
                  <td className="px-6 py-4 whitespace-nowrap text-[var(--color-text-secondary)]">{idx + 1}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <Link href={s.link} className="font-semibold text-[var(--color-primary)] hover:underline">
                      {s.symbol}
                    </Link>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-[var(--color-text-primary)]">{s.name}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-[var(--color-text-secondary)]">—</td>
                  <td className="px-6 py-4 whitespace-nowrap text-right">
                    <ScoreBadge score={s.score} />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center text-xs text-[var(--color-text-secondary)]">
                    {s.grade || "—"}
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

export function DimensionDashboard({ dimension, fetchFn, color, activeSub, onSubChange }: DimensionDashboardProps) {
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

  const subDimensions = useMemo(() => {
    const subs = SUB_DIMENSIONS[dimension];
    if (!subs || subs.length === 0) return [];
    if (!data) return subs;
    return subs
      .filter((s) => data.symbols.some((sym) => s.key in sym.sub_dimensions))
      .map((s) => {
        const scores = data.symbols
          .map((sym) => sym.sub_dimensions[s.key])
          .filter((v): v is number => typeof v === "number");
        const avg = scores.length > 0 ? scores.reduce((a, b) => a + b, 0) / scores.length : 0;
        return { key: s.key, label: s.label, weight: s.weight, avgScore: avg };
      });
  }, [dimension, data]);

  const currentSubInfo = activeSub ? subDimensions.find((s) => s.key === activeSub) : null;

  function getSubDimensionStats(subKey: string) {
    if (!data) return null;
    const scores = data.symbols
      .map((sym) => sym.sub_dimensions[subKey])
      .filter((v): v is number => typeof v === "number");
    if (scores.length === 0) return null;

    const bins = [
      { range: "0-20", count: 0, color: "#EF4444" },
      { range: "20-40", count: 0, color: "#F59E0B" },
      { range: "40-60", count: 0, color: "#F59E0B" },
      { range: "60-80", count: 0, color: "#10B981" },
      { range: "80-100", count: 0, color: "#10B981" },
    ];
    for (const s of scores) {
      const idx = Math.min(Math.floor(s / 20), 4);
      bins[idx].count++;
    }

    const ranked = data.symbols
      .map((sym) => ({
        symbol: sym.symbol,
        name: sym.name,
        score: sym.sub_dimensions[subKey] ?? 0,
        grade: sym.grade,
        sector: sym.sector || "—",
        link: `/stocks/${sym.symbol}/scoring`,
      }))
      .sort((a, b) => b.score - a.score);

    const uniqueRanked = ranked.filter(
      (v, i, a) => a.findIndex((t) => t.symbol === v.symbol) === i
    );

    return {
      avgScore: scores.reduce((a, b) => a + b, 0) / scores.length,
      distribution: bins,
      topPerformers: uniqueRanked.slice(0, 10),
      bottomPerformers: [...uniqueRanked].reverse().slice(0, 10),
    };
  }

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

  const renderOverview = () => (
    <div className="space-y-6">
      <div className="grid gap-6 md:grid-cols-4">
        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
          <p className="text-sm font-medium text-[var(--color-text-secondary)]">Average Score</p>
          <p className="mt-2 text-3xl font-bold text-[var(--color-text-primary)]">
            {data.summary.avg_score.toFixed(1)}
          </p>
        </div>
        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
          <p className="text-sm font-medium text-[var(--color-text-secondary)]">Best Symbol</p>
          <p className="mt-2 text-3xl font-bold text-[var(--color-success)]">
            {data.summary.best_symbol || "—"}
          </p>
          <p className="text-sm text-[var(--color-text-secondary)]">
            Score: {data.summary.best_score.toFixed(1)}
          </p>
        </div>
        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
          <p className="text-sm font-medium text-[var(--color-text-secondary)]">Worst Symbol</p>
          <p className="mt-2 text-3xl font-bold text-[var(--color-error)]">
            {data.summary.worst_symbol || "—"}
          </p>
          <p className="text-sm text-[var(--color-text-secondary)]">
            Score: {data.summary.worst_score.toFixed(1)}
          </p>
        </div>
        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
          <p className="text-sm font-medium text-[var(--color-text-secondary)]">Total Symbols</p>
          <p className="mt-2 text-3xl font-bold text-[var(--color-text-primary)]">
            {data.summary.total_symbols.toLocaleString()}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-[var(--color-text-primary)] mb-4">
            Score Distribution
          </h2>
          <div className="space-y-3">
            {distributionChartData.map((item, i) => (
              <div key={i} className="flex items-center gap-3 group">
                <span className="w-16 text-xs text-[var(--color-text-secondary)] shrink-0">{item.range}</span>
                <div className="relative flex-1 h-7 rounded bg-[var(--color-background)] overflow-hidden">
                  <div
                    className="h-full rounded transition-all group-hover:brightness-110"
                    style={{
                      width: `${Math.max((item.count / Math.max(...distributionChartData.map((d) => d.count), 1)) * 100, 2)}%`,
                      backgroundColor: item.color,
                    }}
                  />
                  <span className="absolute inset-0 flex items-center justify-end pr-2 text-xs font-medium text-[var(--color-text-primary)] opacity-0 group-hover:opacity-100 transition-opacity">
                    {item.count}
                  </span>
                </div>
                <span className="w-8 text-xs text-[var(--color-text-secondary)] text-right shrink-0">{item.count}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
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

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
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

        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
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

      <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-sm overflow-hidden">
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

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      <div className="mb-8 pb-4 border-b border-[var(--color-border)]">
        <div className="flex items-center gap-3">
          <span
            className="h-3 w-3 rounded-full"
            style={{ backgroundColor: color }}
          />
          <h1 className="text-3xl font-bold text-[var(--color-text-primary)] capitalize">
            {dimension} Dashboard
          </h1>
        </div>
        <p className="mt-1 text-[var(--color-text-secondary)]">
          {data.summary.total_symbols.toLocaleString()} symbols analyzed
        </p>
      </div>

      {subDimensions.length > 0 && (
        <div className="sticky z-20">
          <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-thin scrollbar-thumb-[var(--color-border)]">
            <button
              onClick={() => onSubChange(null)}
              className={cn(
                "shrink-0 rounded-lg px-4 py-2.5 text-sm font-medium whitespace-nowrap transition-all",
                !activeSub
                  ? "bg-[var(--color-surface)] text-[var(--color-text-primary)] shadow ring-1 ring-[var(--color-primary)]/20"
                  : "text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-border)]"
              )}
            >
              Overview
            </button>
            {subDimensions.map((sub) => {
              const isActive = activeSub === sub.key;
              return (
                <button
                  key={sub.key}
                  onClick={() => onSubChange(sub.key)}
                  className={cn(
                    "shrink-0 rounded-lg px-4 py-2.5 text-sm font-medium whitespace-nowrap transition-all",
                    isActive
                      ? "text-white shadow"
                      : "text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-border)]"
                  )}
                  style={isActive ? { backgroundColor: color } : undefined}
                >
                  {sub.label}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {currentSubInfo && getSubDimensionStats(activeSub!) ? (
        <SubDimensionCard
          subInfo={currentSubInfo}
          subStats={getSubDimensionStats(activeSub!)!}
          color={color}
        />
      ) : (
        renderOverview()
      )}
    </div>
  );
}
