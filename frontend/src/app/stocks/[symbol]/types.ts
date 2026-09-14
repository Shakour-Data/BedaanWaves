export interface QuotePayload {
  symbol?: string;
  price?: number;
  change?: number;
  change_pct?: number;
  volume?: number;
  open?: number;
  high?: number;
  low?: number;
  freshness_ts?: string;
}

export interface IntradayBar {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
}

export interface IntradayPayload {
  symbol?: string;
  interval?: string;
  bar?: IntradayBar;
  bars?: IntradayBar[];
}

export interface ScoreDelta {
  symbol?: string;
  overall_score?: number;
  overall_score_delta?: number;
  grade?: string;
  dimensions?: Record<string, number>;
}

export interface ScoringData {
  overall_score?: number;
  grade?: string;
  dimension_scores?: Record<string, number>;
  [key: string]: unknown;
}

export interface RiskData {
  [key: string]: string | number | null | undefined;
}

export interface FundamentalData {
  [key: string]: string | number | null | undefined;
}
