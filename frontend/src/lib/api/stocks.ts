/**
 * stocks.ts
 * ---------------------------------------------------------------------------
 * Data access layer for "stocks" (symbols, price-history, latest-prices).
 * These endpoints return real data from the seeded backend database.
 * Numeric values may be serialized as strings (Decimal) or numbers; for that
 * reason `num()` is used everywhere to convert to a number.
 */

import { apiClient } from "@/lib/api";
import { num } from "@/lib/utils";

/* ------------------------------ Types ------------------------------------ */

export type AssetClass = "EQUITY" | "ETF";
export type Market = "NASDAQ";
export type Timeframe = "1m" | "5m" | "15m" | "1h" | "4h" | "1d" | "1w" | "1M";

/** Response of `GET /market/symbols` */
export interface Asset {
  id: string;
  symbol: string;
  name: string;
  asset_class: AssetClass;
  market: Market;
  sector: string | null;
  sub_sector: string | null;
  country_code: string | null;
  currency: string;
  active: boolean;
  created_at: string;
  updated_at: string;
}

/** A single OHLCV candle normalized to `number` */
export interface Candle {
  timestamp: string;
  timeframe: Timeframe;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  turnover: number | null;
  transactions: number | null;
}

/** Real-time stats for a symbol from `GET /market/latest-prices` */
export interface LatestPrice {
  symbol: string;
  price: number;
  change: number;
  change_pct: number;
  volume: number;
  timestamp: string;
}

/* ---------------------------- Raw payloads -------------------------------- */

interface RawCandle {
  timestamp: string;
  timeframe: Timeframe;
  open: number | string;
  high: number | string;
  low: number | string;
  close: number | string;
  volume: number | string;
  turnover?: number | string | null;
  transactions?: number | null;
}

interface RawLatestPricesResponse {
  status: string;
  timestamp: string;
  data: Record<
    string,
    {
      price: number | string;
      change: number | string;
      change_pct: number | string;
      volume: number | string;
      timestamp: string;
    }
  >;
}

/* ------------------------------ Helpers ---------------------------------- */

/* --------------------------------- API ----------------------------------- */

export interface FetchSymbolsParams {
  assetClass?: AssetClass;
  market?: Market;
  sector?: string;
  industry?: string;
  limit?: number;
}

/** List of tradable symbols (with optional filters). */
export async function fetchSymbols(params: FetchSymbolsParams = {}): Promise<Asset[]> {
  const qs = new URLSearchParams();
  if (params.assetClass) qs.set("asset_class", params.assetClass);
  if (params.market) qs.set("market", params.market);
  if (params.sector) qs.set("sector", params.sector);
  if (params.industry) qs.set("industry", params.industry);
  qs.set("limit", String(params.limit ?? 500));
  const res = await apiClient.get<Asset[]>(`market/symbols?${qs.toString()}`);
  return res.data;
}

/** Properties of a symbol by symbol (from the symbols list). */
export async function fetchAsset(symbol: string): Promise<Asset | null> {
  try {
    const all = await fetchSymbols({ limit: 1000 });
    const target = symbol.toUpperCase();
    return all.find((a) => a.symbol.toUpperCase() === target) ?? null;
  } catch {
    return null;
  }
}

export interface FetchPriceHistoryParams {
  symbol: string;
  timeframe?: Timeframe;
  limit?: number;
}

/** OHLCV history of a symbol (sorted ascending by time). */
export async function fetchPriceHistory({
  symbol,
  timeframe = "1d",
  limit = 500 }: FetchPriceHistoryParams): Promise<Candle[]> {
  const qs = new URLSearchParams({
    symbol,
    timeframe,
    limit: String(limit),
  });
  const res = await apiClient.get<RawCandle[]>(`market/price-history?${qs.toString()}`);
  return res.data.map((c) => ({
    timestamp: c.timestamp,
    timeframe: c.timeframe,
    open: num(c.open),
    high: num(c.high),
    low: num(c.low),
    close: num(c.close),
    volume: num(c.volume),
    turnover: c.turnover === undefined || c.turnover === null ? null : num(c.turnover),
    transactions: c.transactions ?? null }));
}

/** Latest prices for multiple symbols. */
export async function fetchLatestPrices(symbols: string[]): Promise<Record<string, LatestPrice>> {
  if (symbols.length === 0) return {};
  const qs = symbols.map((s) => `symbols=${encodeURIComponent(s)}`).join("&");
  const res = await apiClient.get<RawLatestPricesResponse>(`market/latest-prices?${qs}`);

  const out: Record<string, LatestPrice> = {};
  for (const [symbol, v] of Object.entries(res.data.data ?? {})) {
    out[symbol] = {
      symbol,
      price: num(v.price),
      change: num(v.change),
      change_pct: num(v.change_pct),
      volume: num(v.volume),
      timestamp: v.timestamp };
  }
  return out;
}

/** Latest price of a single symbol. */
export async function fetchLatestPrice(symbol: string): Promise<LatestPrice | null> {
  try {
    const map = await fetchLatestPrices([symbol]);
    return map[symbol] ?? null;
  } catch {
    return null;
  }
}

/** 6-dimensional scoring of a symbol. */
export async function fetchScoring(symbol: string): Promise<any | null> {
  try {
    const res = await apiClient.get<any>(`analysis/scoring/${encodeURIComponent(symbol)}`);
    return res.data?.scoring ?? null;
  } catch {
    return null;
  }
}

/** Fundamental analysis of a symbol. */
export async function fetchFundamental(symbol: string): Promise<any | null> {
  try {
    const res = await apiClient.get<any>(`analysis/fundamental/${encodeURIComponent(symbol)}`);
    return res.data?.fundamental ?? null;
  } catch {
    return null;
  }
}

/** Technical analysis of a symbol. */
export async function fetchTechnical(symbol: string): Promise<any | null> {
  try {
    const res = await apiClient.get<any>(`analysis/technical/${encodeURIComponent(symbol)}`);
    return res.data?.indicators ?? null;
  } catch {
    return null;
  }
}

/** Risk analysis of a symbol. */
export async function fetchRisk(symbol: string): Promise<any | null> {
  try {
    const res = await apiClient.get<any>(`analysis/risk/${encodeURIComponent(symbol)}`);
    return res.data?.risk ?? null;
  } catch {
    return null;
  }
}

/** Sentiment analysis of a symbol. */
export async function fetchSentiment(symbol: string): Promise<any | null> {
  try {
    const res = await apiClient.get<any>(`analysis/sentiment/${encodeURIComponent(symbol)}`);
    return res.data?.sentiment ?? null;
  } catch {
    return null;
  }
}
