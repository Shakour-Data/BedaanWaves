/**
 * dashboard-api.ts
 * ---------------------------------------------------------------------------
 * لایه‌ی دسترسی به داده برای داشبورد. داده‌های زنده را از بک‌اند دریافت می‌کند.
 */

import { apiClient } from "@/lib/api";
import type { AssetRow, MarketStat, SignalRow, NewsItem } from "@/lib/dashboard-data";

export interface DashboardData {
  marketStats: MarketStat[];
  topMovers: AssetRow[];
  watchlist: AssetRow[];
  signals: SignalRow[];
  news: NewsItem[];
  live: boolean;
}

interface TseDashboardResponse {
  status: string;
  market: string;
  total_symbols: number;
  average_change_pct: number;
  top_gainers: { symbol: string; name: string; last_close: number; change_pct: number }[];
  top_losers: { symbol: string; name: string; last_close: number; change_pct: number }[];
  timestamp: string;
}

interface MarketOverviewResponse {
  status: string;
  market: string;
  total_assets: number;
  sectors: Record<string, number>;
  timestamp: string;
}

interface SignalsSummaryResponse {
  status: string;
  timestamp: string;
  total_signals: number;
  summary: Record<string, number>;
  average_confidence: Record<string, number>;
}

interface NewsResponse {
  status: string;
  count: number;
  data: { title: string; source: string; published_at: string }[];
}

interface WatchlistResponse {
  id: string;
  name: string;
  description: string | null;
  is_default: boolean;
  items: { asset: { symbol: string; name: string; market: string } }[];
}

interface LatestPricesResponse {
  status: string;
  timestamp: string;
  data: Record<string, { price: number; change_pct: number; volume: number }>;
}

function formatTimeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);
  if (minutes < 1) return "همین الان";
  if (minutes < 60) return `${minutes} دقیقه پیش`;
  if (hours < 24) return `${hours} ساعت پیش`;
  return `${days} روز پیش`;
}

async function fetchMarketStats(): Promise<MarketStat[]> {
  try {
    const [marketOverviewRes, tseDashboardRes] = await Promise.all([
      apiClient.get<MarketOverviewResponse>("/market/market-overview?market=NASDAQ").catch(() => null),
      apiClient.get<TseDashboardResponse>("/market/tse-dashboard").catch(() => null),
    ]);

    const marketOverview = marketOverviewRes?.data;
    const tseDashboard = tseDashboardRes?.data;

    const stats: MarketStat[] = [];

    if (tseDashboard?.status === "success") {
      stats.push(
        { label: "شاخص کل بورس", value: tseDashboard.total_symbols.toLocaleString("fa-IR"), changePct: tseDashboard.average_change_pct },
        { label: "بهترین کسب‌کننده", value: tseDashboard.top_gainers[0]?.change_pct.toFixed(2) + "٪", changePct: tseDashboard.top_gainers[0]?.change_pct ?? 0 },
      );
    }

    if (marketOverview?.status === "success") {
      stats.push(
        { label: "نمادهای فعال بورس", value: marketOverview.total_assets.toLocaleString("fa-IR"), changePct: 0 },
      );
    }

    return stats.length ? stats : [
      { label: "شاخص کل بورس", value: "—", changePct: 0 },
      { label: "نمادهای فعال", value: "—", changePct: 0 },
    ];
  } catch {
    return [
      { label: "شاخص کل بورس", value: "—", changePct: 0 },
      { label: "نمادهای فعال", value: "—", changePct: 0 },
    ];
  }
}

async function fetchTopMovers(): Promise<AssetRow[]> {
  try {
    const res = await apiClient.get<TseDashboardResponse>("/market/tse-dashboard");
    const data = res.data;
    if (data.status !== "success") return [];

    const map = (r: TseDashboardResponse["top_gainers"][number]): AssetRow => ({
      symbol: r.symbol, name: r.name, market: "TSE",
      price: r.last_close, changePct: r.change_pct });

    const gainers = (data.top_gainers ?? []).map(map);
    const losers = (data.top_losers ?? []).map(map);
    return [...gainers, ...losers].slice(0, 10);
  } catch {
    return [];
  }
}

async function fetchWatchlist(): Promise<AssetRow[]> {
  try {
    const watchlistsRes = await apiClient.get<WatchlistResponse[]>("/watchlists");
    const watchlists = watchlistsRes.data;
    const defaultWatchlist = watchlists.find((w) => w.is_default);
    if (!defaultWatchlist?.items?.length) return [];

    const symbols = defaultWatchlist.items.map((item) => item.asset.symbol);
    const pricesRes = await apiClient.get<LatestPricesResponse>(
      `/market/latest-prices?${symbols.map((s) => `symbols=${encodeURIComponent(s)}`).join("&")}`
    );
    const pricesData = pricesRes.data?.data ?? {};

    return defaultWatchlist.items
      .filter((item) => pricesData[item.asset.symbol])
      .map((item) => ({
        symbol: item.asset.symbol,
        name: item.asset.name,
        market: item.asset.market as AssetRow["market"],
        price: pricesData[item.asset.symbol].price,
        changePct: pricesData[item.asset.symbol].change_pct }));
  } catch {
    return [];
  }
}

async function fetchSignals(): Promise<SignalRow[]> {
  try {
    const res = await apiClient.get<SignalsSummaryResponse>("/analysis/signals-summary?min_confidence=0.6");
    const data = res.data;
    if (data.status !== "success") return [];

    const signalTypes = Object.entries(data.summary ?? {})
      .filter(([, count]) => Number(count) > 0)
      .sort(([, a], [, b]) => Number(b) - Number(a))
      .slice(0, 5)
      .map(([type]) => type);

    const allSignals: SignalRow[] = [];
    for (const type of signalTypes) {
      try {
        const typeRes = await apiClient.get<SignalsSummaryResponse>(`/analysis/signals-summary?min_confidence=0.6`);
        const typeData = typeRes.data;
        if (typeData?.status === "success") {
          const summary = typeData.summary;
          allSignals.push({
            symbol: `${type}`,
            type: type as SignalRow["type"],
            confidence: typeData.average_confidence?.[type] ?? 50,
            model: "ML" });
        }
      } catch {}
    }

    return allSignals.slice(0, 10);
  } catch {
    return [];
  }
}

async function fetchNews(): Promise<NewsItem[]> {
  try {
    const res = await apiClient.get<NewsResponse>("/news/market?limit=10");
    const data = res.data;
    if (data.status !== "success") return [];

    return (data.data ?? []).map((n) => ({
      title: n.title,
      source: n.source,
      time: formatTimeAgo(n.published_at) }));
  } catch {
    return [];
  }
}

export async function fetchDashboardData(): Promise<DashboardData> {
  const [marketStats, topMovers, watchlist, signals, news] = await Promise.all([
    fetchMarketStats(),
    fetchTopMovers(),
    fetchWatchlist(),
    fetchSignals(),
    fetchNews(),
  ]);

  const live = [marketStats, topMovers, watchlist, signals, news].some(
    (d) => Array.isArray(d) ? d.length > 0 : true
  );

  return {
    marketStats,
    topMovers,
    watchlist,
    signals,
    news,
    live };
}