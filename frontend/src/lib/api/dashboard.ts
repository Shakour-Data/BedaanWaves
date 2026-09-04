/**
 * dashboard-api.ts
 * ---------------------------------------------------------------------------
 * Data access layer for the dashboard. Fetches live data from the backend.
 */

import { apiClient } from "@/lib/api";
import type { AssetRow, MarketStat, NewsItem } from "@/lib/dashboard-data";
import { isNasdaqEquityLike } from "@/lib/dashboard-data";

export interface DashboardData {
  marketStats: MarketStat[];
  topMovers: AssetRow[];
  watchlist: AssetRow[];
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
    raw_metrics?: Record<string, number>;
    key_ratios?: {
      eps: number | null;
      pe: number | null;
      pb: number | null;
      dps: number | null;
      roe: number | null;
      profit_margin: number | null;
      market_cap: number | null;
      book_value: number | null;
      period: string | null;
      as_of: string | null;
    } | null;
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
  top_performers: Array<{
    symbol: string;
    name: string;
    score: number;
    signal_type: string | null;
    confidence: number;
    expected_return: number;
    risk_score: number;
    generated_at: string | null;
  }>;
  bottom_performers: Array<{
    symbol: string;
    name: string;
    score: number;
    signal_type: string | null;
    confidence: number;
    expected_return: number;
    risk_score: number;
    generated_at: string | null;
  }>;
  timestamp: string;
}

