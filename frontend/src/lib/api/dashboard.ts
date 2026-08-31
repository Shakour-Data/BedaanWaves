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

export interface DimensionDashboardResponse {
  status: string;
  dimension: string;
  summary: {
    total_symbols: number;
    avg_score: number;
    best_symbol: string | null;
    best_score: number;
    worst_symbol: string | null;
    worst_score: number;
  };
  distribution: Array<{ range: string; count: number }>;
  symbols: Array<{
    symbol: string;
    name: string;
    sector: string | null;
    score: number;
    grade: string;
    sub_dimensions: Record<string, number>;
    aspects: Record<string, number>;
    sub_aspects: Record<string, number>;
  }>;
  top_performers: Array<{ symbol: string; name: string; score: number }>;
  bottom_performers: Array<{ symbol: string; name: string; score: number }>;
  timestamp: string;
}

export interface NewsDashboardResponse {
  status: string;
  dimension: string;
  summary: {
    total_symbols: number;
    total_news: number;
    avg_score: number;
    best_symbol: string | null;
    best_score: number;
    worst_symbol: string | null;
    worst_score: number;
  };
  symbols: Array<{
    symbol: string;
    name: string;
    sector: string | null;
    score: number;
    grade: string;
    news_count: number;
    avg_sentiment: number;
    positive_count: number;
    negative_count: number;
    neutral_count: number;
    latest_news: { title: string; source: string; published_at: string } | null;
  }>;
  top_performers: Array<{ symbol: string; name: string; score: number }>;
  bottom_performers: Array<{ symbol: string; name: string; score: number }>;
  timestamp: string;
}

export interface BoardDashboardResponse {
  status: string;
  dimension: string;
  summary: {
    total_symbols: number;
    avg_score: number;
    best_symbol: string | null;
    best_score: number;
    worst_symbol: string | null;
    worst_score: number;
    total_boards: number;
  };
  symbols: Array<{
    symbol: string;
    name: string;
    sector: string | null;
    score: number;
    board_count: number;
    officer_count: number;
    total_leaders: number;
    fundamental_score: number;
    grade: string;
  }>;
  top_performers: Array<{ symbol: string; name: string; score: number; board_count: number; officer_count: number }>;
  bottom_performers: Array<{ symbol: string; name: string; score: number; board_count: number; officer_count: number }>;
  timestamp: string;
}

export interface AiDashboardResponse {
  status: string;
  dimension: string;
  summary: {
    total_symbols: number;
    avg_score: number;
    best_symbol: string | null;
    best_score: number;
    worst_symbol: string | null;
    worst_score: number;
    total_signals: number;
  };
  symbols: Array<{
    symbol: string;
    name: string;
    sector: string | null;
    score: number;
    grade: string;
    signal_type: string | null;
    confidence: number;
    expected_return: number;
    risk_score: number;
    generated_at: string | null;
  }>;
  top_performers: Array<{ symbol: string; name: string; score: number }>;
  bottom_performers: Array<{ symbol: string; name: string; score: number }>;
  timestamp: string;
}

export interface GeneralDashboardResponse {
  status: string;
  summary: {
    total_symbols: number;
    total_signals: number;
    total_news: number;
  };
  dimensions: Record<string, { avg_score: number; count: number }>;
  symbols: Array<{
    symbol: string;
    name: string;
    sector: string | null;
    market: string;
    overall_score: number;
    grade: string;
    dimensions: Record<string, number>;
  }>;
  top_performers: Array<{ symbol: string; name: string; overall_score: number }>;
  bottom_performers: Array<{ symbol: string; name: string; overall_score: number }>;
  timestamp: string;
}

interface NasdaqDashboardResponse {
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
  if (minutes < 1) return "Just now";
  if (minutes < 60) return `${minutes} minutes ago`;
  if (hours < 24) return `${hours} hours ago`;
  return `${days} days ago`;
}

async function fetchMarketStats(): Promise<MarketStat[]> {
  const [marketOverviewRes, nasdaqDashboardRes] = await Promise.all([
    apiClient.get<MarketOverviewResponse>("market/market-overview?market=NASDAQ", { timeout: 60000 }),
    apiClient.get<NasdaqDashboardResponse>("market/nasdaq-dashboard", { timeout: 60000 }),
  ]);

  const marketOverview = marketOverviewRes.data;
  const nasdaqDashboard = nasdaqDashboardRes.data;

  const stats: MarketStat[] = [];

  if (nasdaqDashboard?.status === "success") {
    stats.push(
      { label: "Nasdaq Composite", value: nasdaqDashboard.total_symbols.toLocaleString("en-US"), changePct: nasdaqDashboard.average_change_pct ?? 0 },
      { label: "Top Gainer", value: nasdaqDashboard.top_gainers[0]?.symbol + " " + nasdaqDashboard.top_gainers[0]?.change_pct.toFixed(2) + "%", changePct: nasdaqDashboard.top_gainers[0]?.change_pct ?? 0 },
    );
  }

  if (marketOverview?.status === "success") {
    stats.push(
      { label: "Active Symbols", value: marketOverview.total_assets.toLocaleString("en-US"), changePct: 0 },
    );
  }

  return stats.length ? stats : [
    { label: "Nasdaq Composite", value: "—", changePct: 0 },
    { label: "Active Symbols", value: "—", changePct: 0 },
  ];
}

