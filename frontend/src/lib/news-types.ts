export type NewsCategory =
  | "POLITICAL"
  | "ECONOMIC"
  | "INTERNATIONAL"
  | "STOCK_MARKET"
  | "INDUSTRY"
  | "COMPANY";

export type NewsRegion =
  | "US"
  | "EU"
  | "UK"
  | "ASIA"
  | "MENA"
  | "LATAM"
  | "GLOBAL";

export type NewsPriority = "LOW" | "NORMAL" | "HIGH" | "CRITICAL";

export interface NewsItem {
  id: string;
  source: string;
  title: string;
  body: string | null;
  url: string;
  published_at: string;
  category: NewsCategory;
  sub_category: string | null;
  region: NewsRegion | null;
  priority: NewsPriority;
  language: string;
  asset_id: string | null;
  is_market_moving: boolean;
  time: string;
}

export interface LiveNewsItem extends NewsItem {
  isNewLive?: boolean;
  liveAddedAt?: number;
}

export interface NewsFilterState {
  category: NewsCategory | "all";
  region: NewsRegion | "all";
  priority: NewsPriority | "all";
  marketMovingOnly: boolean;
  searchQuery: string;
}

export interface NewsStreamPayload {
  item?: Partial<LiveNewsItem>;
  items?: Array<Partial<LiveNewsItem>>;
  news_id?: string;
  title?: string;
  summary?: string | null;
  source?: string;
  url?: string | null;
  symbols_affected?: string[];
  sentiment?: string | null;
  published_at?: string;
  freshness_ts?: string;
  received_ts?: string;
  data_age_ms?: number;
  stale?: boolean;
}

/**
 * Normalized item shape produced by `normalizeNewsPayload`.
 * It is an intersection of every field that may appear on an incoming
 * news payload (LiveNewsItem | NewsStreamPayload), so consumers can
 * safely read any of the merged properties.
 */
export type NormalizedNewsItem = Partial<LiveNewsItem> & {
  summary?: string | null;
  symbols_affected?: string[];
  news_id?: string;
  sentiment?: string | null;
  url?: string | null;
  freshness_ts?: string;
  received_ts?: string;
  data_age_ms?: number | null;
  stale?: boolean;
};

export function normalizeNewsPayload(payload: NewsStreamPayload | null | undefined): Array<NormalizedNewsItem> {
  if (!payload) return [];
  const incoming: Array<NormalizedNewsItem> = [];
  if (payload.item) incoming.push(payload.item);
  if (payload.items && Array.isArray(payload.items)) incoming.push(...payload.items);
  if (!incoming.length && (payload.title || payload.news_id)) incoming.push(payload as unknown as NormalizedNewsItem);
  return incoming;
}

