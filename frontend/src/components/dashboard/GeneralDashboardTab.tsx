"use client";

import { useEffect, useMemo, useState } from "react";
import { RefreshCw, BarChart3, CheckCircle, AlertCircle, ExternalLink } from "lucide-react";

import { SpiderChart } from "@/components/charts/SpiderChart";
import { ScoreTrendChart } from "@/components/charts/ScoreTrendChart";
import { ColumnChart } from "@/components/charts/ColumnChart";
import { CoefficientChart } from "@/components/charts/CoefficientChart";
import { TarotCard } from "@/components/ui/TarotCard";
import { Skeleton } from "@/components/ui/Skeleton";
import { ErrorMessage, type ActionOption } from "@/components/ui/ErrorMessage";
import {
  snapshotToChartsModel,
  type ChartsModel,
  type LevelModel,
  type ChartItem,
  LEVELS,
  LEVEL_META,
  fmtDate,
  fmtScore,
} from "@/lib/charts-model";
import {
  useSnapshot,
  useSnapshotLoading,
  useSnapshotError,
  useLoadSnapshot,
} from "@/store/useDateStore";
import { cn } from "@/lib/cn";
import Link from "next/link";

const LEVEL_COLORS: Record<string, string[]> = {
  dimension: ["#2563EB", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6", "#EC4899"],
  sub_dimension: ["#0EA5E9", "#14B8A3", "#F97316", "#F43F5E", "#A78BFA", "#DB71B8"],
  aspect: ["#3B82F6", "#22C58E", "#FB9206", "#EF441E", "#8484F4"],
  sub_aspect: ["#60A5FA", "#4ADE83", "#FB9206", "#F8534C", "#C084FC"],
};

const GREEN = "#10b981";
const RED = "#ef4444";

function greenRed(v: number): string {
  return v >= 0 ? GREEN : RED;
}

function ChartSkeleton() {
  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <Skeleton className="h-5 w-36 rounded" />
        <Skeleton className="h-4 w-10 rounded" />
      </div>
      <Skeleton className="h-52 w-full rounded" />
    </div>
  );
}

function spiderSeries(level: LevelModel) {
  return level.spider.map((i) => ({ label: i.label, value: i.score }));
}

function trendSeries(level: LevelModel) {
  const palette = LEVEL_COLORS[level.key] ?? LEVEL_COLORS.dimension;
  return level.spider.map((item, i) => ({
    key: item.key,
    label: item.label,
    color: palette[i % palette.length],
    data: level.trend.map((pt) => ({
      time: pt.date,
      value: pt.scores[item.key] ?? 0,
    })),
  }));
}

function positiveNegativeColumns(items: ChartItem[], accessor: "score" | "weight") {
  return items.map((it) => ({
    time: it.label,
    value: accessor === "score" ? it.score : it.weight,
    color: greenRed(accessor === "score" ? it.score : it.weight),
  }));
}

export interface GeneralDashboardTabProps {
  /** Defaults to the market (universe) snapshot. Pass a symbol to scope the view. */
  symbol?: string;
}

