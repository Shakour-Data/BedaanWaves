"use client";

import { useMemo } from "react";
import { cn } from "@/lib/cn";
import { num } from "@/lib/utils";
import { SpiderChart } from "@/components/charts/SpiderChart";
import { ScoreTrendChart } from "@/components/charts/ScoreTrendChart";
import { ColumnChart } from "@/components/charts/ColumnChart";
import { CoefficientChart } from "@/components/charts/CoefficientChart";
import { TarotCard } from "@/components/ui/TarotCard";
import type {
  SnapshotResponse,
  HierarchyScores,
  DeltaFrame,
  WeightSnapshot,
  WeightTrendPoint,
  WeightDeltaPoint,
  TrendPoint,
} from "@/store/useDateStore";
import {
  flexPickOverall,
  flexLevelItems,
  flexWeightItems,
  flexTrendWeightValue,
  flexWeightDeltaBucket,
  flexWeightOverallDelta,
  type FlexHierarchyScores,
  type FlexTrendPoint,
  type FlexWeights,
  type FlexWeightDeltas,
} from "@/lib/scoring-adapters";

import type {
  ScoringLevel,
  ScoringTab,
  ViewMode,
  DailyWindow,
  IntradayWindow,
  ChartWrapperBaseProps,
  SpiderChartWrapperProps,
  TrendWrapperProps,
  DeltaWrapperProps,
  WeightCurrentWrapperProps,
  WeightTrendWrapperProps,
  WeightDeltaWrapperProps,
  ViewHeaderControlsProps,
  ScoringLevelSelectorProps,
  ParentSelectorProps,
} from "./chart-wrapper-types";

export type { ScoringLevel, ScoringTab, ViewMode, DailyWindow, IntradayWindow };

export const LEVEL_META: Record<ScoringLevel, { label: string; short: string; key: string }> = {
  0: { label: "Overall", short: "OVERALL", key: "overall" },
  1: { label: "Dimensions", short: "DIM", key: "level1" },
  2: { label: "Sub-Dimensions", short: "SUB-DIM", key: "level2" },
  3: { label: "Aspects", short: "ASP", key: "level3" },
  4: { label: "Sub-Aspects", short: "SUB-ASP", key: "level4" },
};

const PALETTE = [
  "#2563EB",
  "#10B981",
  "#F59E0B",
  "#EF4444",
  "#8B5CF6",
  "#EC4899",
  "#06B6D4",
  "#F97316",
];

function pickOverall(h: HierarchyScores): number {
  return flexPickOverall(h as FlexHierarchyScores);
}

export function levelItemsFromHierarchy(
  hierarchy: HierarchyScores | null | undefined,
  level: ScoringLevel,
  parentKey: string | null = null
): Array<{ key: string; label: string; score: number; weight: number }> {
  if (!hierarchy) return [];
  let all: Array<{ key: string; label: string; score: number; weight: number }> = [];
  if (level === 0) {
    all = [{ key: "overall", label: "Overall", score: pickOverall(hierarchy), weight: 1.0 }];
  } else {
    all = flexLevelItems(hierarchy as FlexHierarchyScores, level);
  }
  if (parentKey && level >= 2) {
    return all.filter((it) => it.key.startsWith(parentKey) || it.label.toLowerCase().includes(parentKey.toLowerCase()));
  }
  return all;
}


export function SpiderChartWrapper({
  snapshot,
  tier,
  level,
  parentKey = null,
  size = 360,
  onLabelClick,
  className,
  title,
  emptyLabel = "No spider data",
}: SpiderChartWrapperProps) {
  const hierarchy = snapshot?.scores?.[tier];
  const items = useMemo(
    () => levelItemsFromHierarchy(hierarchy, level, parentKey),
    [hierarchy, level, parentKey]
  );
  const spiderData = useMemo(
    () => items.map((i) => ({ label: i.label, value: num(i.score) })),
    [items]
  );
  const meta = LEVEL_META[level];
  const displayTitle = title ?? `◈ ${meta.label} Spider · ${tier.toUpperCase()}`;

  return (
    <TarotCard className={className} title={displayTitle}>
      {spiderData.length > 0 ? (
        <div className="flex justify-center">
          <SpiderChart
            data={spiderData}
            size={size}
            color={PALETTE[Math.max(0, level - 1)]}
            onLabelClick={onLabelClick ? (label) => {
              const it = items.find((x) => x.label === label);
              if (it) onLabelClick(label, it);
            } : undefined}
          />
        </div>
      ) : (
        <div
          className="flex items-center justify-center text-sm text-muted-foreground"
          style={{ minHeight: size ?? 240 }}
        >
          {emptyLabel}
        </div>
      )}
    </TarotCard>
  );
}


