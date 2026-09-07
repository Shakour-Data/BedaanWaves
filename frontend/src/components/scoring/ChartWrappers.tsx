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

type RawScoreOverall = number | { score?: number; grade?: string } | null;

interface RawHierarchyScoreShape {
  overall?: RawScoreOverall;
  overallScore?: number;
  OVERALL?: { score?: number; grade?: string };
  dimension?: Record<string, number>;
  sub_dimension?: Record<string, number>;
  aspect?: Record<string, number>;
  sub_aspect?: Record<string, number>;
  level1?: ScoreItemEntry[] | null;
  level2?: ScoreItemEntry[] | null;
  level3?: ScoreItemEntry[] | null;
  level4?: ScoreItemEntry[] | null;
  dimensions?: ScoreItemEntry[] | null;
  sub_dimensions?: ScoreItemEntry[] | null;
  aspects?: ScoreItemEntry[] | null;
  sub_aspects?: ScoreItemEntry[] | null;
  [key: string]: unknown;
}

interface ScoreItemEntry {
  key?: string;
  label?: string;
  score?: number;
  value?: number;
  level_key?: string;
  name?: string;
  level_score?: number;
  weight?: number;
  coefficient?: number;
  w?: number;
}

interface RawWeightShape {
  level1?: ScoreItemEntry[];
  level2?: ScoreItemEntry[];
  level3?: ScoreItemEntry[];
  level4?: ScoreItemEntry[];
  dimension?: Record<string, number>;
  sub_dimension?: Record<string, number>;
  aspect?: Record<string, number>;
  sub_aspect?: Record<string, number>;
  overall?: number;
  [key: string]: unknown;
}

interface RawTrendPointShape {
  date?: string;
  effective_at?: string;
  time?: string;
  overall?: number | null;
  level_scores?: Record<string, number>;
  scores?: Record<string, number>;
  dimension_scores?: Record<string, number | string>;
  sub_dimension_scores?: Record<string, number | string>;
  aspect_scores?: Record<string, number | string>;
  sub_aspect_scores?: Record<string, number | string>;
  value?: number;
  weights?: Record<string, unknown>;
  [key: string]: unknown;
}

interface RawWeightDeltaEntry {
  delta?: number;
  delta_pct?: number;
  change?: number;
  weight?: number;
  value?: number;
}

interface RawWeightDeltaShape {
  delta?: number | null;
  delta_pct?: number | null;
  overall?: { delta?: number; delta_pct?: number };
  weights?: Record<string, unknown>;
  [key: string]: unknown;
}

export type ScoringLevel = 0 | 1 | 2 | 3 | 4;

export const LEVEL_META: Record<ScoringLevel, { label: string; short: string; key: string }> = {
  0: { label: "Overall", short: "OVERALL", key: "overall" },
  1: { label: "Dimensions", short: "DIM", key: "level1" },
  2: { label: "Sub-Dimensions", short: "SUB-DIM", key: "level2" },
  3: { label: "Aspects", short: "ASP", key: "level3" },
  4: { label: "Sub-Aspects", short: "SUB-ASP", key: "level4" },
};

export const LEVEL_ALIASES: Record<string, ScoringLevel> = {
  overall: 0,
  dimension: 1,
  dimensions: 1,
  sub_dimension: 2,
  sub_dimensions: 2,
  aspect: 3,
  aspects: 3,
  sub_aspect: 4,
  sub_aspects: 4,
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
  const raw = h as unknown as RawHierarchyScoreShape;
  const overallVal = raw.overall;
  const objScore = typeof overallVal === 'object' && overallVal !== null ? overallVal.score : undefined;
  const numScore = typeof overallVal === 'number' ? overallVal : undefined;
  const v = objScore ?? raw.overallScore ?? raw.OVERALL?.score ?? numScore ?? 0;
  return num(v);
}

