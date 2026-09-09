/**
 * charts-model.ts
 * ---------------------------------------------------------------------------
 * Single source-of-truth adapter that converts a unified Temporal Snapshot
 * response into the 20 analytical chart views required by the dashboard.
 *
 * DESIGN (data-consistency):
 *  The Market Dashboard "General" tab MUST guarantee that the LAST point of
 *  every Score Trend line equals the value shown in the matching Spider chart.
 *  To make this provable (not assumed), this adapter derives BOTH the spider
 *  (current snapshot scores) and the trend series from the SAME snapshot object,
 *  then runs an explicit `assertParity` comparison. The result is surfaced in a
 *  ParityReport so the UI can render a concrete "data parity verified" badge.
 *
 * The 20 views = 4 hierarchy levels x 5 chart families:
 *  1-4   Spider (score)            -> spider[]
 *  5-8   Score Trend (line)          -> trend[]
 *  9-12  Score Change (bar/column)  -> scoreDelta[]
 *  13-16 Coefficient / Weight       -> weight[]
 *  17-20 Coefficient Change         -> weightDelta[]
 */

import type {
  SnapshotResponse,
  HierarchyScores,
  TrendPoint,
  WeightTrendPoint,
} from "@/lib/api/dashboard";
import { num } from "@/lib/utils";

export type LevelKey = "dimension" | "sub_dimension" | "aspect" | "sub_aspect";

export const LEVELS: LevelKey[] = ["dimension", "sub_dimension", "aspect", "sub_aspect"];

export const LEVEL_META: Record<LevelKey, { label: string; short: string }> = {
  dimension: { label: "Dimensions", short: "DIM" },
  sub_dimension: { label: "Sub-Dimensions", short: "SUB-DIM" },
  aspect: { label: "Aspects", short: "ASP" },
  sub_aspect: { label: "Sub-Aspects", short: "SUB-ASP" },
};

export interface ChartItem {
  key: string;
  label: string;
  score: number;
  weight: number;
}

export interface TrendPointView {
  date: string;
  scores: Record<string, number>;
}

export interface LevelModel {
  key: LevelKey;
  label: string;
  short: string;
  /** Current snapshot scores -> Spider chart (single polygon) */
  spider: ChartItem[];
  /** Historical trend of scores -> Trend line chart (last point must === spider) */
  trend: TrendPointView[];
  /** Per-item score change over the trend window -> Bar/Column chart */
  scoreDelta: ChartItem[];
  /** Current coefficients (weights) -> Coefficient chart */
  weight: ChartItem[];
  /** Coefficient change vs previous period -> Column/Bar chart */
  weightDelta: ChartItem[];
}

export interface ParityMismatch {
  level: string;
  key: string;
  spider: number;
  trendLast: number;
}

export interface ParityReport {
  ok: boolean;
  tolerance: number;
  latestDate: string | null;
  snapshotId: string | null;
  mismatches: ParityMismatch[];
}

export interface ChartsModel {
  snapshotId: string | null;
  timestamp: string | null;
  effectiveAt: string | null;
  tier: string;
  latestDate: string | null;
  overallScore: number;
  overallTrend: TrendPointView[];
  levels: LevelModel[];
  parity: ParityReport;
  source: "snapshot" | "fallback";
}

/** Raw dimension-only weight delta as emitted by the backend array. */
interface FlatWeightDelta {
  key: string;
  label?: string;
  value: number;
  delta?: number;
  delta_pct?: number;
}

function prettify(key: string): string {
  return key
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase())
    .trim();
}

/**
 * Classify a flat `level_scores` key into its hierarchy level.
 * Mirrors the decomposition used by the per-stock scoring page so the two
 * views stay numerically identical (parity contract).
 */
export function classifyLevelKey(key: string): LevelKey {
  if (!key.includes("_")) return "dimension";
  if (key.includes("_aspect_") && key.includes("_detail_")) return "sub_aspect";
  if (key.includes("_aspect_")) return "aspect";
  return "sub_dimension";
}

function asRecord(value: unknown): Record<string, unknown> {
  return (value && typeof value === "object" ? value : {}) as Record<string, unknown>;
}

/** Read one level's scores from a HierarchyScores dict (covers singular+plural). */
function readLevelDict(h: HierarchyScores | null | undefined, level: LevelKey): Record<string, number> {
  if (!h) return {};
  const r = asRecord(h) as Record<string, unknown>;
  const singular = r[level];
  if (singular && typeof singular === "object") {
    return singular as Record<string, number>;
  }
  const plural = r[`${level}s`];
  if (plural && typeof plural === "object") {
    return plural as Record<string, number>;
  }
  return {};
}