export function ScoreTrendWrapper({
  series,
  hierarchy,
  level,
  parentKey = null,
  height = 280,
  showLegend = true,
  windowLabel,
  className,
  title,
  emptyLabel = "No trend data",
}: TrendWrapperProps) {
  const items = useMemo(
    () => levelItemsFromHierarchy(hierarchy, level, parentKey),
    [hierarchy, level, parentKey]
  );
  const chartSeries = useMemo(() => {
    if (!series || series.length === 0) return [];
    const flexSeries = series as unknown as FlexTrendPoint[];
    if (level === 0) {
      return [{
        key: "overall",
        label: "Overall",
        color: PALETTE[0],
        data: flexSeries.map((pt) => ({ time: pt.date ?? pt.effective_at, value: num(pt.overall ?? pt.value ?? 0) })),
      }];
    }
    const scoreKeyMap: Record<ScoringLevel, string> = {
      0: "overall",
      1: "dimension_scores",
      2: "sub_dimension_scores",
      3: "aspect_scores",
      4: "sub_aspect_scores",
    };
    const sk = scoreKeyMap[level];
    return items.map((item, i) => ({
      key: item.key,
      label: item.label,
      color: PALETTE[i % PALETTE.length],
      data: flexSeries.map((pt) => {
        const bucket =
          (pt[sk as keyof FlexTrendPoint] as Record<string, number> | undefined) ??
          pt.level_scores ??
          pt.scores ??
          {};
        const val = bucket && typeof bucket === "object" ? bucket[item.key] : undefined;
        return { time: pt.date ?? pt.effective_at, value: num(val ?? pt.overall ?? pt.value ?? 0) };
      }),
    }));
  }, [series, items, level]);
  const meta = LEVEL_META[level];
  const displayTitle = title ?? `◈ ${meta.label} Trend${windowLabel ? ` (${windowLabel})` : ""}`;

  return (
    <TarotCard className={className} title={displayTitle}>
      {chartSeries.length > 0 ? (
        <ScoreTrendChart showLegend={showLegend} series={chartSeries} height={height} />
      ) : (
        <div
          className="flex items-center justify-center text-sm text-muted-foreground"
          style={{ minHeight: height }}
        >
          {emptyLabel}
        </div>
      )}
    </TarotCard>
  );
}

function deltaBucketForLevel(df: DeltaFrame, level: ScoringLevel): Record<string, { delta: number | null; delta_pct: number | null }> {
  if (level === 1) return df.dimension_deltas ?? {};
  if (level === 2) return df.sub_dimension_deltas ?? {};
  if (level === 3) return df.aspect_deltas ?? {};
  if (level === 4) return df.sub_aspect_deltas ?? {};
  return {};
}