export interface GeneralDashboardResponse {
  status: string;
  summary: {
    total_symbols: number;
    total_signals: number;
    total_news: number;
  };
  dimensions: Record<string, {
    avg_score: number;
    min_score: number;
    max_score: number;
    stdev: number;
    count: number;
    distribution: { strong: number; neutral: number; weak: number };
  }>;
  coefficients: Array<{ key: string; label: string; weight: number }>;
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
  latest_date: string | null;
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

async function fetchMarketStats(generalPromise: Promise<GeneralDashboardResponse> = apiClient.get<GeneralDashboardResponse>("/analysis/dashboard/general", { timeout: 60000 }).then((r) => r.data)): Promise<MarketStat[]> {
  const [marketOverviewRes, generalRes] = await Promise.all([
    apiClient.get<MarketOverviewResponse>("market/market-overview?market=NASDAQ", { timeout: 60000 }),
    generalPromise,
  ]);

  const marketOverview = marketOverviewRes.data;
  const general = generalRes;

  const stats: MarketStat[] = [];

  if (general?.status === "success") {
    const top = general.top_performers?.[0];
    const totalSymbols = general.summary?.total_symbols ?? 0;
    stats.push(
      { label: "Active Symbols", value: totalSymbols.toLocaleString("en-US"), changePct: 0 },
      { label: "Top Scorer", value: top ? `${top.symbol} ${top.overall_score?.toFixed(1) ?? "0"}` : "—", changePct: 0 },
      { label: "Lowest Scorer", value: general.bottom_performers?.[0] ? `${general.bottom_performers[0].symbol} ${general.bottom_performers[0].overall_score?.toFixed(1) ?? "0"}` : "—", changePct: 0 },
    );
  }

  if (marketOverview?.status === "success" && stats.length === 0) {
    stats.push(
      { label: "Active Symbols", value: marketOverview.total_assets.toLocaleString("en-US"), changePct: 0 },
    );
  }

  return stats.length ? stats : [
    { label: "Active Symbols", value: "—", changePct: 0 },
  ];
}

async function fetchTopMovers(generalPromise: Promise<GeneralDashboardResponse> = apiClient.get<GeneralDashboardResponse>("/analysis/dashboard/general", { timeout: 60000 }).then((r) => r.data)): Promise<AssetRow[]> {
  const data = await generalPromise;
  if (!data || data.status !== "success") return [];

  const map = (p: GeneralDashboardResponse["top_performers"][number]): AssetRow => ({
    symbol: p.symbol,
    name: p.name,
    market: "NASDAQ",
    price: 0,
    changePct: 0,
  });

  // Defense in depth: even if the backend ever returns a non-Nasdaq row,
  // we drop it before it reaches the dashboard. The backend already
  // filters to market=NASDAQ, but a stale cache or a future regression
  // would otherwise leak crypto/non-Nasdaq tickers into the UI.
  const ranked = [...(data.top_performers ?? []), ...(data.bottom_performers ?? [])]
    .filter((p) => isNasdaqEquityLike({ symbol: p.symbol }))
    .sort((a, b) => b.overall_score - a.overall_score);
  return ranked.slice(0, 10).map(map);
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
      .filter((item) => isNasdaqEquityLike(item.asset) && pricesData[item.asset.symbol])
      .map((item) => ({
        symbol: item.asset.symbol,
        name: item.asset.name,
        market: "NASDAQ" as const,
        price: pricesData[item.asset.symbol].price,
        changePct: pricesData[item.asset.symbol].change_pct }));
  } catch {
    return [];
  }
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

export async function fetchDashboardData(generalOverride?: GeneralDashboardResponse): Promise<DashboardData> {
  const generalPromise: Promise<GeneralDashboardResponse> = generalOverride
    ? Promise.resolve(generalOverride)
    : apiClient.get<GeneralDashboardResponse>("/analysis/dashboard/general", { timeout: 60000 }).then((r) => r.data);

  const results = await Promise.allSettled([
    fetchMarketStats(generalPromise),
    fetchTopMovers(generalPromise),
    fetchWatchlist(),
    fetchNews(),
  ]);

  const marketStats = results[0].status === "fulfilled" ? results[0].value : [];
  const topMovers = results[1].status === "fulfilled" ? results[1].value : [];
  const watchlist = results[2].status === "fulfilled" ? results[2].value : [];
  const news = results[3].status === "fulfilled" ? results[3].value : [];

  const live = [marketStats, topMovers, watchlist, news].some(
    (d) => Array.isArray(d) ? d.length > 0 : true
  );

  return {
    marketStats,
    topMovers,
    watchlist,
    news,
    live };
}

export async function fetchGeneralDashboard(latest: boolean = false): Promise<GeneralDashboardResponse> {
  const url = latest ? "/analysis/dashboard/general?latest=true" : "/analysis/dashboard/general";
  const res = await apiClient.get<GeneralDashboardResponse>(url, { timeout: 120000 });
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

export interface ScoreTrendPoint {
  date: string;
  avg_score: number;
  avg_dimensions: Record<string, number>;
  score_change: number;
  technical_change: number;
  dimension_changes: Record<string, number>;
  symbol_count: number;
}

export interface ScoreTrendResponse {
  status: string;
  days: number;
  market: string;
  count: number;
  dimensions: string[];
  latest_date: string | null;
  series: ScoreTrendPoint[];
  timestamp: string;
}

export interface ScoreTrendOptions {
  latest?: boolean;
  endDate?: string;
}

export async function fetchScoreTrend(
  days: number = 30,
  market?: string,
  options?: ScoreTrendOptions,
): Promise<ScoreTrendResponse> {
  const params = new URLSearchParams({ days: String(days) });
  if (market) params.set("market", market);
  if (options?.latest) params.set("latest", "true");
  if (options?.endDate) params.set("end_date", options.endDate);
  const res = await apiClient.get<ScoreTrendResponse>(
    `/analysis/dashboard/score-trend?${params.toString()}`,
    { timeout: 60000 },
  );
  return res.data;
}

export interface CoefficientHistoryPoint {
  date: string;
  dimensions: Record<string, number>;
  dimension_changes: Record<string, number>;
}

export interface CoefficientHistoryResponse {
  status: string;
  days: number;
  market: string;
  count: number;
  dimensions: string[];
  series: CoefficientHistoryPoint[];
  latest_date: string | null;
  timestamp: string;
}

export interface HierarchicalTrendPoint {
  date: string;
  metrics: Record<string, number>;
  metric_changes: Record<string, number>;
}

export interface HierarchicalTrendResponse {
  status: string;
  level: "sub_dimension" | "aspect" | "sub_aspect";
  days: number;
  market: string;
  parent: string | null;
  count: number;
  latest_date: string | null;
  series: HierarchicalTrendPoint[];
  timestamp: string;
}

export interface CoefficientHistoryByLevelResponse {
  status: string;
  level: "dimension" | "sub_dimension" | "aspect" | "sub_aspect";
  days: number;
  market: string;
  parent: string | null;
  count: number;
  latest_date: string | null;
  series: Array<{
    date: string;
    metrics: Record<string, number>;
    metric_changes: Record<string, number>;
  }>;
  timestamp: string;
}

export async function fetchCoefficientHistory(
  days: number = 30,
  market?: string,
  options?: ScoreTrendOptions,
): Promise<CoefficientHistoryResponse> {
  const params = new URLSearchParams({ days: String(days) });
  if (market) params.set("market", market);
  if (options?.latest) params.set("latest", "true");
  if (options?.endDate) params.set("end_date", options.endDate);
  const url = `/analysis/dashboard/coefficient-history?${params.toString()}`;
  const res = await apiClient.get<CoefficientHistoryResponse>(url, { timeout: 60000 });
  return res.data;
}

export async function fetchHierarchicalTrend(
  level: "sub_dimension" | "aspect" | "sub_aspect",
  days: number = 30,
  market?: string,
  options?: ScoreTrendOptions & { parent?: string },
): Promise<HierarchicalTrendResponse> {
  const params = new URLSearchParams({ level, days: String(days) });
  if (market) params.set("market", market);
  if (options?.latest) params.set("latest", "true");
  if (options?.endDate) params.set("end_date", options.endDate);
  if (options?.parent) params.set("parent", options.parent);
  const res = await apiClient.get<HierarchicalTrendResponse>(
    `/analysis/dashboard/hierarchical-trend?${params.toString()}`,
    { timeout: 60000 },
  );
  return res.data;
}

export async function fetchCoefficientHistoryByLevel(
  level: "dimension" | "sub_dimension" | "aspect" | "sub_aspect",
  days: number = 30,
  market?: string,
  options?: ScoreTrendOptions & { parent?: string },
): Promise<CoefficientHistoryByLevelResponse> {
  const params = new URLSearchParams({ level, days: String(days) });
  if (market) params.set("market", market);
  if (options?.latest) params.set("latest", "true");
  if (options?.endDate) params.set("end_date", options.endDate);
  if (options?.parent) params.set("parent", options.parent);
  const res = await apiClient.get<CoefficientHistoryByLevelResponse>(
    `/analysis/dashboard/coefficient-history-by-level?${params.toString()}`,
    { timeout: 60000 },
  );
  return res.data;
}

export interface LevelTrendPoint {
  date: string;
  avg_scores: Record<string, number>;
  score_changes: Record<string, number>;
  symbol_count: number;
}

export interface LevelTrendResponse {
  status: string;
  days: number;
  market: string;
  count: number;
  level: "sub_dimension" | "aspect" | "sub_aspect";
  keys: string[];
  series: LevelTrendPoint[];
  latest_date: string | null;
  timestamp: string;
}

function buildLevelTrendFetcher(path: string) {
  return async function fetchLevelTrend(
    days: number = 30,
    market?: string,
    options?: ScoreTrendOptions,
  ): Promise<LevelTrendResponse> {
    const params = new URLSearchParams({ days: String(days) });
    if (market) params.set("market", market);
    if (options?.latest) params.set("latest", "true");
    if (options?.endDate) params.set("end_date", options.endDate);
    const url = `${path}?${params.toString()}`;
    const res = await apiClient.get<LevelTrendResponse>(url, { timeout: 60000 });
    return res.data;
  };
}

export const fetchSubDimensionTrend = buildLevelTrendFetcher(
  "/analysis/dashboard/sub-dimension-trend",
);

export const fetchAspectTrend = buildLevelTrendFetcher(
  "/analysis/dashboard/aspect-trend",
);

export const fetchSubAspectTrend = buildLevelTrendFetcher(
  "/analysis/dashboard/sub-aspect-trend",
);