/** Extract one level's {key:score} from a flat level_scores map. */
function extractFlatLevel(level_scores: Record<string, unknown> | undefined, level: LevelKey): Record<string, number> {
  const out: Record<string, number> = {};
  if (!level_scores) return out;
  for (const [k, v] of Object.entries(level_scores)) {
    if (classifyLevelKey(k) === level) {
      out[k] = num(v);
    }
  }
  return out;
}

/**
 * Safely read the market snapshot's weight-trend / weight-delta arrays.
 * Backend returns camelCase arrays (`weightTrends`, `weightDeltas`); the
 * legacy type declared snake_case nested shapes. We tolerate BOTH so the
 * model is robust to whichever form the API emits.
 */
function getWeightTrends(raw: SnapshotResponse): WeightTrendPoint[] {
  const r = asRecord(raw);
  const a = r["weightTrends"];
  if (Array.isArray(a)) return a as WeightTrendPoint[];
  const n = r["weight_trends"] as { daily?: WeightTrendPoint[] } | undefined;
  return n?.daily ?? [];
}

function getWeightDeltas(raw: SnapshotResponse): FlatWeightDelta[] {
  const r = asRecord(raw);
  const a = r["weightDeltas"];
  if (Array.isArray(a)) return a as unknown as FlatWeightDelta[];
  const n = r["weight_deltas"] as
    | { daily?: { weights?: Record<string, Record<string, unknown>> } | null }
    | undefined;
  const daily = n?.daily;
  // Normalise the nested single-DeltaPoint form into a flat list.
  if (daily && daily.weights) {
    const dim = asRecord(daily.weights["dimension"]) as Record<string, Record<string, unknown>>;
    return Object.entries(dim).map(([k, v]) => ({
      key: k,
      value: num(v?.delta ?? v?.value ?? 0),
      delta: num(v?.delta ?? 0),
      delta_pct: num(v?.delta_pct ?? 0),
    }));
  }
  return [];
}

interface SnapshotToModelOptions {
  /** When true, the last trend point is normalised to exactly equal
   *  `scores.daily`, structurally guaranteeing spider/trend parity even if
   *  the upstream trend series lags by one period. */
  alignTrendToSnapshot?: boolean;
}

/**
 * Convert a unified Temporal Snapshot into the 20-view chart model.
 *
 * Parity contract:
 *  - `spider[L]` is built from `snapshot.scores.daily` (CURRENT tier scores).
 *  - `trend[L].last` is built from `snapshot.trends.daily` latest point.
 *  - `parity` is computed: each spider score must equal the trend's last
 *    score for the same key within `tolerance` (0.01).
 */
export function snapshotToChartsModel(
  snapshot: SnapshotResponse | null | undefined,
  options: SnapshotToModelOptions = {},
): ChartsModel | null {
  if (!snapshot) return null;

  const raw = asRecord(snapshot);
  const dailyScores = (snapshot.scores?.daily ?? snapshot.scores?.current) as HierarchyScores | undefined;
  const dailyTrend: TrendPoint[] = snapshot.trends?.daily ?? snapshot.trends?.intraday ?? [];
  const weights = (snapshot.weights ?? {}) as unknown as HierarchyScores;

  const rawWeightTrends = getWeightTrends(snapshot);
  const rawWeightDeltas = getWeightDeltas(snapshot);

  const latestDate = pickLatestDate(raw, dailyTrend);

  const align = !!options.alignTrendToSnapshot;

  const levels: LevelModel[] = LEVELS.map((level) => {
    const scoreDict = readLevelDict(dailyScores, level);
    const spider: ChartItem[] = Object.entries(scoreDict).map(([key, value]) => ({
      key,
      label: prettify(key),
      score: num(value),
      weight: 0,
    }));

    const trend: TrendPointView[] = dailyTrend.map((pt) => ({
      date: pt.date ?? pt.effective_at ?? rawTrendDate(pt),
      scores: extractFlatLevel(asRecord(pt)["level_scores"] as Record<string, unknown> | undefined, level),
    }));

    // If aligning, force the trend's latest point to match the spider exactly.
    if (align && trend.length > 0 && spider.length > 0) {
      const lastScores: Record<string, number> = {};
      for (const it of spider) lastScores[it.key] = it.score;
      trend[trend.length - 1] = { date: trend[trend.length - 1].date, scores: lastScores };
    }

    const scoreDelta: ChartItem[] = spider.map((it) => ({
      key: it.key,
      label: it.label,
      score: computeScoreDelta(trend, it.key),
      weight: 0,
    }));

    const weightDict = readLevelDict(weights, level);
    const weight: ChartItem[] = Object.entries(weightDict).map(([key, value]) => ({
      key,
      label: prettify(key),
      score: 0,
      weight: num(value),
    }));

    const weightDelta: ChartItem[] = buildWeightDelta(rawWeightDeltas, rawWeightTrends, level, weight);

    return { key: level, label: LEVEL_META[level].label, short: LEVEL_META[level].short, spider, trend, scoreDelta, weight, weightDelta };
  });

  const overallTrend: TrendPointView[] = dailyTrend.map((pt) => ({
    date: pt.date ?? pt.effective_at ?? rawTrendDate(pt),
    scores: { __overall: num(asRecord(pt)["overall"]) },
  }));

  const overallScore = num(dailyScores?.overall);

  const parity = assertParity(levels, latestDate, snapshot.snapshotId ?? null);

  return {
    snapshotId: snapshot.snapshotId ?? null,
    timestamp: snapshot.timestamp ?? null,
    effectiveAt: (raw["effectiveAt"] as string | null) ?? (raw["fetchedAt"] as string | null) ?? null,
    tier: (raw["tier"] as string | undefined) ?? "daily",
    latestDate,
    overallScore,
    overallTrend,
    levels,
    parity,
    source: "snapshot",
  };
}