export function levelItemsFromHierarchy(
  hierarchy: HierarchyScores | null | undefined,
  level: ScoringLevel | string,
  parentKey: string | null = null
): Array<{ key: string; label: string; score: number; value: number; weight: number }> {
  const numericLevel: ScoringLevel = typeof level === "number"
    ? level
    : LEVEL_ALIASES[level] ?? 0;

  if (!hierarchy) return [];
  let all: Array<{ key: string; label: string; score: number; value: number; weight: number }> = [];
  if (numericLevel === 0) {
    all = [{ key: "overall", label: "Overall", score: pickOverall(hierarchy), value: pickOverall(hierarchy), weight: 1.0 }];
  } else {
    const k = LEVEL_META[numericLevel].key as "level1" | "level2" | "level3" | "level4";
    const raw = hierarchy as unknown as RawHierarchyScoreShape;
    const arr = raw[k];
    if (Array.isArray(arr)) {
      all = arr.map((it) => {
        const s = num(it.score ?? it.value ?? it.level_score ?? 0);
        return {
          key: it.key ?? it.level_key ?? it.label ?? String(Math.random()).slice(2),
          label: it.label ?? it.name ?? it.key ?? "Item",
          score: s,
          value: s,
          weight: num(it.weight ?? it.coefficient ?? it.w ?? 0),
        };
      });
    } else {
      const dimKeyMap: Record<ScoringLevel, string> = {
        0: "overall",
        1: "dimension",
        2: "sub_dimension",
        3: "aspect",
        4: "sub_aspect",
      };
      const singular = dimKeyMap[numericLevel];
      const bucket = (raw[singular] ?? raw[singular + "s"]) as Record<string, number> | undefined;
      if (bucket && typeof bucket === "object") {
        all = Object.entries(bucket).map(([k2, v]) => {
          const s = num(v);
          return {
            key: k2,
            label: k2.replace(/_/g, " "),
            score: s,
            value: s,
            weight: 0,
          };
        });
      }
    }
  }
  if (parentKey && numericLevel >= 2) {
    return all.filter((it) => it.key.startsWith(parentKey) || it.label.toLowerCase().includes(parentKey.toLowerCase()));
  }
  return all;
}

interface ChartWrapperBaseProps {
  className?: string;
  title?: string;
  emptyLabel?: string;
  minHeight?: number;
}

