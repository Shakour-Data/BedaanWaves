import type { Watchlist as WatchlistType } from "@/lib/api/watchlist";

export interface QuotePayload {
  symbol?: string;
  price?: number;
  change_pct?: number;
  change?: number;
}

export interface MarketStreamPayload {
  top_movers?: Array<{
    symbol: string;
    price?: number;
    change_pct?: number;
  }>;
  quotes?: Record<string, { price?: number; change_pct?: number }>;
}

export interface EnrichedWatchlistRow {
  symbol: string;
  name: string;
  market: "NASDAQ";
  price: number;
  changePct: number;
  watchlistItemId: string;
}

export type LiveQuotesMap = Record<string, { price: number; changePct: number; ts: number }>;

export type { WatchlistType };