export function ScoreDeltaWrapper({
  deltaFrame,
  hierarchy,
  level,
  parentKey = null,
  height = 220,
  includeL1Grid = true,
  deltaLabel,
  periodEndLabel,
  className,
  title,
  emptyLabel = "No delta data",
}: DeltaWrapperProps) {
  const items = useMemo(
    () => levelItemsFromHierarchy(hierarchy, level, parentKey),
    [hierarchy, level, parentKey]
  );
  const l1Series = useMemo(() => {
    if (!deltaFrame) return [];
    const bucket = deltaBucketForLevel(deltaFrame, level);
    return items.map((item, i) => {
      let delta = 0;
      if (level === 0) {
        delta = num(deltaFrame.overall_delta ?? 0);
      } else {
        const entry = bucket[item.key];
        delta = num(entry?.delta ?? 0);
      }
      const t = periodEndLabel ?? "Δ";
      return {
        key: item.key,
        label: item.label,
        color: PALETTE[i % PALETTE.length],
        data: [{ time: t, value: delta }],
      };
    });
  }, [deltaFrame, items, level, periodEndLabel]);

  const flatSeries = useMemo(() => {
    if (l1Series.length === 0) return [];
    if (level === 0) {
      const only = l1Series[0]?.data?.[0];
      return only ? [{ time: only.time, value: only.value, color: only.value >= 0 ? "#10b981" : "#ef4444" }] : [];
    }
    return l1Series.map((s) => {
      const v = s.data[s.data.length - 1]?.value ?? 0;
      return { time: s.label, value: v, color: v >= 0 ? "#10b981" : "#ef4444" };
    });
  }, [l1Series, level]);

  const meta = LEVEL_META[level];
  const defaultTitle = `◈ ${meta.label} Deltas${deltaLabel ? ` · ${deltaLabel}` : ""}`;

  return (
    <TarotCard className={className} title={title ?? defaultTitle}>
      {flatSeries.length > 0 ? (
        level === 1 && includeL1Grid ? (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
            {l1Series.map((series) => (
              <div key={series.key} className="rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] p-3">
                <div className="mb-1 flex items-center gap-2">
                  <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: series.color }} />
                  <span className="text-xs font-medium text-[var(--color-text-secondary)]">{series.label}</span>
                </div>
                <ColumnChart
                  data={series.data.map((pt) => ({ ...pt, color: pt.value >= 0 ? "#10b981" : "#ef4444" }))}
                  height={120}
                  valueFormatter={(v) => (v >= 0 ? "+" : "") + v.toFixed(2)}
                />
              </div>
            ))}
          </div>
        ) : (
          <ColumnChart
            data={flatSeries}
            height={height}
            valueFormatter={(v) => (v >= 0 ? "+" : "") + v.toFixed(2)}
          />
        )
      ) : (
        <div
          className="flex items-center justify-center text-sm text-muted-foreground"
          style={{ minHeight: height }}
        >
          {emptyLabel}
        </div>
      )}
    </TarotCard>
  );
}


export function WeightCurrentWrapper({
  weights,
  level,
  parentKey = null,
  height = 260,
  className,
  title,
  emptyLabel = "No weight data",
}: WeightCurrentWrapperProps) {
  const weightArr = useMemo(() => {
    if (!weights) return [];
    const normalized = flexWeightItems(weights as FlexWeights, level);
    return parentKey && level >= 2
      ? normalized.filter((w) => w.key.startsWith(parentKey))
      : normalized;
  }, [weights, level, parentKey]);

  const meta = LEVEL_META[level];
  const displayTitle = title ?? `◈ ${meta.label} Weights`;

  return (
    <TarotCard className={className} title={displayTitle}>
      {weightArr.length > 0 ? (
        <CoefficientChart
          data={weightArr}
          height={height}
        />
      ) : (
        <div
          className="flex items-center justify-center text-sm text-muted-foreground"
          style={{ minHeight: height }}
        >
          {emptyLabel}
        </div>
      )}
    </TarotCard>
  );
}

export function WeightTrendWrapper({
  weightTrends,
  weights,
  level,
  parentKey = null,
  height = 260,
  windowLabel,
  showLegend = true,
  className,
  title,
  emptyLabel = "No weight trend data",
}: WeightTrendWrapperProps) {
  const weightArr = useMemo(() => {
    if (!weights) return [];
    const norm = flexWeightItems(weights as FlexWeights, level);
    return parentKey && level >= 2 ? norm.filter((w) => w.key.startsWith(parentKey)) : norm;
  }, [weights, level, parentKey]);

  const series = useMemo(() => {
    if (!weightTrends || weightTrends.length === 0) return [];
    if (level === 0) {
      return [{
        key: "overall",
        label: "Overall",
        color: PALETTE[0],
        data: weightTrends.map((pt) => ({
          time: pt.date ?? pt.effective_at,
          value: num((weights as FlexWeights)?.overall ?? (pt.weights as FlexWeights)?.overall ?? 0),
        })),
      }];
    }
    return weightArr.map((w, i) => ({
      key: w.key,
      label: w.label,
      color: PALETTE[i % PALETTE.length],
      data: weightTrends.map((pt) => {
        const v = flexTrendWeightValue(pt.weights as FlexWeights, level, w.key);
        return { time: pt.date ?? pt.effective_at, value: v };
      }),
    }));
  }, [weightTrends, weightArr, level, weights]);

  const meta = LEVEL_META[level];
  const displayTitle = title ?? `◈ ${meta.label} Weight Trend${windowLabel ? ` (${windowLabel})` : ""}`;

  return (
    <TarotCard className={className} title={displayTitle}>
      {series.length > 0 ? (
        <ScoreTrendChart showLegend={showLegend} series={series} height={height} />
      ) : (
        <div
          className="flex items-center justify-center text-sm text-muted-foreground"
          style={{ minHeight: height }}
        >
          {emptyLabel}
        </div>
      )}
    </TarotCard>
  );
}


