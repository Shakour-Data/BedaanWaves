"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { apiClient, getApiErrorMessage } from "@/lib/api";
import { cn } from "@/lib/cn";
import type { AiDashboardResponse } from "@/lib/api/dashboard";
import { useUXStore } from "@/store/useUXStore";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { ScoreTrendChart } from "@/components/charts/ScoreTrendChart";

export function AiDashboard() {
  const [data, setData] = useState<AiDashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const addToast = useUXStore((state) => state.addToast);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.get<AiDashboardResponse>("/analysis/dashboard/ai", { timeout: 120000 });
      setData(res.data);
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
  }, []);

  const chartData = useMemo(() => {
    if (!data) return [];
    return data.top_performers.slice(0, 10).map((p) => ({
      time: p.symbol,
      value: p.score,
    }));
  }, [data]);

  const confidenceData = useMemo(() => {
    if (!data) return [];
    return data.symbols
      .filter((s) => s.confidence > 0)
      .slice(0, 15)
      .map((s) => ({
        time: s.symbol,
        value: s.confidence,
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
        <h1 className="text-3xl font-bold text-[var(--color-text-primary)]">AI Dashboard</h1>
        <p className="mt-1 text-[var(--color-text-secondary)]">
          ML predictions for {data.summary.total_symbols.toLocaleString()} symbols
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-4">
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
          <p className="text-sm font-medium text-[var(--color-text-secondary)]">Avg AI Score</p>
          <p className="mt-2 text-3xl font-bold text-[var(--color-text-primary)]">
            {data.summary.avg_score.toFixed(1)}
          </p>
        </div>
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
          <p className="text-sm font-medium text-[var(--color-text-secondary)]">Best Prediction</p>
          <p className="mt-2 text-3xl font-bold text-[var(--color-success)]">
            {data.summary.best_symbol || "—"}
          </p>
          <p className="text-sm text-[var(--color-text-secondary)]">
            Score: {data.summary.best_score.toFixed(1)}
          </p>
        </div>
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
          <p className="text-sm font-medium text-[var(--color-text-secondary)]">Worst Prediction</p>
          <p className="mt-2 text-3xl font-bold text-[var(--color-error)]">
            {data.summary.worst_symbol || "—"}
          </p>
          <p className="text-sm text-[var(--color-text-secondary)]">
            Score: {data.summary.worst_score.toFixed(1)}
          </p>
        </div>
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
          <p className="text-sm font-medium text-[var(--color-text-secondary)]">Scored Symbols</p>
          <p className="mt-2 text-3xl font-bold text-[var(--color-text-primary)]">
            {data.summary.total_signals.toLocaleString()}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-[var(--color-text-primary)] mb-4">Top 10 AI Scores</h2>
          <ScoreTrendChart
            series={[
              {
                key: "score",
                label: "AI Score",
                color: "#2563EB",
                data: chartData,
              },
            ]}
            height={300}
          />
        </div>
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-[var(--color-text-primary)] mb-4">AI Confidence</h2>
          <ScoreTrendChart
            series={[
              {
                key: "confidence",
                label: "Confidence %",
                color: "#10B981",
                data: confidenceData,
              },
            ]}
            height={300}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-[var(--color-text-primary)] mb-4">Top Performers</h2>
          <div className="space-y-2">
            {data.top_performers.slice(0, 5).map((s, i) => (
              <Link
                key={s.symbol}
                href={`/stocks/${s.symbol}`}
                className="flex items-center justify-between rounded-lg p-3 hover:bg-[var(--color-background)]"
              >
                <div className="flex items-center gap-3">
                  <span className="text-sm font-bold text-[var(--color-text-secondary)]">#{i + 1}</span>
                  <div>
                    <span className="font-semibold text-[var(--color-text-primary)]">{s.symbol}</span>
                    <span className="text-xs text-[var(--color-text-secondary)] ml-2">{s.name}</span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-[var(--color-text-secondary)]">
                    {s.confidence > 0 ? `${s.confidence.toFixed(0)}%` : "—"}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        </div>
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-[var(--color-text-primary)] mb-4">Bottom Performers</h2>
          <div className="space-y-2">
            {data.bottom_performers.slice(0, 5).map((s, i) => (
              <Link
                key={s.symbol}
                href={`/stocks/${s.symbol}`}
                className="flex items-center justify-between rounded-lg p-3 hover:bg-[var(--color-background)]"
              >
                <div className="flex items-center gap-3">
                  <span className="text-sm font-bold text-[var(--color-text-secondary)]">#{i + 1}</span>
                  <div>
                    <span className="font-semibold text-[var(--color-text-primary)]">{s.symbol}</span>
                    <span className="text-xs text-[var(--color-text-secondary)] ml-2">{s.name}</span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-[var(--color-text-secondary)]">
                    {s.confidence > 0 ? `${s.confidence.toFixed(0)}%` : "—"}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </div>

      <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] shadow-sm overflow-hidden">
        <div className="p-6 border-b border-[var(--color-border)]">
          <h2 className="text-xl font-semibold text-[var(--color-text-primary)]">All AI Scores</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-[var(--color-background)]">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-[var(--color-text-secondary)] uppercase tracking-wider">Symbol</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-[var(--color-text-secondary)] uppercase tracking-wider">Name</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-[var(--color-text-secondary)] uppercase tracking-wider">AI Score</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-[var(--color-text-secondary)] uppercase tracking-wider">Confidence</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-[var(--color-text-secondary)] uppercase tracking-wider">Expected Return</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-[var(--color-text-secondary)] uppercase tracking-wider">Risk Score</th>
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
                  <td className="px-6 py-4 whitespace-nowrap text-right">
                    <span className={cn(
                      "px-2 py-1 rounded text-xs font-bold",
                      s.score >= 70 ? "bg-[var(--color-success)]/20 text-[var(--color-success)]" :
                      s.score >= 40 ? "bg-[var(--color-warning)]/20 text-[var(--color-warning)]" :
                      "bg-[var(--color-error)]/20 text-[var(--color-error)]"
                    )}>
                      {s.score.toFixed(1)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-[var(--color-text-secondary)]">
                    {s.confidence.toFixed(0)}%
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-[var(--color-text-secondary)]">
                    {(s.expected_return * 100).toFixed(2)}%
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-[var(--color-text-secondary)]">
                    {s.risk_score.toFixed(1)}
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
