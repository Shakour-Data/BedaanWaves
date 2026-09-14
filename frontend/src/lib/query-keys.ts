/**
 * query-keys.ts
 * ---------------------------------------------------------------------------
 * Centralized query-key factory for TanStack React Query.
 * Every useQuery / useMutation in the app should derive its key from here
 * so that cache invalidation is consistent and predictable.
 */

export const QK = {
  /** /market/symbols */
  symbols: (params?: Record<string, string | number | undefined>) =>
    ["symbols", params] as const,

  /** /market/price-history */
  priceHistory: (symbol: string, timeframe = "1d", limit = 500) =>
    ["priceHistory", symbol, timeframe, limit] as const,

  /** /market/latest-prices */
  latestPrices: (symbols: string[]) =>
    ["latestPrices", [...symbols].sort()] as const,

  /** /analysis/scoring/:symbol */
  scoring: (symbol: string) =>
    ["scoring", symbol] as const,

  /** /analysis/fundamental/:symbol */
  fundamental: (symbol: string) =>
    ["fundamental", symbol] as const,

  /** /analysis/technical/:symbol */
  technical: (symbol: string) =>
    ["technical", symbol] as const,

  /** /analysis/risk/:symbol */
  risk: (symbol: string) =>
    ["risk", symbol] as const,

  /** /analysis/sentiment/:symbol */
  sentiment: (symbol: string) =>
    ["sentiment", symbol] as const,

  /** /analysis/scoring/hierarchy/:symbol */
  hierarchyScores: (symbol: string) =>
    ["hierarchyScores", symbol] as const,

  /** /analysis/scoring/history/:symbol */
  scoreHistory: (symbol: string, days = 30) =>
    ["scoreHistory", symbol, days] as const,

  /** /analysis/scoring/coefficients (derived from hierarchy) */
  coefficients: (symbol: string) =>
    ["coefficients", symbol] as const,

  /** /watchlists */
  watchlists: () =>
    ["watchlists"] as const,

  /** /watchlists/:id */
  watchlist: (id: string) =>
    ["watchlist", id] as const,

  /** /analysis/dashboard/general */
  dashboardGeneral: (opts?: { latest?: boolean; endDate?: string }) =>
    ["dashboardGeneral", opts] as const,

  /** /analysis/dashboard/snapshot */
  dashboardSnapshot: (opts?: Record<string, string | number | undefined>) =>
    ["dashboardSnapshot", opts] as const,

  /** /analysis/dashboard/snapshots (index) */
  dashboardSnapshotIndex: (opts?: { hourly_limit?: number; daily_limit?: number }) =>
    ["dashboardSnapshotIndex", opts] as const,

  /** /analysis/dashboard/technical | fundamental | news | risk | board | ai */
  dashboardDimension: (dimension: string) =>
    ["dashboardDimension", dimension] as const,

  /** /analysis/dashboard/score-trend */
  scoreTrend: (days: number, market?: string, opts?: Record<string, string | undefined>) =>
    ["scoreTrend", days, market, opts] as const,

  /** /analysis/dashboard/coefficient-history */
  coefficientHistory: (days: number, market?: string, opts?: Record<string, string | undefined>) =>
    ["coefficientHistory", days, market, opts] as const,

  /** /analysis/dashboard/hierarchical-trend */
  hierarchicalTrend: (level: string, days: number, market?: string, opts?: Record<string, string | undefined>) =>
    ["hierarchicalTrend", level, days, market, opts] as const,

  /** /analysis/dashboard/coefficient-history-by-level */
  coefficientHistoryByLevel: (level: string, days: number, market?: string, opts?: Record<string, string | undefined>) =>
    ["coefficientHistoryByLevel", level, days, market, opts] as const,

  /** /analysis/dashboard/sub-dimension-trend | aspect-trend | sub-aspect-trend */
  levelTrend: (type: string, days: number, market?: string, opts?: Record<string, string | undefined>) =>
    ["levelTrend", type, days, market, opts] as const,

  /** /analysis/dashboard/top-performers */
  topPerformers: (opts: { level?: string; dimension?: string; limit?: number }) =>
    ["topPerformers", opts] as const,

  /** /analysis/dashboard/biggest-movers */
  biggestMovers: (opts: { level?: string; dimension?: string; limit?: number; days?: number }) =>
    ["biggestMovers", opts] as const,

  /** /ranking/nasdaq */
  ranking: (params: { limit?: number; offset?: number; sort_by?: string; order?: string }) =>
    ["ranking", params] as const,

  /** /news/* */
  news: {
    market: (limit = 20) => ["news", "market", limit] as const,
    category: (category: string, opts?: Record<string, string | number | undefined>) =>
      ["news", "category", category, opts] as const,
    marketMoving: (limit = 20) => ["news", "marketMoving", limit] as const,
    search: (query: string, limit = 20) => ["news", "search", query, limit] as const,
    categories: () => ["news", "categories"] as const,
    regions: () => ["news", "regions"] as const,
  },

  /** /nerk/* */
  nerk: {
    constituents: () => ["nerk", "constituents"] as const,
    overview: () => ["nerk", "overview"] as const,
    priceHistory: (symbol: string, period = "1y") =>
      ["nerk", "priceHistory", symbol, period] as const,
  },

  /** /filter/* */
  filter: {
    fields: () => ["filter", "fields"] as const,
    advanced: (payload: unknown) => ["filter", "advanced", payload] as const,
  },

  /** /settings/* */
  settings: {
    marketPreferences: () => ["settings", "marketPreferences"] as const,
    countries: () => ["settings", "countries"] as const,
    recentSearches: () => ["settings", "recentSearches"] as const,
  },

  /** /portfolio/* */
  portfolio: {
    detail: () => ["portfolio", "detail"] as const,
    holdings: (id: string) => ["portfolio", "holdings", id] as const,
  },

  /** /stocks/search and /stocks/batch */
  stocksSearch: (query: string) =>
    ["stocksSearch", query] as const,
  stocksBatch: (tickers: string[]) =>
    ["stocksBatch", [...tickers].sort()] as const,

  /** /analysis/top-performers (analysis page) */
  analysisTopPerformers: (limit = 10, timeframe = "1d", market = "NASDAQ") =>
    ["analysisTopPerformers", limit, timeframe, market] as const,
} as const;