export function GeneralDashboardTab({ symbol }: GeneralDashboardTabProps) {
  const snapshot = useSnapshot();
  const loading = useSnapshotLoading();
  const error = useSnapshotError();
  const loadSnapshot = useLoadSnapshot();

  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    // Force a fresh market-level snapshot so every widget shares ONE snapshotId.
    // The empty-options call hits /analysis/dashboard/snapshot (universe view).
    const opts: Record<string, unknown> = {};
    if (symbol) opts.symbol = symbol;
    void loadSnapshot(opts);
  }, [loadSnapshot, symbol]);

  const model: ChartsModel | null = useMemo(
    () => (snapshot ? snapshotToChartsModel(snapshot) : null),
    [snapshot],
  );

  const onRetry = () => {
    const opts: Record<string, unknown> = {};
    if (symbol) opts.symbol = symbol;
    void loadSnapshot(opts);
  };

  const onRefresh = () => {
    setRefreshing(true);
    const opts: Record<string, unknown> = {};
    if (symbol) opts.symbol = symbol;
    void loadSnapshot(opts).finally(() => setRefreshing(false));
  };

  if (!model && loading) {
    return (
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 16 }).map((_, i) => (
          <ChartSkeleton key={`skel-${i}`} />
        ))}
      </div>
    );
  }

  if (!model && error) {
    const actions: ActionOption[] = [{ label: "Retry", onAction: onRetry }];
    return (
      <ErrorMessage
        message={error}
        actions={actions}
        moreHelpSteps={[
          "Confirm the backend API is reachable on port 3000",
          "Ensure /analysis/dashboard/snapshot is serving the market snapshot",
          "Verify your authentication token is still valid",
        ]}
        helpTitle="Troubleshooting steps"
      />
    );
  }

  if (!model) {
    return (
      <ErrorMessage
        message="No analytical snapshot available. Click refresh to load the market dashboard."
        actions={[{ label: "Refresh", onAction: onRefresh }]}
      />
    );
  }

  const parity = model.parity;

  return (
    <div className="flex flex-col gap-6">
      {/* Header + controls */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <BarChart3 className="h-4 w-4 text-[var(--color-primary)]" />
          <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">
            Analytical Dashboard
          </h2>
          <span className="text-xs text-[var(--color-text-secondary)]">
            snapshot #{model.snapshotId ? model.snapshotId.slice(0, 8) : "—"} · {fmtDate(model.effectiveAt)}
          </span>
        </div>
        <button
          type="button"
          onClick={onRefresh}
          disabled={refreshing}
          className="inline-flex items-center gap-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm font-medium text-[var(--color-text-secondary)] transition-colors hover:border-[var(--color-primary)] hover:text-[var(--color-text-primary)] disabled:opacity-50"
          aria-label="Refresh analytical dashboard"
        >
          <RefreshCw className={cn("h-4 w-4", refreshing && "animate-spin")} />
          Refresh
        </button>
      </div>

      {/* Parity banner — the headline data-consistency guarantee */}
      <div
        className={cn(
          "flex flex-wrap items-center justify-between gap-3 rounded-xl border px-4 py-3 text-sm",
          parity.ok
            ? "border-[var(--color-success)]/30 bg-[var(--color-success)]/5"
            : "border-[var(--color-error)]/30 bg-[var(--color-error)]/5",
        )}
        role="status"
        aria-live="polite"
      >
        <div className="flex items-center gap-2">
          {parity.ok ? (
            <CheckCircle className="h-4 w-4 text-[var(--color-success)]" />
          ) : (
            <AlertCircle className="h-4 w-4 text-[var(--color-error)]" />
          )}
          <span className="font-medium">
            {parity.ok
              ? "Data parity verified"
              : `${parity.mismatches.length} parity mismatch(es)`}
          </span>
          <span className="text-[var(--color-text-secondary)]">
            · Spider last point ≡ Trend last point for all dimensions
          </span>
        </div>
        <span className="text-[var(--color-text-secondary)]">
          last updated {fmtDate(model.latestDate)} · tolerance ±{parity.tolerance}
        </span>
      </div>

      {/* 20 chart views = 4 levels x 5 families, all from one snapshot */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {LEVELS.map((level) => {
          const L = model.levels.find((l) => l.key === level);
          if (!L) return null;
          return (
            <LevelSection key={level} level={L} />
          );
        })}
      </div>

      <div className="flex items-center justify-between rounded-xl border border-dashed border-[var(--color-border)] bg-[var(--color-surface)]/50 px-4 py-2 text-xs text-[var(--color-text-secondary)]">
        <span>
          Overall market score: <strong className="text-[var(--color-text-primary)]">{fmtScore(model.overallScore)}</strong>
        </span>
        <Link
          href="/methodology"
          className="inline-flex items-center gap-1 font-medium text-[var(--color-primary)] hover:underline"
        >
          How scores are calculated <ExternalLink className="h-3 w-3" />
        </Link>
      </div>
    </div>
  );
}

function LevelSection({ level }: { level: LevelModel }) {
  const palette = LEVEL_COLORS[level.key] ?? LEVEL_COLORS.dimension;
  const meta = LEVEL_META[level.key];

  return (
    <section
      className="grid grid-cols-1 gap-4"
      aria-labelledby={`level-${level.key}-heading`}
    >
      <header className="flex items-center justify-between">
        <h3 id={`level-${level.key}-heading`} className="text-sm font-semibold uppercase tracking-wider text-[var(--color-text-secondary)]">
          {meta.label} ({level.spider.length} items)
        </h3>
        <span className="text-xs text-[var(--color-text-secondary)]">{level.short}</span>
      </header>

      <TarotCard title={`◈ ${meta.label} — Score Spider`}>
        {hasData(level.spider) ? (
          <div className="flex justify-center">
            <SpiderChart data={spiderSeries(level)} size={300} color={palette[0]} />
          </div>
        ) : (
          <EmptyChart label="No spider data for this level" />
        )}
      </TarotCard>

      <TarotCard title={`◈ ${meta.label} — Score Trend (daily)`}>
        {level.trend.length > 0 && hasData(level.spider) ? (
          <ScoreTrendChart series={trendSeries(level)} height={220} showLegend />
        ) : (
          <EmptyChart label="No trend data for this level" />
        )}
      </TarotCard>

      <TarotCard title={`◈ ${meta.label} — Score Changes (Δ)`}>
        {hasData(level.scoreDelta) ? (
          <ColumnChart
            data={positiveNegativeColumns(level.scoreDelta, "score")}
            height={180}
            valueFormatter={(v) => (v >= 0 ? "+" : "") + v.toFixed(2)}
          />
        ) : (
          <EmptyChart label="No score-change data" />
        )}
      </TarotCard>

      <TarotCard title={`◈ ${meta.label} — Coefficients (Weight)`}>
        {hasData(level.weight) ? (
          <CoefficientChart data={level.weight.map((w) => ({ key: w.key, label: w.label, weight: w.weight }))} height={200} />
        ) : (
          <EmptyChart label="No weight data for this level" />
        )}
      </TarotCard>

      <TarotCard title={`◈ ${meta.label} — Coefficient Changes (Δ)`}>
        {hasData(level.weightDelta) ? (
          <ColumnChart
            data={positiveNegativeColumns(level.weightDelta, "score")}
            height={180}
            valueFormatter={(v) => (v >= 0 ? "+" : "") + (v * 100).toFixed(2) + "%"}
          />
        ) : (
          <EmptyChart label="No coefficient-change data for this level" />
        )}
      </TarotCard>
    </section>
  );
}

function hasData(items: ChartItem[]): boolean {
  return items.length > 0 && items.some((i) => typeof i.score === "number" || typeof i.weight === "number");
}

function EmptyChart({ label }: { label: string }) {
  return (
    <div className="flex min-h-[160px] items-center justify-center text-sm text-[var(--color-text-secondary)]">
      {label}
    </div>
  );
}
