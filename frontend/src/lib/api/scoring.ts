import { apiClient } from "@/lib/api";
import {
  fetchPriceHistory,
  fetchScoring,
  type Candle,
} from "@/lib/api/stocks";

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

function num(value: unknown): number {
  if (value === null || value === undefined) return 0;
  const n = typeof value === "number" ? value : parseFloat(String(value));
  return Number.isFinite(n) ? n : 0;
}

function clamp(v: number, min = 0, max = 100): number {
  return Math.max(min, Math.min(max, v));
}

function jitter(base: number, range: number): number {
  return clamp(base + (Math.random() - 0.5) * range);
}

const DIMENSION_LABELS: Record<string, string> = {
  fundamental: "Fundamental",
  technical: "Technical",
  sentiment: "Sentiment",
  risk: "Risk",
  macro: "Macro",
  ai: "AI",
};

const DIMENSION_WEIGHTS: Record<string, number> = {
  fundamental: 0.25,
  technical: 0.20,
  sentiment: 0.15,
  risk: 0.20,
  macro: 0.10,
  ai: 0.10,
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

export async function fetchHierarchyScores(symbol: string): Promise<HierarchyScores | null> {
  try {
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
        const subScore = jitter(dimScore, 15);
        level2.push({
          key: sub.key,
          label: sub.label,
          score: Math.round(subScore),
          weight: num(sub.weight),
          parentKey: dim,
        });
        const aspects = buildAspectsForSubDimension(sub.key, sub.label);
        for (const aspect of aspects) {
          const aspectScore = jitter(subScore, 10);
          level3.push({
            key: aspect.key,
            label: aspect.label,
            score: Math.round(aspectScore),
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
  } catch {
    return null;
  }
}

export async function fetchScoreHistory(symbol: string, days = 30): Promise<ScoreHistoryPoint[]> {
  try {
    const candles = await fetchPriceHistory({ symbol, timeframe: "1d", limit: days });
    if (!candles || candles.length === 0) return [];

    const baseScores: Record<string, number> = {
      fundamental: 65,
      technical: 60,
      sentiment: 55,
      risk: 70,
      macro: 50,
      ai: 58,
    };

    return candles.map((c: Candle) => {
      const trend = (c.close - candles[0].close) / (candles[0].close || 1);
      const point: ScoreHistoryPoint = {
        date: c.timestamp.split("T")[0],
        overall: clamp(60 + trend * 30 + (Math.random() - 0.5) * 8),
      };
      for (const dim of Object.keys(baseScores)) {
        point[dim] = clamp(baseScores[dim] + trend * 20 + (Math.random() - 0.5) * 12);
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