interface SpiderChartWrapperProps extends ChartWrapperBaseProps {
  snapshot: SnapshotResponse | null;
  tier: "daily" | "hourly" | "current";
  level: ScoringLevel;
  parentKey?: string | null;
  size?: number;
  onLabelClick?: (label: string, item: { key: string; label: string; score: number; weight: number }) => void;
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

interface TrendWrapperProps extends ChartWrapperBaseProps {
  series: TrendPoint[] | undefined | null;
  hierarchy: HierarchyScores | null | undefined;
  level: ScoringLevel;
  parentKey?: string | null;
  height?: number;
  showLegend?: boolean;
  windowLabel?: string;
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
    if (level === 0) {
      return [{
        key: "overall",
        label: "Overall",
        color: PALETTE[0],
        data: series.map((pt) => {
          const rawPt = pt as unknown as RawTrendPointShape;
          return { time: pt.date ?? pt.effective_at, value: num(pt.overall ?? rawPt.value ?? 0) };
        }),
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
         data: series.map((pt) => {
           const rawPt = pt as unknown as RawTrendPointShape;
           const bucket = rawPt[sk] ?? rawPt.level_scores ?? rawPt.scores ?? {};
           const val = bucket && typeof bucket === "object" ? (bucket as Record<string, number>)[item.key] : undefined;
           return { time: pt.date ?? pt.effective_at, value: num(val ?? pt.overall ?? rawPt.value ?? 0) };
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

interface DeltaWrapperProps extends ChartWrapperBaseProps {
  deltaFrame: DeltaFrame | null | undefined;
  hierarchy: HierarchyScores | null | undefined;
  level: ScoringLevel;
  parentKey?: string | null;
  height?: number;
  includeL1Grid?: boolean;
  deltaLabel?: string;
  periodEndLabel?: string;
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

interface WeightCurrentWrapperProps extends ChartWrapperBaseProps {
  weights: WeightSnapshot | null | undefined;
  level: ScoringLevel;
  parentKey?: string | null;
  height?: number;
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
    if (level === 0) {
      return [{ key: "overall", label: "Overall", weight: 1.0 }];
    }
    const raw = weights as unknown as RawWeightShape;
    const k = LEVEL_META[level].key as "level1" | "level2" | "level3" | "level4";
    const rawLevel = raw[k] as ScoreItemEntry[] | undefined;
    let normalized: Array<{ key: string; label: string; weight: number }> = [];
    if (Array.isArray(rawLevel)) {
      normalized = rawLevel.map((it) => ({
        key: it.key ?? it.level_key ?? it.label ?? "",
        label: it.label ?? it.name ?? it.key ?? "",
        weight: num(it.weight ?? it.value ?? 0),
      }));
    } else {
      const weightShortKey: Record<Exclude<ScoringLevel, 0>, string> = {
        1: "dimension",
        2: "sub_dimension",
        3: "aspect",
        4: "sub_aspect",
      };
      const bucket = raw[weightShortKey[level as Exclude<ScoringLevel, 0>]] as Record<string, number> | undefined;
      if (bucket && typeof bucket === "object") {
        normalized = Object.entries(bucket).map(([wk, wv]) => ({
          key: wk,
          label: wk.replace(/_/g, " "),
          weight: num(wv),
        }));
      }
    }
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

interface WeightTrendWrapperProps extends ChartWrapperBaseProps {
  weightTrends: WeightTrendPoint[] | undefined | null;
  weights: WeightSnapshot | null | undefined;
  level: ScoringLevel;
  parentKey?: string | null;
  height?: number;
  windowLabel?: string;
  showLegend?: boolean;
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
    if (level === 0) return [{ key: "overall", label: "Overall", weight: 1.0 }];
    const raw = weights as unknown as RawWeightShape;
    const k = LEVEL_META[level].key as "level1" | "level2" | "level3" | "level4";
    const rawLevel = raw[k] as ScoreItemEntry[] | undefined;
    let norm: Array<{ key: string; label: string; weight: number }> = [];
    if (Array.isArray(rawLevel)) {
      norm = rawLevel.map((it) => ({
        key: it.key ?? it.level_key ?? it.label ?? "",
        label: it.label ?? it.key ?? "",
        weight: num(it.weight ?? 0),
      }));
    } else {
      const weightShortKey: Record<Exclude<ScoringLevel, 0>, string> = {
        1: "dimension",
        2: "sub_dimension",
        3: "aspect",
        4: "sub_aspect",
      };
      const bucket = raw[weightShortKey[level as Exclude<ScoringLevel, 0>]] as Record<string, number> | undefined;
      if (bucket && typeof bucket === "object") {
        norm = Object.entries(bucket).map(([wk, wv]) => ({
          key: wk,
          label: wk.replace(/_/g, " "),
          weight: num(wv),
        }));
      }
    }
    return parentKey && level >= 2 ? norm.filter((w) => w.key.startsWith(parentKey)) : norm;
  }, [weights, level, parentKey]);

  const series = useMemo(() => {
    if (!weightTrends || weightTrends.length === 0) return [];
    if (level === 0) {
      return [{
        key: "overall",
        label: "Overall",
        color: PALETTE[0],
        data: weightTrends.map((pt) => {
          const rawPt = pt as unknown as RawTrendPointShape;
          const rawWeights = weights as unknown as RawWeightShape;
          return {
            time: pt.date ?? pt.effective_at,
            value: num(rawWeights?.overall ?? rawPt.weights?.overall ?? 0),
          };
        }),
      }];
    }
    return weightArr.map((w, i) => ({
      key: w.key,
      label: w.label,
      color: PALETTE[i % PALETTE.length],
      data: weightTrends.map((pt) => {
        const rawPt = pt as unknown as RawTrendPointShape;
        const k = LEVEL_META[level].key as "level1" | "level2" | "level3" | "level4";
        const bucket = (rawPt.weights as Record<string, unknown>)[k];
        let entry: unknown;
        if (Array.isArray(bucket)) {
          entry = (bucket as ScoreItemEntry[]).find((b) => (b.key ?? b.level_key) === w.key);
        } else if (bucket && typeof bucket === "object") {
          entry = (bucket as Record<string, unknown>)[w.key];
        }
        const weightShortKey: Record<Exclude<ScoringLevel, 0>, string> = {
          1: "dimension",
          2: "sub_dimension",
          3: "aspect",
          4: "sub_aspect",
        };
        const altKey = weightShortKey[level as Exclude<ScoringLevel, 0>];
        const rawWeights = rawPt.weights as Record<string, unknown> | undefined;
        const altBucket = rawWeights?.[altKey];
        let v = 0;
        if (entry && typeof entry === "object") {
          const e = entry as RawWeightDeltaEntry;
          v = num(e.weight ?? e.value ?? 0);
        } else if (typeof entry === "number") {
          v = entry;
        } else if (altBucket && typeof altBucket === "object" && typeof (altBucket as Record<string, unknown>)[w.key] === "number") {
          v = (altBucket as Record<string, number>)[w.key];
        }
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

interface WeightDeltaWrapperProps extends ChartWrapperBaseProps {
  weightDeltas: WeightDeltaPoint | null | undefined;
  weights: WeightSnapshot | null | undefined;
  level: ScoringLevel;
  parentKey?: string | null;
  height?: number;
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
    if (level === 0) return [{ key: "overall", label: "Overall", weight: 1.0 }];
    const raw = weights as unknown as RawWeightShape;
    const k = LEVEL_META[level].key as "level1" | "level2" | "level3" | "level4";
    const rawLevel = raw[k] as ScoreItemEntry[] | undefined;
    let norm: Array<{ key: string; label: string; weight: number }> = [];
    if (Array.isArray(rawLevel)) {
      norm = rawLevel.map((it) => ({
        key: it.key ?? it.level_key ?? it.label ?? "",
        label: it.label ?? it.key ?? "",
        weight: num(it.weight ?? 0),
      }));
    } else {
      const weightShortKey: Record<Exclude<ScoringLevel, 0>, string> = {
        1: "dimension",
        2: "sub_dimension",
        3: "aspect",
        4: "sub_aspect",
      };
      const bucket = raw[weightShortKey[level as Exclude<ScoringLevel, 0>]] as Record<string, number> | undefined;
      if (bucket && typeof bucket === "object") {
        norm = Object.entries(bucket).map(([wk, wv]) => ({
          key: wk,
          label: wk.replace(/_/g, " "),
          weight: num(wv),
        }));
      }
    }
    return parentKey && level >= 2 ? norm.filter((w) => w.key.startsWith(parentKey)) : norm;
  }, [weights, level, parentKey]);

  const flatSeries = useMemo(() => {
    if (!weightDeltas) return [];
    const rawWD = weightDeltas as unknown as RawWeightDeltaShape;
    const k = LEVEL_META[level].key as "level1" | "level2" | "level3" | "level4";
    type DeltaBucket = Record<string, { delta?: number; delta_pct?: number; change?: number }>;
    let bucket: DeltaBucket | undefined = rawWD.weights?.[k] as DeltaBucket | undefined;
    if (!bucket) {
      const weightShortKey: Record<Exclude<ScoringLevel, 0>, string> = {
        1: "dimension",
        2: "sub_dimension",
        3: "aspect",
        4: "sub_aspect",
      };
      bucket = rawWD[`${weightShortKey[level as Exclude<ScoringLevel, 0>]}_deltas`] as DeltaBucket | undefined;
    }
    if (!bucket && level !== 0) return [];
    if (level === 0) {
      const delta = num(weightDeltas.delta ?? rawWD.overall?.delta ?? 0);
      return delta !== 0 ? [{ time: "Overall", value: delta, color: delta >= 0 ? "#10b981" : "#ef4444" }] : [];
    }
    return weightArr
      .map((w) => {
        const e = bucket?.[w.key] as RawWeightDeltaEntry | undefined;
        const v = num(e?.delta ?? e?.change ?? 0);
        return { time: w.label, value: v, color: v >= 0 ? "#10b981" : "#ef4444" };
      })
      .filter(() => true);
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

export type ScoringTab = "HISTORICAL" | "INTRADAY";
export type ViewMode = "SIMPLE" | "EXPERT";
export type DailyWindow = 30 | 90 | 365;
export type IntradayWindow = "6h" | "24h" | "7d";

interface ViewHeaderControlsProps {
  scoringTab: ScoringTab;
  onScoringTabChange: (t: ScoringTab) => void;
  viewMode: ViewMode;
  onViewModeChange: (m: ViewMode) => void;
  windowDaily: DailyWindow;
  onWindowDailyChange: (w: DailyWindow) => void;
  windowIntraday: IntradayWindow;
  onWindowIntradayChange: (w: IntradayWindow) => void;
  className?: string;
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

interface ScoringLevelSelectorProps {
  level?: ScoringLevel;
  value?: string;
  onLevelChange?: (l: ScoringLevel) => void;
  onChange?: (level: string) => void;
  className?: string;
  includeOverall?: boolean;
}

const LEVEL_SHORT_TO_NUM: Record<string, ScoringLevel> = {
  overall: 0,
  dimension: 1,
  sub_dimension: 2,
  aspect: 3,
  sub_aspect: 4,
};

export function ScoringLevelSelector({
  level,
  value,
  onLevelChange,
  onChange,
  className,
  includeOverall = true,
}: ScoringLevelSelectorProps) {
  const currentLevel: ScoringLevel = level ?? (value ? LEVEL_SHORT_TO_NUM[value] ?? 0 : 0);
  const levels: ScoringLevel[] = includeOverall ? [0, 1, 2, 3, 4] : [1, 2, 3, 4];
  const handleChange = (lvl: ScoringLevel) => {
    onLevelChange?.(lvl);
    if (onChange) onChange(LEVEL_META[lvl].key);
  };
  return (
    <div
      className={cn(
        "flex items-center gap-1 rounded-lg bg-[var(--color-neutral)] p-1 flex-wrap",
        className,
      )}
      role="group"
      aria-label="Hierarchy level"
    >
      {levels.map((lvl) => {
        const meta = LEVEL_META[lvl];
        return (
          <button
            key={lvl}
            type="button"
            onClick={() => handleChange(lvl)}
            className={cn(
              "rounded-md px-3 py-1 text-xs font-semibold transition whitespace-nowrap",
              currentLevel === lvl
                ? "bg-[var(--color-background)] text-[var(--color-primary)] border border-[var(--color-border)] shadow-sm"
                : "text-muted-foreground hover:text-foreground",
            )}
            aria-pressed={currentLevel === lvl}
          >
            {meta.short}
          </button>
        );
      })}
    </div>
  );
}

interface ParentSelectorProps {
  hierarchy?: HierarchyScores | null | undefined;
  level?: ScoringLevel;
  parentLevel?: Exclude<ScoringLevel, 0 | 4>;
  parentKey?: string | null;
  onParentChange?: (parentKey: string | null) => void;
  options?: string[];
  value?: string | null;
  onChange?: (key: string) => void;
  className?: string;
}

export function ParentSelector({
  hierarchy,
  level: _level,
  parentLevel: _parentLevel,
  parentKey,
  onParentChange,
  options,
  value,
  onChange,
  className,
}: ParentSelectorProps) {
  const parents = useMemo(
    () => (_parentLevel && hierarchy ? levelItemsFromHierarchy(hierarchy, _parentLevel) : []),
    [hierarchy, _parentLevel],
  );
  const showOptions = options !== undefined;
  const items = showOptions ? options! : parents.map((p) => p.key);

  if (!showOptions && (!_level || !_parentLevel || _level <= _parentLevel)) return null;
  const label = _parentLevel ? LEVEL_META[_parentLevel].label : "Parent";
  return (
    <div className={cn("flex items-center gap-2 flex-wrap", className)}>
      <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
        Parent {label}:
      </span>
      <div
        className="flex items-center gap-1 rounded-lg bg-[var(--color-neutral)] p-1 flex-wrap"
        role="group"
        aria-label={`Parent ${label}`}
      >
        {!showOptions && (
          <button
            type="button"
            onClick={() => onParentChange?.(null)}
            className={cn(
              "rounded-md px-3 py-1 text-xs font-semibold transition",
              parentKey === null
                ? "bg-[var(--color-background)] text-[var(--color-primary)] border border-[var(--color-border)] shadow-sm"
                : "text-muted-foreground hover:text-foreground",
            )}
            aria-pressed={parentKey === null}
          >
            ALL
          </button>
        )}
        {items.map((p) => {
          const key = p;
          const isActive = showOptions ? value === p : parentKey === p;
          return (
            <button
              key={key}
              type="button"
              onClick={() => {
                if (showOptions) onChange?.(p);
                else onParentChange?.(p);
              }}
              className={cn(
                "rounded-md px-3 py-1 text-xs font-semibold transition whitespace-nowrap",
                isActive
                  ? "bg-[var(--color-background)] text-[var(--color-primary)] border border-[var(--color-border)] shadow-sm"
                  : "text-muted-foreground hover:text-foreground",
              )}
              aria-pressed={isActive}
            >
              {p}
            </button>
          );
        })}
      </div>
    </div>
  );
}
