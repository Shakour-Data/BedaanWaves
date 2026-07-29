/**
 * dashboard-api.ts
 * ---------------------------------------------------------------------------
 * لایه‌ی دسترسی به داده برای داشبورد. داده‌های زنده را از بک‌اند (که روی
 * پایگاهِ seed شده اجرا می‌شود) دریافت می‌کند و در صورت در دسترس نبودن API،
 * به داده‌های نمایشی (mock) بازمی‌گردد تا داشبورد همیشه رندر شود.
 */

import { apiClient } from "@/lib/api";
import {
  marketStats as mockMarketStats,
  topMovers as mockTopMovers,
  watchlist as mockWatchlist,
  signals as mockSignals,
  news as mockNews,
  type AssetRow,
  type MarketStat,
  type SignalRow,
  type NewsItem,
} from "@/lib/dashboard-data";

export interface DashboardData {
  marketStats: MarketStat[];
  topMovers: AssetRow[];
  watchlist: AssetRow[];
  signals: SignalRow[];
  news: NewsItem[];
  /** true اگر حداقل بخشی از داده به‌صورت زنده از API دریافت شده باشد */
  live: boolean;
}

const WATCHLIST_SYMBOLS = mockWatchlist.map((w) => w.symbol);

interface TseDashboard {
  average_change_pct: number;
  total_symbols: number;
  top_gainers: { symbol: string; name: string; last_close: number; change_pct: number }[];
  top_losers: { symbol: string; name: string; last_close: number; change_pct: number }[];
}

async function fetchTopMovers(): Promise<AssetRow[] | null> {
  try {
    const data = await apiClient.get<TseDashboard>("/market/tse-dashboard");
    const map = (r: TseDashboard["top_gainers"][number]): AssetRow => ({
      symbol: r.symbol,
      name: r.name,
      market: "TSE",
      price: r.last_close,
      changePct: r.change_pct,
    });
    const gainers = (data.top_gainers ?? []).map(map);
    const losers = (data.top_losers ?? []).map(map);
    return [...gainers, ...losers].slice(0, 6);
  } catch {
    return null;
  }
}

async function fetchWatchlist(): Promise<AssetRow[] | null> {
  try {
    const res = await apiClient.get<{ data: Record<string, { price: number; change_pct: number }> }>(
      `/market/latest-prices?${WATCHLIST_SYMBOLS.map((s) => `symbols=${encodeURIComponent(s)}`).join("&")}`,
    );
    const prices = res.data ?? {};
    const rows = mockWatchlist
      .filter((w) => prices[w.symbol])
      .map((w) => ({
        ...w,
        price: prices[w.symbol].price,
        changePct: prices[w.symbol].change_pct,
      }));
    return rows.length ? rows : null;
  } catch {
    return null;
  }
}

export async function fetchDashboardData(): Promise<DashboardData> {
  const [movers, watch] = await Promise.all([fetchTopMovers(), fetchWatchlist()]);

  const live = movers !== null || watch !== null;

  return {
    marketStats: mockMarketStats,
    topMovers: movers ?? mockTopMovers,
    watchlist: watch ?? mockWatchlist,
    signals: mockSignals,
    news: mockNews,
    live,
  };
}
