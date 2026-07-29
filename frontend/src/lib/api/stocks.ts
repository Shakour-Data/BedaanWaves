/**
 * stocks.ts
 * ---------------------------------------------------------------------------
 * لایه‌ی دسترسی به داده‌ی «سهام» (symbols, price-history, latest-prices).
 * این endpointها روی پایگاهِ seed شده‌ی بک‌اند داده‌ی واقعی برمی‌گردانند.
 * مقادیر عددی ممکن است به‌صورت رشته (Decimal) یا عدد سریالایز شوند؛ به همین
 * دلیل همه‌جا با `num()` به عدد تبدیل می‌شوند.
 */

import { apiClient } from "@/lib/api";

/* ------------------------------ Types ------------------------------------ */

export type AssetClass = "EQUITY" | "ETF" | "CRYPTO" | "COMMODITY" | "BOND" | "INDEX";
export type Market = "TSE" | "OTC" | "BINANCE" | "KRAKEN" | "COINBASE" | "NYSE" | "NASDAQ";
export type Timeframe = "1m" | "5m" | "15m" | "1h" | "4h" | "1d" | "1w" | "1M";

/** پاسخِ `GET /market/symbols` */
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

/** یک کندلِ OHLCV پس از نرمال‌سازی به `number` */
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

/** آمار لحظه‌ای یک نماد از `GET /market/latest-prices` */
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

function num(value: number | string | null | undefined): number {
  if (value === null || value === undefined) return 0;
  const n = typeof value === "number" ? value : parseFloat(value);
  return Number.isFinite(n) ? n : 0;
}

/* --------------------------------- API ----------------------------------- */

export interface FetchSymbolsParams {
  assetClass?: AssetClass;
  market?: Market;
  sector?: string;
  industry?: string;
  limit?: number;
}

/** فهرست نمادهای قابل معامله (با فیلترهای اختیاری). */
export async function fetchSymbols(params: FetchSymbolsParams = {}): Promise<Asset[]> {
  const qs = new URLSearchParams();
  if (params.assetClass) qs.set("asset_class", params.assetClass);
  if (params.market) qs.set("market", params.market);
  if (params.sector) qs.set("sector", params.sector);
  if (params.industry) qs.set("industry", params.industry);
  qs.set("limit", String(params.limit ?? 500));
  return apiClient.get<Asset[]>(`/market/symbols?${qs.toString()}`);
}

/** مشخصات یک نماد بر اساس symbol (از فهرست symbols). */
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

/** تاریخچه‌ی OHLCV یک نماد (مرتب‌شده صعودی بر اساس زمان). */
export async function fetchPriceHistory({
  symbol,
  timeframe = "1d",
  limit = 500,
}: FetchPriceHistoryParams): Promise<Candle[]> {
  const qs = new URLSearchParams({
    symbol,
    timeframe,
    limit: String(limit),
  });
  const raw = await apiClient.get<RawCandle[]>(`/market/price-history?${qs.toString()}`);
  return raw.map((c) => ({
    timestamp: c.timestamp,
    timeframe: c.timeframe,
    open: num(c.open),
    high: num(c.high),
    low: num(c.low),
    close: num(c.close),
    volume: num(c.volume),
    turnover: c.turnover === undefined || c.turnover === null ? null : num(c.turnover),
    transactions: c.transactions ?? null,
  }));
}

/** آخرین قیمت‌ها برای چند نماد. */
export async function fetchLatestPrices(symbols: string[]): Promise<Record<string, LatestPrice>> {
  if (symbols.length === 0) return {};
  const qs = symbols.map((s) => `symbols=${encodeURIComponent(s)}`).join("&");
  const res = await apiClient.get<RawLatestPricesResponse>(`/market/latest-prices?${qs}`);
  const out: Record<string, LatestPrice> = {};
  for (const [symbol, v] of Object.entries(res.data ?? {})) {
    out[symbol] = {
      symbol,
      price: num(v.price),
      change: num(v.change),
      change_pct: num(v.change_pct),
      volume: num(v.volume),
      timestamp: v.timestamp,
    };
  }
  return out;
}

/** آخرین قیمتِ یک نماد. */
export async function fetchLatestPrice(symbol: string): Promise<LatestPrice | null> {
  try {
    const map = await fetchLatestPrices([symbol]);
    return map[symbol] ?? null;
  } catch {
    return null;
  }
}
