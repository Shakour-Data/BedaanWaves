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
  items?: LiveNewsItem[];
  item?: LiveNewsItem;
}
