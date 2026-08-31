"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { apiClient, getApiErrorMessage } from "@/lib/api";
import { cn } from "@/lib/cn";
import type { BoardDashboardResponse } from "@/lib/api/dashboard";
import { useUXStore } from "@/store/useUXStore";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { SpiderChart } from "@/components/charts/SpiderChart";

export function BoardDashboard() {
  const [data, setData] = useState<BoardDashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const addToast = useUXStore((state) => state.addToast);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.get<BoardDashboardResponse>("/analysis/dashboard/board", { timeout: 120000 });
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

  const spiderData = useMemo(() => {
    if (!data) return [];
    const top = data.top_performers[0];
    if (!top) return [];
    const item = data.symbols.find((s) => s.symbol === top.symbol);
    if (!item) return [];
    return [
      { label: "Board Score", value: item.score },
      { label: "Board Members", value: Math.min(item.board_count * 10, 100) },
      { label: "Officers", value: Math.min(item.officer_count * 10, 100) },
      { label: "Total Leaders", value: Math.min(item.total_leaders * 5, 100) },
      { label: "Fundamental", value: item.fundamental_score },
    ];
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
        <h1 className="text-3xl font-bold text-[var(--color-text-primary)]">Board Dashboard</h1>
        <p className="mt-1 text-[var(--color-text-secondary)]">
          Governance and leadership metrics for {data.summary.total_symbols.toLocaleString()} symbols
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-4">
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
          <p className="text-sm font-medium text-[var(--color-text-secondary)]">Avg Board Score</p>
          <p className="mt-2 text-3xl font-bold text-[var(--color-text-primary)]">
            {data.summary.avg_score.toFixed(1)}
          </p>
        </div>
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
          <p className="text-sm font-medium text-[var(--color-text-secondary)]">Best Governed</p>
          <p className="mt-2 text-3xl font-bold text-[var(--color-success)]">
            {data.summary.best_symbol || "—"}
          </p>
          <p className="text-sm text-[var(--color-text-secondary)]">
            Score: {data.summary.best_score.toFixed(1)}
          </p>
        </div>
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
          <p className="text-sm font-medium text-[var(--color-text-secondary)]">Needs Attention</p>
          <p className="mt-2 text-3xl font-bold text-[var(--color-error)]">
            {data.summary.worst_symbol || "—"}
          </p>
          <p className="text-sm text-[var(--color-text-secondary)]">
            Score: {data.summary.worst_score.toFixed(1)}
          </p>
        </div>
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
          <p className="text-sm font-medium text-[var(--color-text-secondary)]">With Board Data</p>
          <p className="mt-2 text-3xl font-bold text-[var(--color-text-primary)]">
            {data.summary.total_boards.toLocaleString()}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-[var(--color-text-primary)] mb-4">
            Best Governed Company Profile
          </h2>
          {spiderData.length > 0 ? (
            <div className="flex justify-center">
              <SpiderChart data={spiderData} size={360} color="#2563EB" />
            </div>
          ) : (
            <p className="text-center text-[var(--color-text-secondary)] py-8">No data available</p>
          )}
        </div>
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
                <span className="text-sm text-[var(--color-text-secondary)]">
                  {s.board_count} board / {s.officer_count} officers
                </span>
              </Link>
            ))}
          </div>
        </div>
      </div>

      <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] shadow-sm overflow-hidden">
        <div className="p-6 border-b border-[var(--color-border)]">
          <h2 className="text-xl font-semibold text-[var(--color-text-primary)]">All Board Scores</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-[var(--color-background)]">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-[var(--color-text-secondary)] uppercase tracking-wider">Symbol</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-[var(--color-text-secondary)] uppercase tracking-wider">Name</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-[var(--color-text-secondary)] uppercase tracking-wider">Board Score</th>
                <th className="px-6 py-3 text-center text-xs font-medium text-[var(--color-text-secondary)] uppercase tracking-wider">Board Members</th>
                <th className="px-6 py-3 text-center text-xs font-medium text-[var(--color-text-secondary)] uppercase tracking-wider">Officers</th>
                <th className="px-6 py-3 text-center text-xs font-medium text-[var(--color-text-secondary)] uppercase tracking-wider">Total Leaders</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-[var(--color-text-secondary)] uppercase tracking-wider">Fundamental Score</th>
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
                  <td className="px-6 py-4 whitespace-nowrap text-center text-[var(--color-text-secondary)]">
                    {s.board_count}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center text-[var(--color-text-secondary)]">
                    {s.officer_count}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center text-[var(--color-text-secondary)]">
                    {s.total_leaders}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-[var(--color-text-secondary)]">
                    {s.fundamental_score.toFixed(1)}
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
