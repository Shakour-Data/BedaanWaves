/**
 * Flexible type definitions and accessor functions for working with
 * hierarchy scores, trend points, and weights that may come in multiple
 * shapes (snapshot Record-based vs legacy array-based formats).
 *
 * These replace `any` casts throughout the scoring and chart code.
 */

import { num } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Flexible hierarchy types
// ---------------------------------------------------------------------------

export interface FlexHierarchyItem {
  key?: string;
  level_key?: string;
  label?: string;
  name?: string;
  score?: number;
  value?: number;
  level_score?: number;
  weight?: number;
  coefficient?: number;
  w?: number;
}

/**
 * A hierarchy bucket can be either an array of items (legacy format)
 * or a Record<string, number> (snapshot format).
 */
export type FlexHierarchyBucket = FlexHierarchyItem[] | Record<string, number>;

/**
 * Union of all known shapes for hierarchy scores flowing through the UI.
 *
 * - Snapshot (dashboard.ts): `{ overall, dimension, sub_dimension, aspect, sub_aspect }`
 * - Legacy (scoring.ts):     `{ overallScore, grade, level1, level2, level3, level4 }`
 * - Extended legacy:         `{ OVERALL: { score }, dimensions, sub_dimensions, aspects, sub_aspects }`
 */
export interface FlexHierarchyScores {
  // Snapshot shape
  overall?: number | null | { score?: number; grade?: string };
  dimension?: Record<string, number>;
  sub_dimension?: Record<string, number>;
  aspect?: Record<string, number>;
  sub_aspect?: Record<string, number>;
  // Legacy shape
  overallScore?: number;
  grade?: string;
  level1?: FlexHierarchyBucket;
  level2?: FlexHierarchyBucket;
  level3?: FlexHierarchyBucket;
  level4?: FlexHierarchyBucket;
  // Extended legacy
  OVERALL?: { score?: number };
  dimensions?: FlexHierarchyBucket;
  sub_dimensions?: FlexHierarchyBucket;
  aspects?: FlexHierarchyBucket;
  sub_aspects?: FlexHierarchyBucket;
  [key: string]: unknown;
}

// ---------------------------------------------------------------------------
// Flexible trend types
// ---------------------------------------------------------------------------

export interface FlexTrendPoint {
  date?: string;
  effective_at?: string;
  time?: string;
  overall?: number;
  value?: number;
  level_scores?: Record<string, number>;
  scores?: Record<string, number>;
  dimension_scores?: Record<string, number>;
  sub_dimension_scores?: Record<string, number>;
  aspect_scores?: Record<string, number>;
  sub_aspect_scores?: Record<string, number>;
  [key: string]: unknown;
}

// ---------------------------------------------------------------------------
// Flexible weight types
// ---------------------------------------------------------------------------

export interface FlexWeightItem {
  key?: string;
  level_key?: string;
  label?: string;
  name?: string;
  weight?: number;
  value?: number;
}

export type FlexWeightBucket = FlexWeightItem[] | Record<string, number>;

export interface FlexWeights {
  overall?: number;
  // Long keys (legacy array format)
  level1?: FlexWeightBucket;
  level2?: FlexWeightBucket;
  level3?: FlexWeightBucket;
  level4?: FlexWeightBucket;
  // Short keys (snapshot Record format)
  dimension?: Record<string, number>;
  sub_dimension?: Record<string, number>;
  aspect?: Record<string, number>;
  sub_aspect?: Record<string, number>;
  [key: string]: unknown;
}

export interface FlexWeightDeltaEntry {
  delta?: number;
  delta_pct?: number;
  change?: number;
}

export interface FlexWeightDeltas {
  delta?: number;
  delta_pct?: number;
  weights?:
    | Record<string, FlexWeightDeltaEntry>
    | Record<string, FlexWeightBucket>;
  overall?: FlexWeightDeltaEntry;
  // Long keys
  level1?: FlexWeightBucket;
  level2?: FlexWeightBucket;
  level3?: FlexWeightBucket;
  level4?: FlexWeightBucket;
  // Short keys
  dimension?: Record<string, number>;
  sub_dimension?: Record<string, number>;
  aspect?: Record<string, number>;
  sub_aspect?: Record<string, number>;
  // Delta buckets
  dimension_deltas?: Record<string, FlexWeightDeltaEntry>;
  sub_dimension_deltas?: Record<string, FlexWeightDeltaEntry>;
  aspect_deltas?: Record<string, FlexWeightDeltaEntry>;
  sub_aspect_deltas?: Record<string, FlexWeightDeltaEntry>;
  [key: string]: unknown;
}