export function WeightDeltaWrapper({
  weightDeltas,
  weights,
  level,
  parentKey = null,
  height = 220,
  className,
  title,
  emptyLabel = "No weight delta data",
}: WeightDeltaWrapperProps) {
  const weightArr = useMemo(() => {
    if (!weights) return [];
    const norm = flexWeightItems(weights as FlexWeights, level);
    return parentKey && level >= 2 ? norm.filter((w) => w.key.startsWith(parentKey)) : norm;
  }, [weights, level, parentKey]);

  const flatSeries = useMemo(() => {
    if (!weightDeltas) return [];
    const flexDeltas = weightDeltas as unknown as FlexWeightDeltas;
    let bucket = flexWeightDeltaBucket(flexDeltas, level);
    if (!bucket && level !== 0) return [];
    if (level === 0) {
      const delta = flexWeightOverallDelta(flexDeltas);
      return delta !== 0 ? [{ time: "Overall", value: delta, color: delta >= 0 ? "#10b981" : "#ef4444" }] : [];
    }
    return weightArr
      .map((w) => {
        const e = bucket?.[w.key];
        const v = num(e?.delta ?? e?.change ?? 0);
        return { time: w.label, value: v, color: v >= 0 ? "#10b981" : "#ef4444" };
      })
      .filter((pt) => true);
  }, [weightDeltas, weightArr, level]);

  const meta = LEVEL_META[level];
  const displayTitle = title ?? `◈ ${meta.label} Weight Δ`;

  return (
    <TarotCard className={className} title={displayTitle}>
      {flatSeries.length > 0 ? (
        <ColumnChart
          data={flatSeries}
          height={height}
          valueFormatter={(v) => (v >= 0 ? "+" : "") + v.toFixed(4)}
        />
      ) : (
        <div
          className="flex items-center justify-center text-sm text-muted-foreground"
          style={{ minHeight: height }}
        >
          {emptyLabel}
        </div>
      )}
    </TarotCard>
  );
}


