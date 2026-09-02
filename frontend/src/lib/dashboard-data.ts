/**
 * dashboard-data.ts
 * ---------------------------------------------------------------------------
 * Types + live-data fetchers for the dashboard.
 * Real data is pulled from the live backend endpoints; sample data
 * has been removed so the UI always reflects actual market state.
 *
 * The dashboard is hard-locked to instruments that participate in the
 * formation of the Nasdaq index. Any backend response that still
 * contains a non-Nasdaq instrument (a legacy row, a partial migration,
 * a test fixture, etc.) is dropped here before the UI ever sees it.
 */

export interface MarketStat {
  label: string;
  value: string;
  changePct?: number;
}

export interface AssetRow {
  symbol: string;
  name: string;
  market: "NASDAQ";
  price: number;
  changePct: number;
  quantity?: number;
  avg_price?: number;
}

export interface NewsItem {
  title: string;
  source: string;
  time: string;
}

const ALLOWED_MARKETS = new Set(["NASDAQ"]);

/**
 * Drop any row that is not a Nasdaq-listed equity or ETF. This is a
 * defense-in-depth filter that runs after every backend response. The
 * backend is supposed to enforce the same rule, but if a stale cache,
 * a partial migration, or a new endpoint ever leaks a non-Nasdaq row,
 * the UI will not surface it.
 */
export function isNasdaqEquityLike(row: {
  market?: string | null;
  symbol?: string | null;
}): boolean {
  if (row.market && !ALLOWED_MARKETS.has(row.market)) return false;
  const sym = (row.symbol ?? "").toUpperCase();
  // yfinance's crypto tickers use suffixes like "-USD" (BTC-USD); filter
  // those out even if the backend says "NASDAQ" (defense in depth).
  if (sym.endsWith("-USD") || sym.endsWith("USD")) {
    // Keep legit "USD" pairs from real Nasdaq-listed ETFs (e.g. "USD" by
    // itself is not a real ticker) — but drop crypto-style suffixes.
    if (sym.includes("-USD") || /^[A-Z]{2,5}USD$/.test(sym)) return false;
  }
  return true;
}