// ---------------------------------------------------------------------------
// Accessor helpers (replace all `as any` property access)
// ---------------------------------------------------------------------------

/** Extract a numeric overall score from any hierarchy shape. */
export function flexPickOverall(h: FlexHierarchyScores): number {
  if (h.overall != null) {
    if (typeof h.overall === "number") return num(h.overall);
    if (typeof h.overall === "object" && h.overall.score != null)
      return num(h.overall.score);
  }
  if (h.overallScore != null) return num(h.overallScore);
  if (h.OVERALL?.score != null) return num(h.OVERALL.score);
  return 0;
}

const LEVEL_LONG_KEY = {
  1: "level1",
  2: "level2",
  3: "level3",
  4: "level4",
} as const;

const LEVEL_SHORT_KEY: Record<Exclude<number, 0>, string> = {
  1: "dimension",
  2: "sub_dimension",
  3: "aspect",
  4: "sub_aspect",
};

/**
 * Extract an array of normalised items from a hierarchy at a given level.
 * Handles both array-format and Record-format buckets.
 */
export function flexLevelItems(
  hierarchy: FlexHierarchyScores,
  level: number,
): Array<{ key: string; label: string; score: number; weight: number }> {
  const longKey = LEVEL_LONG_KEY[level as keyof typeof LEVEL_LONG_KEY];
  const shortKey = LEVEL_SHORT_KEY[level];

  const raw =
    (longKey ? hierarchy[longKey] : undefined) ??
    (shortKey ? hierarchy[shortKey] : undefined);

  if (!raw) return [];

  if (Array.isArray(raw)) {
    return raw.map((it) => ({
      key: it.key ?? it.level_key ?? it.label ?? String(Math.random()).slice(2),
      label: it.label ?? it.name ?? it.key ?? "Item",
      score: num(it.score ?? it.value ?? it.level_score ?? 0),
      weight: num(it.weight ?? it.coefficient ?? it.w ?? 0),
    }));
  }

  if (typeof raw === "object") {
    return Object.entries(raw as Record<string, number>).map(([k, v]) => ({
      key: k,
      label: k.replace(/_/g, " "),
      score: num(v),
      weight: 0,
    }));
  }

  return [];
}

/**
 * Extract a weight bucket as a normalised array.
 */
export function flexWeightItems(
  weights: FlexWeights,
  level: number,
): Array<{ key: string; label: string; weight: number }> {
  if (level === 0) return [{ key: "overall", label: "Overall", weight: 1.0 }];

  const longKey = LEVEL_LONG_KEY[level as keyof typeof LEVEL_LONG_KEY];
  const shortKey = LEVEL_SHORT_KEY[level];

  const raw =
    (longKey ? weights[longKey] : undefined) ??
    (shortKey ? weights[shortKey] : undefined);

  if (!raw) return [];

  if (Array.isArray(raw)) {
    return raw.map((it) => ({
      key: it.key ?? it.level_key ?? it.label ?? "",
      label: it.label ?? it.name ?? it.key ?? "",
      weight: num(it.weight ?? it.value ?? 0),
    }));
  }

  if (typeof raw === "object") {
    return Object.entries(raw as Record<string, number>).map(([k, v]) => ({
      key: k,
      label: k.replace(/_/g, " "),
      weight: num(v),
    }));
  }

  return [];
}

/**
 * Find the weight value for a specific key at a given level from a
 * WeightTrendPoint's weights object.
 */