export function ViewHeaderControls({
  scoringTab,
  onScoringTabChange,
  viewMode,
  onViewModeChange,
  windowDaily,
  onWindowDailyChange,
  windowIntraday,
  onWindowIntradayChange,
  className,
}: ViewHeaderControlsProps) {
  const dailyOpts: DailyWindow[] = [30, 90, 365];
  const intradayOpts: IntradayWindow[] = ["6h", "24h", "7d"];
  return (
    <div
      role="tablist"
      aria-label="Scoring view mode"
      className={cn(
        "flex items-center justify-between gap-3 flex-wrap rounded-xl border border-[var(--color-border)] bg-[var(--color-background)] p-3",
        className
      )}
    >
      <div className="flex items-center gap-1 rounded-lg bg-[var(--color-neutral)] p-1">
        {(["HISTORICAL", "INTRADAY"] as ScoringTab[]).map((tab) => (
          <button
            key={tab}
            role="tab"
            type="button"
            aria-selected={scoringTab === tab}
            aria-controls={`scoring-panel-${tab}`}
            id={`scoring-tab-${tab}`}
            onClick={() => onScoringTabChange(tab)}
            className={cn(
              "rounded-md px-4 py-1.5 text-sm font-semibold transition",
              scoringTab === tab
                ? "bg-[var(--color-background)] text-[var(--color-primary)] shadow-sm border border-[var(--color-border)]"
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            {tab === "HISTORICAL" ? "◷ HISTORICAL" : "⚡ INTRADAY"}
          </button>
        ))}
      </div>
      <div className="flex items-center gap-2 flex-wrap">
        {scoringTab === "HISTORICAL" ? (
          <div className="flex items-center gap-1 rounded-lg bg-[var(--color-neutral)] p-1" role="group" aria-label="Historical window">
            {dailyOpts.map((w) => (
              <button
                key={w}
                type="button"
                onClick={() => onWindowDailyChange(w)}
                className={cn(
                  "rounded-md px-3 py-1 text-xs font-semibold transition",
                  windowDaily === w
                    ? "bg-[var(--color-background)] text-[var(--color-primary)] border border-[var(--color-border)] shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                )}
                aria-pressed={windowDaily === w}
              >
                {w}D
              </button>
            ))}
          </div>
        ) : (
          <div className="flex items-center gap-1 rounded-lg bg-[var(--color-neutral)] p-1" role="group" aria-label="Intraday window">
            {intradayOpts.map((w) => (
              <button
                key={w}
                type="button"
                onClick={() => onWindowIntradayChange(w)}
                className={cn(
                  "rounded-md px-3 py-1 text-xs font-semibold transition",
                  windowIntraday === w
                    ? "bg-[var(--color-background)] text-[var(--color-primary)] border border-[var(--color-border)] shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                )}
                aria-pressed={windowIntraday === w}
              >
                {w.toUpperCase()}
              </button>
            ))}
          </div>
        )}
        <div className="flex items-center gap-1 rounded-lg bg-[var(--color-neutral)] p-1" role="group" aria-label="View complexity">
          {(["SIMPLE", "EXPERT"] as ViewMode[]).map((m) => (
            <button
              key={m}
              type="button"
              onClick={() => onViewModeChange(m)}
              className={cn(
                "rounded-md px-3 py-1 text-xs font-semibold transition",
                viewMode === m
                  ? "bg-[var(--color-background)] text-[var(--color-primary)] border border-[var(--color-border)] shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              )}
              aria-pressed={viewMode === m}
            >
              {m}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

export function ScoringLevelSelector({
  level,
  onLevelChange,
  className,
  includeOverall = true,
}: ScoringLevelSelectorProps) {
  const levels: ScoringLevel[] = includeOverall ? [0, 1, 2, 3, 4] : [1, 2, 3, 4];
  return (
    <div className={cn("flex items-center gap-1 rounded-lg bg-[var(--color-neutral)] p-1 flex-wrap", className)} role="group" aria-label="Hierarchy level">
      {levels.map((lvl) => {
        const meta = LEVEL_META[lvl];
        return (
          <button
            key={lvl}
            type="button"
            onClick={() => onLevelChange(lvl)}
            className={cn(
              "rounded-md px-3 py-1 text-xs font-semibold transition whitespace-nowrap",
              level === lvl
                ? "bg-[var(--color-background)] text-[var(--color-primary)] border border-[var(--color-border)] shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            )}
            aria-pressed={level === lvl}
          >
            {meta.short}
          </button>
        );
      })}
    </div>
  );
}

export function ParentSelector({
  hierarchy,
  level,
  parentLevel,
  parentKey,
  onParentChange,
  className,
}: ParentSelectorProps) {
  const parents = useMemo(
    () => levelItemsFromHierarchy(hierarchy, parentLevel),
    [hierarchy, parentLevel]
  );
  if (level <= parentLevel) return null;
  const label = LEVEL_META[parentLevel].label;
  return (
    <div className={cn("flex items-center gap-2 flex-wrap", className)}>
      <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
        Parent {label}:
      </span>
      <div className="flex items-center gap-1 rounded-lg bg-[var(--color-neutral)] p-1 flex-wrap" role="group" aria-label={`Parent ${label}`}>
        <button
          type="button"
          onClick={() => onParentChange(null)}
          className={cn(
            "rounded-md px-3 py-1 text-xs font-semibold transition",
            parentKey === null
              ? "bg-[var(--color-background)] text-[var(--color-primary)] border border-[var(--color-border)] shadow-sm"
              : "text-muted-foreground hover:text-foreground"
          )}
          aria-pressed={parentKey === null}
        >
          ALL
        </button>
        {parents.map((p) => (
          <button
            key={p.key}
            type="button"
            onClick={() => onParentChange(p.key)}
            className={cn(
              "rounded-md px-3 py-1 text-xs font-semibold transition whitespace-nowrap",
              parentKey === p.key
                ? "bg-[var(--color-background)] text-[var(--color-primary)] border border-[var(--color-border)] shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            )}
            aria-pressed={parentKey === p.key}
          >
            {p.label}
          </button>
        ))}
      </div>
    </div>
  );
}
