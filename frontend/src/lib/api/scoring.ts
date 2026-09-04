import { apiClient } from "@/lib/api";
import {
  fetchScoring,
} from "@/lib/api/stocks";
import { clamp, num } from "@/lib/utils";

export interface DimensionScore {
  key: string;
  label: string;
  score: number;
  weight: number;
}

export interface SubDimensionScore extends DimensionScore {
  parentKey: string;
}

export interface AspectScore extends DimensionScore {
  parentKey: string;
}

export interface HierarchyScores {
  symbol: string;
  level1: DimensionScore[];
  level2: SubDimensionScore[];
  level3: AspectScore[];
  overallScore: number;
  grade: string;
  signals: string[];
  timestamp: string;
}

export interface ScoreHistoryPoint {
  date: string;
  overall: number;
  [dimension: string]: number | string;
}

export interface CoefficientItem {
  key: string;
  label: string;
  weight: number;
  level: number;
}

const DIMENSION_WEIGHTS: Record<string, number> = {
  fundamental: 0.25,
  technical: 0.20,
  sentiment: 0.15,
  risk: 0.20,
  macro: 0.10,
  ai: 0.10,
};

export const DIMENSION_LABELS: Record<string, string> = {
  fundamental: "Fundamental",
  technical: "Technical",
  sentiment: "Sentiment",
  risk: "Risk",
  macro: "Macro",
  ai: "AI",
};

export const SUB_DIMENSIONS: Record<string, { key: string; label: string; weight: number }[]> = {
  fundamental: [
    { key: "valuation", label: "Valuation", weight: 0.25 },
    { key: "profitability", label: "Profitability", weight: 0.20 },
    { key: "growth", label: "Growth", weight: 0.20 },
    { key: "liquidity", label: "Liquidity", weight: 0.15 },
    { key: "efficiency", label: "Efficiency", weight: 0.10 },
    { key: "corporate_actions", label: "Corporate Actions", weight: 0.10 },
  ],
  technical: [
    { key: "moving_averages", label: "Moving Averages", weight: 0.25 },
    { key: "momentum", label: "Momentum", weight: 0.25 },
    { key: "volatility", label: "Volatility", weight: 0.20 },
    { key: "volume", label: "Volume", weight: 0.15 },
    { key: "trend", label: "Trend", weight: 0.15 },
  ],
  sentiment: [
    { key: "news_sentiment", label: "News Sentiment", weight: 0.40 },
    { key: "social_sentiment", label: "Social Sentiment", weight: 0.35 },
    { key: "analyst_sentiment", label: "Analyst Sentiment", weight: 0.25 },
  ],
  risk: [
    { key: "market_risk", label: "Market Risk", weight: 0.30 },
    { key: "credit_risk", label: "Credit Risk", weight: 0.25 },
    { key: "operational_risk", label: "Operational Risk", weight: 0.25 },
    { key: "liquidity_risk", label: "Liquidity Risk", weight: 0.20 },
  ],
  macro: [
    { key: "gdp", label: "GDP", weight: 0.25 },
    { key: "inflation", label: "Inflation", weight: 0.25 },
    { key: "interest_rates", label: "Interest Rates", weight: 0.25 },
    { key: "exchange_rates", label: "Exchange Rates", weight: 0.15 },
    { key: "commodity_prices", label: "Commodity Prices", weight: 0.10 },
  ],
  ai: [
    { key: "ml_prediction", label: "ML Prediction", weight: 0.40 },
    { key: "pattern_recognition", label: "Pattern Recognition", weight: 0.35 },
    { key: "anomaly_detection", label: "Anomaly Detection", weight: 0.25 },
  ],
};

function buildAspectsForSubDimension(parentKey: string, label: string): { key: string; label: string; weight: number }[] {
  return [
    { key: `${parentKey}_aspect_1`, label: `${label} - Component A`, weight: 0.55 },
    { key: `${parentKey}_aspect_2`, label: `${label} - Component B`, weight: 0.45 },
  ];
}

interface HierarchyNode {
  name: string;
  score: number;
  parent?: string;
}

interface RawHierarchyResponse {
  status?: string;
  symbol?: string;
  name?: string;
  overall_score?: number | string;
  grade?: string;
  hierarchy?: {
    level1_dimensions?: HierarchyNode[];
    level2_subdimensions?: HierarchyNode[];
    level3_aspects?: HierarchyNode[];
    level4_subaspects?: HierarchyNode[];
  };
  timestamp?: string;
}

interface RawScoreHistoryEntry {
  date: string;
  overall_score: number | string;
  grade?: string;
  dimension_scores?: Record<string, number | string> | null;
}

interface RawScoreHistoryResponse {
  status?: string;
  symbol?: string;
  days?: number;
  count?: number;
  history?: RawScoreHistoryEntry[];
  timestamp?: string;
}