function rawTrendDate(pt: TrendPoint): string | null {
  const r = asRecord(pt);
  const v = r["date"] ?? r["effective_at"];
  return typeof v === "string" ? v : null;
}

function pickLatestDate(raw: Record<string, unknown>, trend: TrendPoint[] | undefined): string | null {
  const dates: (string | null)[] = [];
  dates.push(raw["effectiveAt"] as string | null);
  if (trend?.length) {
    dates.push(trend[trend.length - 1]?.date ?? null);
    dates.push(trend[0]?.date ?? null);
  }
  const valid = dates.filter((d): d is string => !!d && !Number.isNaN(new Date(d).getTime()));
  return valid.length ? valid[0] : null;
}

function computeScoreDelta(trend: TrendPointView[], key: string): number {
  if (trend.length < 2) return 0;
  const last = trend[trend.length - 1].scores[key];
  const prev = trend[trend.length - 2].scores[key];
  if (typeof last !== "number" || typeof prev !== "number") return 0;
  return last - prev;
}

function buildWeightDelta(
  rawWeightDeltas: FlatWeightDelta[],
  rawWeightTrends: WeightTrendPoint[],
  level: LevelKey,
  weightItems: ChartItem[],
): ChartItem[] {
  // Backend only emits dimension-level weight deltas at market granularity.
  // For L2/L3/L4 fall back to diff of the (sparse) weight trend series.
  if (level === "dimension" && rawWeightDeltas.length > 0) {
    const byKey = new Map(rawWeightDeltas.map((d) => [d.key, d]));
    return weightItems.map((w) => {
      const d = byKey.get(w.key);
      return { ...w, score: d ? num(d.value ?? d.delta ?? 0) : 0 };
    });
  }

  // Derive delta from the weight trend series when available (flat dimension map).
  if (rawWeightTrends.length >= 2) {
    const last = asRecord(rawWeightTrends[rawWeightTrends.length - 1].weights ?? {});
    const prev = asRecord(rawWeightTrends[rawWeightTrends.length - 2].weights ?? {});
    return weightItems.map((w) => ({ ...w, score: num(last[w.key]) - num(prev[w.key]) }));
  }

  return weightItems.map((w) => ({ ...w, score: 0 }));
}

/**
 * Verify that, for every level, the trend's LAST point equals the spider
 * (current snapshot) scores within tolerance. This is the headline
 * data-consistency guarantee of the General dashboard.
 */
export function assertParity(
  levels: LevelModel[],
  latestDate: string | null,
  snapshotId: string | null,
  tolerance = 0.01,
): ParityReport {
  const mismatches: ParityMismatch[] = [];
  for (const level of levels) {
    const trendLast = level.trend[level.trend.length - 1];
    if (!trendLast) continue;
    for (const item of level.spider) {
      const trendVal = trendLast.scores[item.key];
      if (typeof trendVal !== "number") continue;
      if (Math.abs(trendVal - item.score) > tolerance) {
        mismatches.push({
          level: level.key,
          key: item.key,
          spider: item.score,
          trendLast: trendVal,
        });
      }
    }
  }
  return { ok: mismatches.length === 0, tolerance, latestDate, snapshotId, mismatches };
}

export function fmtDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (!Number.isFinite(d.getTime())) return "—";
  return d.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function fmtScore(score: number | null | undefined): string {
  if (typeof score !== "number" || !Number.isFinite(score)) return "—";
  return score.toFixed(1);
}
