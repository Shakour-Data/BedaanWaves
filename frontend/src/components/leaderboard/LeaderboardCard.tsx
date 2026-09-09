"use client";

import { memo, useMemo, useState, useEffect, useRef, useCallback } from "react";
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
  virtualize?: boolean;
  itemHeight?: number;
}

const RANK_COLORS = [
  "bg-[var(--color-warning)] text-white",
  "bg-gray-400 text-white",
  "bg-amber-700 text-white",
  "bg-[var(--color-primary)] text-white",
  "bg-[var(--color-primary)]/80 text-white",
];

const ENTRY_HEIGHT = 72;

const Entry = memo(function Entry({ entry, index, showChange, showDimensions }: {
  entry: LeaderboardCardProps["entries"][number];
  index: number;
  showChange: boolean;
  showDimensions: boolean;
}) {
  const dimensionTags = useMemo(() => {
    if (!showDimensions || !entry.dimensions) return null;
    return Object.entries(entry.dimensions)
      .slice(0, 3)
      .map(([key, val]) => (
        <span
          key={key}
          className="rounded bg-[var(--color-background)] px-2 py-1 text-[10px] font-medium text-[var(--color-text-secondary)]"
        >
          {key.slice(0, 3).toUpperCase()}: {val.toFixed(1)}
        </span>
      ));
  }, [showDimensions, entry.dimensions]);

  return (
    <div
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

      {showDimensions && <div className="hidden xl:flex items-center gap-1">{dimensionTags}</div>}
    </div>
  );
});

Entry.displayName = "LeaderboardEntry";

function VirtualizedList({ entries, itemHeight, renderEntry, height }: {
  entries: LeaderboardCardProps["entries"];
  itemHeight: number;
  renderEntry: (entry: LeaderboardCardProps["entries"][number], index: number) => React.ReactNode;
  height: number;
}) {
  const [scrollPosition, setScrollPosition] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);

  const handleScroll = useCallback(() => {
    if (containerRef.current) {
      setScrollPosition(containerRef.current.scrollTop);
    }
  }, []);

  useEffect(() => {
    const container = containerRef.current;
    if (container) {
      container.addEventListener("scroll", handleScroll, { passive: true });
      return () => container.removeEventListener("scroll", handleScroll);
    }
  }, [handleScroll]);

  const visibleCount = Math.ceil(height / itemHeight) + 2;
  const startIndex = Math.floor(scrollPosition / itemHeight);
  const endIndex = Math.min(startIndex + visibleCount, entries.length);
  const visibleEntries = entries.slice(startIndex, endIndex);
  const offsetY = startIndex * itemHeight;

  return (
    <div
      ref={containerRef}
      className="overflow-y-auto"
      style={{ height, contain: "strict" }}
      role="list"
      aria-label="Leaderboard entries"
    >
      <div style={{ height: entries.length * itemHeight, position: "relative" }}>
        <div style={{ transform: `translateY(${offsetY}px)` }}>
          {visibleEntries.map((entry, i) => {
            const actualIndex = startIndex + i;
            return (
              <div key={`${entry.symbol}-${entry.rank}`} style={{ height: itemHeight }}>
                {renderEntry(entry, actualIndex)}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export const LeaderboardCard = memo(function LeaderboardCard({
  entries,
  showChange = false,
  showDimensions = false,
  className,
  virtualize = false,
  itemHeight = ENTRY_HEIGHT,
}: LeaderboardCardProps) {
  const renderEntry = useCallback((entry: LeaderboardCardProps["entries"][number], index: number) => {
    return (
      <Entry
        entry={entry}
        index={index}
        showChange={showChange}
        showDimensions={showDimensions}
      />
    );
  }, [showChange, showDimensions]);

  if (!entries || entries.length === 0) {
    return (
      <div className={cn("rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-12 shadow-sm text-center", className)}>
        <p className="text-[var(--color-text-secondary)]">No data available</p>
      </div>
    );
  }

  if (virtualize && entries.length > 20) {
    return (
      <div className={cn("rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-sm", className)}>
        <VirtualizedList
          entries={entries}
          itemHeight={itemHeight}
          renderEntry={renderEntry}
          height={600}
        />
      </div>
    );
  }

  return (
    <div className={cn("space-y-3", className)}>
      {entries.map((entry, index) => (
        <Entry
          key={`${entry.symbol}-${entry.rank}`}
          entry={entry}
          index={index}
          showChange={showChange}
          showDimensions={showDimensions}
        />
      ))}
    </div>
  );
});

LeaderboardCard.displayName = "LeaderboardCard";