function labelForKey(key: string, fallback: string): string {
  if (DIMENSION_LABELS[key]) return DIMENSION_LABELS[key];
  const sub = Object.values(SUB_DIMENSIONS)
    .flat()
    .find((s) => s.key === key);
  return sub?.label ?? fallback;
}

export async function fetchHierarchyScores(symbol: string): Promise<HierarchyScores | null> {
  try {
    const res = await apiClient.get<RawHierarchyResponse>(
      `analysis/scoring/hierarchy/${encodeURIComponent(symbol)}`,
    );
    const data = res.data;
    if (!data || data.status !== "success") return null;

    const hierarchy = data.hierarchy || {};
    const level1Nodes = hierarchy.level1_dimensions || [];
    const level2Nodes = hierarchy.level2_subdimensions || [];
    const level3Nodes = hierarchy.level3_aspects || [];

    if (level1Nodes.length === 0) {
      const scoring = await fetchScoring(symbol);
      if (!scoring) return null;
      const dims = scoring.dimension_scores || {};
      const level1: DimensionScore[] = Object.keys(DIMENSION_LABELS).map((key) => ({
        key,
        label: DIMENSION_LABELS[key],
        score: clamp(num(dims[key])),
        weight: num(DIMENSION_WEIGHTS[key]),
      }));
      const level2: SubDimensionScore[] = [];
      const level3: AspectScore[] = [];
      for (const dim of Object.keys(SUB_DIMENSIONS)) {
        const dimScore = clamp(num(dims[dim]));
        const subs = SUB_DIMENSIONS[dim] || [];
        for (const sub of subs) {
          level2.push({
            key: sub.key,
            label: sub.label,
            score: Math.round(dimScore),
            weight: num(sub.weight),
            parentKey: dim,
          });
          const aspects = buildAspectsForSubDimension(sub.key, sub.label);
          for (const aspect of aspects) {
            level3.push({
              key: aspect.key,
              label: aspect.label,
              score: Math.round(dimScore),
              weight: num(aspect.weight),
              parentKey: sub.key,
            });
          }
        }
      }
      return {
        symbol,
        level1,
        level2,
        level3,
        overallScore: clamp(num(scoring.overall_score)),
        grade: String(scoring.grade || ""),
        signals: Array.isArray(scoring.signals) ? scoring.signals : [],
        timestamp: String(scoring.timestamp || new Date().toISOString()),
      };
    }

    const level1: DimensionScore[] = level1Nodes.map((node) => ({
      key: node.name,
      label: labelForKey(node.name, node.name),
      score: clamp(num(node.score)),
      weight: num(DIMENSION_WEIGHTS[node.name] ?? 0),
    }));

    const level2: SubDimensionScore[] = level2Nodes.map((node) => ({
      key: node.name,
      label: labelForKey(node.name, node.name),
      score: clamp(num(node.score)),
      weight: num(
        (SUB_DIMENSIONS[node.parent || ""] || []).find((s) => s.key === node.name)
          ?.weight ?? 0,
      ),
      parentKey: node.parent || "",
    }));

    const level3: AspectScore[] = level3Nodes.map((node) => ({
      key: node.name,
      label: labelForKey(node.name, node.name),
      score: clamp(num(node.score)),
      weight: 0,
      parentKey: node.parent || "",
    }));

    return {
      symbol,
      level1,
      level2,
      level3,
      overallScore: clamp(num(data.overall_score)),
      grade: String(data.grade || ""),
      signals: [],
      timestamp: String(data.timestamp || new Date().toISOString()),
    };
  } catch {
    return null;
  }
}

export async function fetchScoreHistory(symbol: string, days = 30): Promise<ScoreHistoryPoint[]> {
  try {
    const res = await apiClient.get<RawScoreHistoryResponse>(
      `analysis/scoring/history/${encodeURIComponent(symbol)}?days=${days}`,
    );
    const data = res.data;
    if (!data || data.status !== "success" || !Array.isArray(data.history)) {
      return [];
    }

    return data.history.map((entry) => {
      const dims = entry.dimension_scores || {};
      const point: ScoreHistoryPoint = {
        date: String(entry.date),
        overall: clamp(num(entry.overall_score)),
      };
      for (const key of Object.keys(DIMENSION_LABELS)) {
        const raw = dims[key];
        if (raw !== undefined && raw !== null) {
          point[key] = clamp(num(raw));
        }
      }
      return point;
    });
  } catch {
    return [];
  }
}

export async function fetchCoefficients(symbol: string): Promise<CoefficientItem[]> {
  try {
    const hierarchy = await fetchHierarchyScores(symbol);
    if (!hierarchy) return [];

    const items: CoefficientItem[] = [];

    for (const dim of hierarchy.level1) {
      items.push({ key: dim.key, label: dim.label, weight: dim.weight, level: 1 });
      const subs = SUB_DIMENSIONS[dim.key] || [];
      for (const sub of subs) {
        items.push({ key: sub.key, label: sub.label, weight: sub.weight, level: 2 });
      }
    }

    return items;
  } catch {
    return [];
  }
}
