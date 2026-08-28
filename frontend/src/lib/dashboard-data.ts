/**
 * dashboard-data.ts
 * ---------------------------------------------------------------------------
 * Types + live-data fetchers for the dashboard.
 * Real data is pulled from the live backend endpoints; sample data
 * has been removed so the UI always reflects actual market state.
 */

export interface MarketStat {
  label: string;
  value: string;
  changePct?: number;
}

export interface AssetRow {
  symbol: string;
  name: string;
  market: "TSE" | "OTC" | "BINANCE" | "CRYPTO" | "NASDAQ";
  price: number;
  changePct: number;
  quantity?: number;
  avg_price?: number;
}

export interface SignalRow {
  symbol: string;
  type: "BUY" | "SELL" | "HOLD" | "STRONG_BUY" | "STRONG_SELL";
  confidence: number;
  model: string;
}

export interface NewsItem {
  title: string;
  source: string;
  time: string;
}