async function fetchTopMovers(): Promise<AssetRow[]> {
  const res = await apiClient.get<NasdaqDashboardResponse>("market/nasdaq-dashboard", { timeout: 60000 });
  const data = res.data;
  if (data.status !== "success") return [];

  const map = (r: NasdaqDashboardResponse["top_gainers"][number]): AssetRow => ({
    symbol: r.symbol, name: r.name, market: "NASDAQ",
    price: r.last_close, changePct: r.change_pct });

  const gainers = (data.top_gainers ?? []).map(map);
  const losers = (data.top_losers ?? []).map(map);
  return [...gainers, ...losers].slice(0, 10);
}

async function fetchWatchlist(): Promise<AssetRow[]> {
  try {
    const watchlistsRes = await apiClient.get<WatchlistResponse[]>("watchlists");
    const watchlists = watchlistsRes.data;
    const defaultWatchlist = watchlists.find((w) => w.is_default);
    if (!defaultWatchlist?.items?.length) return [];

    const symbols = defaultWatchlist.items.map((item) => item.asset.symbol);
    const pricesRes = await apiClient.get<LatestPricesResponse>(
      `market/latest-prices?${symbols.map((s) => `symbols=${encodeURIComponent(s)}`).join("&")}`
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

interface SignalsListResponse {
  status: string;
  data: Array<{
    symbol: string;
    name: string;
    signal_type: string;
    confidence: number;
    model: string;
    generated_at: string;
  }>;
}

async function fetchSignals(): Promise<SignalRow[]> {
  const res = await apiClient.get<SignalsListResponse>("analysis/signals?min_confidence=0.6&limit=10");
  const data = res.data;
  if (data.status !== "success") return [];

  return (data.data ?? []).map((s) => ({
    symbol: s.symbol,
    type: s.signal_type as SignalRow["type"],
    confidence: s.confidence,
    model: s.model,
  }));
}

async function fetchNews(): Promise<NewsItem[]> {
  const res = await apiClient.get<NewsResponse>("news/market?limit=10");
  const data = res.data;
  if (data.status !== "success") return [];

  return (data.data ?? []).map((n) => ({
    title: n.title,
    source: n.source,
    time: formatTimeAgo(n.published_at) }));
}

export async function fetchDashboardData(): Promise<DashboardData> {
  const results = await Promise.allSettled([
    fetchMarketStats(),
    fetchTopMovers(),
    fetchWatchlist(),
    fetchSignals(),
    fetchNews(),
  ]);

  const marketStats = results[0].status === "fulfilled" ? results[0].value : [];
  const topMovers = results[1].status === "fulfilled" ? results[1].value : [];
  const watchlist = results[2].status === "fulfilled" ? results[2].value : [];
  const signals = results[3].status === "fulfilled" ? results[3].value : [];
  const news = results[4].status === "fulfilled" ? results[4].value : [];

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

export async function fetchGeneralDashboard(): Promise<GeneralDashboardResponse> {
  const res = await apiClient.get<GeneralDashboardResponse>("/analysis/dashboard/general", { timeout: 120000 });
  return res.data;
}

export async function fetchTechnicalDashboard(): Promise<DimensionDashboardResponse> {
  const res = await apiClient.get<DimensionDashboardResponse>("/analysis/dashboard/technical", { timeout: 120000 });
  return res.data;
}

export async function fetchFundamentalDashboard(): Promise<DimensionDashboardResponse> {
  const res = await apiClient.get<DimensionDashboardResponse>("/analysis/dashboard/fundamental", { timeout: 120000 });
  return res.data;
}

export async function fetchNewsDashboard(): Promise<NewsDashboardResponse> {
  const res = await apiClient.get<NewsDashboardResponse>("/analysis/dashboard/news", { timeout: 120000 });
  return res.data;
}

export async function fetchRiskDashboard(): Promise<DimensionDashboardResponse> {
  const res = await apiClient.get<DimensionDashboardResponse>("/analysis/dashboard/risk", { timeout: 120000 });
  return res.data;
}

export async function fetchBoardDashboard(): Promise<BoardDashboardResponse> {
  const res = await apiClient.get<BoardDashboardResponse>("/analysis/dashboard/board", { timeout: 120000 });
  return res.data;
}

export async function fetchAiDashboard(): Promise<AiDashboardResponse> {
  const res = await apiClient.get<AiDashboardResponse>("/analysis/dashboard/ai", { timeout: 120000 });
  return res.data;
}