export function flexTrendWeightValue(
  ptWeights: FlexWeights,
  level: number,
  targetKey: string,
): number {
  const longKey = LEVEL_LONG_KEY[level as keyof typeof LEVEL_LONG_KEY];
  const shortKey = LEVEL_SHORT_KEY[level];

  const longBucket = longKey ? ptWeights[longKey] : undefined;
  if (Array.isArray(longBucket)) {
    const entry = longBucket.find(
      (b) => (b.key ?? b.level_key) === targetKey,
    );
    if (entry) return num(entry.weight ?? entry.value ?? 0);
  } else if (longBucket && typeof longBucket === "object") {
    const v = (longBucket as Record<string, unknown>)[targetKey];
    if (typeof v === "number") return v;
  }

  const shortBucket = shortKey ? ptWeights[shortKey] : undefined;
  if (shortBucket && typeof shortBucket === "object") {
    const v = (shortBucket as Record<string, unknown>)[targetKey];
    if (typeof v === "number") return v;
  }

  return 0;
}

/**
 * Get the delta bucket for a given level from a FlexWeightDeltas object.
 */
export function flexWeightDeltaBucket(
  weightDeltas: FlexWeightDeltas,
  level: number,
): Record<string, FlexWeightDeltaEntry> | undefined {
  const longKey = LEVEL_LONG_KEY[level as keyof typeof LEVEL_LONG_KEY];
  const shortKey = LEVEL_SHORT_KEY[level];

  // Try the weights sub-object first
  const wLong = longKey ? weightDeltas.weights?.[longKey] : undefined;
  if (wLong && typeof wLong === "object" && !Array.isArray(wLong)) {
    return wLong as Record<string, FlexWeightDeltaEntry>;
  }

  // Try delta-named keys
  const deltaKey = `${shortKey}_deltas`;
  const deltaBucket = weightDeltas[deltaKey];
  if (deltaBucket && typeof deltaBucket === "object" && !Array.isArray(deltaBucket)) {
    return deltaBucket as Record<string, FlexWeightDeltaEntry>;
  }

  // Try short key on weights
  const wShort = shortKey ? weightDeltas.weights?.[shortKey] : undefined;
  if (wShort && typeof wShort === "object" && !Array.isArray(wShort)) {
    return wShort as Record<string, FlexWeightDeltaEntry>;
  }

  return undefined;
}

/**
 * Extract the overall delta from a FlexWeightDeltas object.
 */
export function flexWeightOverallDelta(
  weightDeltas: FlexWeightDeltas,
): number {
  if (weightDeltas.delta != null) return num(weightDeltas.delta);
  if (weightDeltas.overall?.delta != null) return num(weightDeltas.overall.delta);
  return 0;
}

/**
 * Convert a snapshot's hierarchy scores into the legacy HierarchyScores
 * shape used by scoring.ts consumers.
 */
export function flexHierarchyToLegacy(
  scores: FlexHierarchyScores,
  timestamp: string,
): {
  overallScore: number;
  grade: string;
  timestamp: string;
  level1: Array<{ key: string; label: string; score: number; weight: number }>;
  level2: Array<{ key: string; label: string; score: number; weight: number }>;
  level3: Array<{ key: string; label: string; score: number; weight: number }>;
  level4: Array<{ key: string; label: string; score: number; weight: number }>;
} {
  const overall = flexPickOverall(scores);
  const grade =
    typeof scores.grade === "string"
      ? scores.grade
      : overall >= 70
        ? "STRONG_BUY"
        : overall >= 40
          ? "HOLD"
          : "STRONG_SELL";

  return {
    overallScore: overall,
    grade,
    timestamp,
    level1: flexLevelItems(scores, 1),
    level2: flexLevelItems(scores, 2),
    level3: flexLevelItems(scores, 3),
    level4: flexLevelItems(scores, 4),
  };
}

/**
 * Convert a snapshot's weights into a flat array of CoefficientItem-like
 * objects (one per level bucket entry).
 */
export function flexWeightsToLegacy(
  weights: FlexWeights,
): Array<{ level: 1 | 2 | 3 | 4; key: string; label: string; weight: number }> {
  const result: Array<{
    level: 1 | 2 | 3 | 4;
    key: string;
    label: string;
    weight: number;
  }> = [];

  for (const lvl of [1, 2, 3, 4] as const) {
    const items = flexWeightItems(weights, lvl);
    for (const it of items) {
      result.push({ level: lvl, ...it });
    }
  }

  return result;
}
