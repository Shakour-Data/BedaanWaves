"use client";

import { cn } from "@/lib/cn";
import { ScoreBadge, ChangeBadge, GradeBadge } from "./ScoreBadge";

interface LeaderboardCardProps {
  entries: Array<{
    rank: number;
    symbol: string;
    name: string;
    sector: string | null;
    score: number;
    grade: string;
    change?: number;
    change_pct?: number;
    dimensions?: Record<string, number>;
    sub_dimensions?: Record<string, number>;
    aspects?: Record<string, number>;
    sub_aspects?: Record<string, number>;
  }>;
  showChange?: boolean;
  showDimensions?: boolean;
  className?: string;
}

const RANK_COLORS = [
  "bg-[var(--color-warning)] text-white",
  "bg-gray-400 text-white",
  "bg-amber-700 text-white",
  "bg-[var(--color-primary)] text-white",
  "bg-[var(--color-primary)]/80 text-white",
];

export function LeaderboardCard({ entries, showChange = false, showDimensions = false, className }: LeaderboardCardProps) {
  if (!entries || entries.length === 0) {
    return (
      <div className={cn("rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-12 shadow-sm text-center", className)}>
        <p className="text-[var(--color-text-secondary)]">No data available</p>
      </div>
    );
  }

  return (
    <div className={cn("space-y-3", className)}>
      {entries.map((entry, index) => (
        <div
          key={`${entry.symbol}-${entry.rank}`}
          className="group flex items-center gap-4 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 shadow-sm transition-all hover:shadow-md hover:border-[var(--color-primary)]/30"
        >
          <div
            className={cn(
              "flex h-10 w-10 shrink-0 items-center justify-center rounded-lg text-sm font-bold",
              index < RANK_COLORS.length ? RANK_COLORS[index] : "bg-[var(--color-border)] text-[var(--color-text-secondary)]"
            )}
          >
            {entry.rank}
          </div>

          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-[var(--color-primary)]/10 text-sm font-bold text-[var(--color-primary)]">
            {entry.symbol.slice(0, 2)}
          </div>

          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-[var(--color-text-primary)]">{entry.symbol}</span>
              <GradeBadge grade={entry.grade} />
            </div>
            <p className="truncate text-xs text-[var(--color-text-secondary)]">{entry.name}</p>
            {entry.sector && (
              <p className="text-[10px] text-[var(--color-text-secondary)]">{entry.sector}</p>
            )}
          </div>

          <div className="shrink-0 text-right">
            {showChange && entry.change !== undefined ? (
              <ChangeBadge change={entry.change} changePct={entry.change_pct || 0} />
            ) : (
              <ScoreBadge score={entry.score} size="lg" />
            )}
          </div>

          {showDimensions && entry.dimensions && (
            <div className="hidden xl:flex items-center gap-1">
              {Object.entries(entry.dimensions).slice(0, 3).map(([key, val]) => (
                <span
                  key={key}
                  className="rounded bg-[var(--color-background)] px-2 py-1 text-[10px] font-medium text-[var(--color-text-secondary)]"
                >
                  {key.slice(0, 3).toUpperCase()}: {val.toFixed(1)}
                </span>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
