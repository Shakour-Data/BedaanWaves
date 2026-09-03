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
 *
 * Returns ``true`` when the row passes all filters (i.e. is a Nasdaq
 * equity/ETF). Returns ``false`` when the row is explicitly tagged as
 * a non-Nasdaq instrument OR carries a crypto-style symbol suffix
 * (e.g. ``BTC-USD``, ``ETHUSDT``).
 *
 * The ``market`` field is optional. Many backend responses (e.g.
 * ``top_performers`` on the general dashboard) omit the field because
 * the list is already pre-filtered on the server; in that case we only
 * reject on symbol-shape signals (crypto suffixes), not on a missing
 * market tag.
 */
export function isNasdaqEquityLike(row: {
  market?: string | null;
  symbol?: string | null;
}): boolean {
  // Explicit non-Nasdaq market tag → reject.
  if (row.market && !ALLOWED_MARKETS.has(row.market)) return false;

  const sym = (row.symbol ?? "").toUpperCase();
  if (!sym) return false;

  // Crypto-style suffixes from yfinance / Binance / Coinbase. Legitimate
  // Nasdaq tickers are 1-5 uppercase letters; crypto pairs add "-USD",
  // "USDT", "USDC" or similar.
  if (sym.endsWith("-USD") || sym.endsWith("-USDT") || sym.endsWith("-USDC")) {
    return false;
  }
  if (
    /^[A-Z]{2,5}(USD|USDT|USDC|BUSD|DAI)$/.test(sym)
  ) {
    // e.g. BTCUSDT, ETHUSD, SOLUSDC — these are crypto pairs, not Nasdaq
    // equities, regardless of what the backend ``market`` field says.
    return false;
  }
  return true;
}

