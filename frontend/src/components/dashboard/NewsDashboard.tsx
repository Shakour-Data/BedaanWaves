"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { apiClient, getApiErrorMessage } from "@/lib/api";
import { cn } from "@/lib/cn";
import type { NewsDashboardResponse } from "@/lib/api/dashboard";
import { useUXStore } from "@/store/useUXStore";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { BarChart } from "@/components/charts/BarChart";

function SentimentBadge({ positive, negative, neutral }: { positive: number; negative: number; neutral: number }) {
  const total = positive + negative + neutral || 1;
  const posPct = (positive / total) * 100;
  const negPct = (negative / total) * 100;
  const neuPct = (neutral / total) * 100;

  return (
    <div className="flex items-center gap-2">
      <div className="h-2 w-24 rounded-full bg-[var(--color-border)] overflow-hidden flex">
        <div className="h-full bg-[var(--color-success)]" style={{ width: `${posPct}%` }} />
        <div className="h-full bg-[var(--color-warning)]" style={{ width: `${neuPct}%` }} />
        <div className="h-full bg-[var(--color-error)]" style={{ width: `${negPct}%` }} />
      </div>
      <span className="text-xs text-[var(--color-text-secondary)]">
        {positive}/{negative}/{neutral}
      </span>
    </div>
  );
}

export function NewsDashboard() {
  const [data, setData] = useState<NewsDashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const addToast = useUXStore((state) => state.addToast);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.get<NewsDashboardResponse>("/analysis/dashboard/news", { timeout: 120000 });
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
    return data.symbols.slice(0, 20).map((s) => ({
      time: s.symbol,
      value: s.avg_sentiment,
      color: s.avg_sentiment > 0.5 ? "#10B981" : s.avg_sentiment < -0.5 ? "#EF4444" : "#F59E0B",
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
        <h1 className="text-3xl font-bold text-[var(--color-text-primary)]">News Dashboard</h1>
        <p className="mt-1 text-[var(--color-text-secondary)]">
          News sentiment analysis for {data.summary.total_symbols.toLocaleString()} symbols
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-4">
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
          <p className="text-sm font-medium text-[var(--color-text-secondary)]">Avg Sentiment</p>
          <p className="mt-2 text-3xl font-bold text-[var(--color-text-primary)]">
            {data.summary.avg_score.toFixed(1)}
          </p>
        </div>
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
          <p className="text-sm font-medium text-[var(--color-text-secondary)]">Total News</p>
          <p className="mt-2 text-3xl font-bold text-[var(--color-text-primary)]">
            {data.summary.total_news.toLocaleString()}
          </p>
        </div>
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
          <p className="text-sm font-medium text-[var(--color-text-secondary)]">Most Positive</p>
          <p className="mt-2 text-3xl font-bold text-[var(--color-success)]">
            {data.summary.best_symbol || "—"}
          </p>
          <p className="text-sm text-[var(--color-text-secondary)]">
            Score: {data.summary.best_score.toFixed(1)}
          </p>
        </div>
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
          <p className="text-sm font-medium text-[var(--color-text-secondary)]">Most Negative</p>
          <p className="mt-2 text-3xl font-bold text-[var(--color-error)]">
            {data.summary.worst_symbol || "—"}
          </p>
          <p className="text-sm text-[var(--color-text-secondary)]">
            Score: {data.summary.worst_score.toFixed(1)}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-[var(--color-text-primary)] mb-4">
            Sentiment by Symbol (Top 20)
          </h2>
          <BarChart data={chartData} height={300} />
        </div>
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-[var(--color-text-primary)] mb-4">Top Positive</h2>
          <div className="space-y-2">
            {data.top_performers.slice(0, 5).map((s, i) => (
              <Link
                key={s.symbol}
                href={`/stocks/${s.symbol}`}
                className="flex items-center justify-between rounded-lg p-3 hover:bg-[var(--color-background)]"
              >
                <div className="flex items-center gap-3">
                  <span className="text-sm font-bold text-[var(--color-text-secondary)]">#{i + 1}</span>
                  <span className="font-semibold text-[var(--color-text-primary)]">{s.symbol}</span>
                  <span className="text-xs text-[var(--color-text-secondary)]">{s.name}</span>
                </div>
                <span className="text-sm font-medium text-[var(--color-success)]">+{s.score.toFixed(1)}</span>
              </Link>
            ))}
          </div>
        </div>
      </div>

      <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] shadow-sm overflow-hidden">
        <div className="p-6 border-b border-[var(--color-border)]">
          <h2 className="text-xl font-semibold text-[var(--color-text-primary)]">All Symbols News Sentiment</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-[var(--color-background)]">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-[var(--color-text-secondary)] uppercase tracking-wider">Symbol</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-[var(--color-text-secondary)] uppercase tracking-wider">Name</th>
                <th className="px-6 py-3 text-center text-xs font-medium text-[var(--color-text-secondary)] uppercase tracking-wider">Sentiment</th>
                <th className="px-6 py-3 text-center text-xs font-medium text-[var(--color-text-secondary)] uppercase tracking-wider">Pos / Neg / Neu</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-[var(--color-text-secondary)] uppercase tracking-wider">News Count</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-[var(--color-text-secondary)] uppercase tracking-wider">Latest News</th>
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
                  <td className="px-6 py-4 whitespace-nowrap text-center">
                    <span className={cn(
                      "px-2 py-1 rounded text-xs font-bold",
                      s.score >= 0.5 ? "bg-[var(--color-success)]/20 text-[var(--color-success)]" :
                      s.score <= -0.5 ? "bg-[var(--color-error)]/20 text-[var(--color-error)]" :
                      "bg-[var(--color-warning)]/20 text-[var(--color-warning)]"
                    )}>
                      {s.score.toFixed(2)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <SentimentBadge positive={s.positive_count} negative={s.negative_count} neutral={s.neutral_count} />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-[var(--color-text-secondary)]">
                    {s.news_count}
                  </td>
                  <td className="px-6 py-4 text-xs text-[var(--color-text-secondary)] max-w-xs truncate">
                    {s.latest_news?.title || "—"}
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
