import { useState, useEffect, useRef, useCallback } from "react";
import { getApiErrorMessage } from "@/lib/api";
import { searchNews } from "@/lib/api/news";
import { useStockSearch } from "@/hooks/useStockSearch";

export type SearchStatus = "idle" | "loading" | "success" | "error" | "empty";

export interface PageSearchItem {
  kind: "page";
  id: string;
  title: string;
  href: string;
  description: string;
  category: "Analytics" | "Intelligence" | "Resources" | "Account";
  keywords: string[];
}

export interface NewsSearchItem {
  kind: "news";
  id: string;
  title: string;
  source: string;
  url: string;
  publishedAt: string;
  category: string | null;
  isMarketMoving: boolean;
}

export type UnifiedSearchItem =
  | (ReturnType<typeof useStockSearch>["results"][number] & { kind: "stock" })
  | NewsSearchItem
  | PageSearchItem;

export interface SearchGroup<T = UnifiedSearchItem> {
  label: string;
  items: T[];
}

export interface UnifiedSearchState {
  query: string;
  status: SearchStatus;
  error: string | null;
  groups: SearchGroup[];
  total: number;
}

const PAGE_INDEX: PageSearchItem[] = [
  {
    kind: "page",
    id: "page-dashboard",
    title: "Dashboard",
    href: "/dashboard",
    description: "Live NASDAQ market overview, scores, and movers",
    category: "Analytics",
    keywords: ["dashboard", "home", "overview", "market", "summary"],
  },
  {
    kind: "page",
    id: "page-leaderboard",
    title: "Leaderboard",
    href: "/leaderboard",
    description: "Top scoring NASDAQ equities by overall or dimension",
    category: "Analytics",
    keywords: ["leaderboard", "top", "ranking", "best", "score"],
  },
  {
    kind: "page",
    id: "page-movers",
    title: "Biggest Movers",
    href: "/movers",
    description: "Today's biggest gainers and losers",
    category: "Analytics",
    keywords: ["movers", "gainers", "losers", "biggest", "today"],
  },
  {
    kind: "page",
    id: "page-stocks",
    title: "Stocks",
    href: "/stocks",
    description: "Browse, search, and analyze NASDAQ stocks",
    category: "Analytics",
    keywords: ["stocks", "list", "browse", "all", "nasdaq"],
  },
  {
    kind: "page",
    id: "page-analysis",
    title: "Analysis",
    href: "/analysis",
    description: "Deep-dive analysis tools for any ticker",
    category: "Analytics",
    keywords: ["analysis", "analyze", "deep", "dive", "tool"],
  },
  {
    kind: "page",
    id: "page-scoring",
    title: "AI Scoring",
    href: "/scoring",
    description: "AI-powered scoring overview",
    category: "Analytics",
    keywords: ["scoring", "ai", "score", "rating", "grade"],
  },
  {
    kind: "page",
    id: "page-scoring-filter",
    title: "Scoring Filter",
    href: "/scoring-filter",
    description: "Filter and screen stocks by score",
    category: "Analytics",
    keywords: ["filter", "screener", "screen", "filterable"],
  },
  {
    kind: "page",
    id: "page-portfolio",
    title: "Portfolio",
    href: "/portfolio",
    description: "Track your holdings and performance",
    category: "Analytics",
    keywords: ["portfolio", "holdings", "my", "positions", "watch"],
  },
  {
    kind: "page",
    id: "page-ranking",
    title: "Rankings",
    href: "/ranking",
    description: "Full NASDAQ ranking table",
    category: "Analytics",
    keywords: ["ranking", "rank", "table", "all", "nasdaq"],
  },
  {
    kind: "page",
    id: "page-news",
    title: "News",
    href: "/news",
    description: "Live market news and headlines",
    category: "Intelligence",
    keywords: ["news", "headlines", "articles", "live", "feed"],
  },
  {
    kind: "page",
    id: "page-alerts",
    title: "Alerts",
    href: "/alerts",
    description: "Manage your price and score alerts",
    category: "Intelligence",
    keywords: ["alerts", "notifications", "price", "alert"],
  },
  {
    kind: "page",
    id: "page-watchlist",
    title: "Watchlist",
    href: "/watchlist",
    description: "Track stocks you care about",
    category: "Intelligence",
    keywords: ["watchlist", "watch", "track", "follow", "saved"],
  },
  {
    kind: "page",
    id: "page-compare",
    title: "Compare",
    href: "/compare",
    description: "Compare two or more stocks side by side",
    category: "Intelligence",
    keywords: ["compare", "versus", "vs", "side by side"],
  },
  {
    kind: "page",
    id: "page-methodology",
    title: "Methodology",
    href: "/methodology",
    description: "How our scores and ratings are calculated",
    category: "Resources",
    keywords: ["methodology", "how", "calc", "formula", "explained"],
  },
  {
    kind: "page",
    id: "page-help",
    title: "Help",
    href: "/help",
    description: "Help center and documentation",
    category: "Resources",
    keywords: ["help", "docs", "support", "faq"],
  },
  {
    kind: "page",
    id: "page-settings",
    title: "Settings",
    href: "/settings",
    description: "Your market data and account settings",
    category: "Account",
    keywords: ["settings", "preferences", "config"],
  },
  {
    kind: "page",
    id: "page-profile",
    title: "Profile",
    href: "/settings/profile",
    description: "Manage your profile",
    category: "Account",
    keywords: ["profile", "account", "me", "user"],
  },
];

function filterPages(q: string): PageSearchItem[] {
  const norm = q.trim().toLowerCase();
  if (!norm) return [];
  return PAGE_INDEX.filter((p) => {
    if (p.title.toLowerCase().includes(norm)) return true;
    if (p.description.toLowerCase().includes(norm)) return true;
    return p.keywords.some((k) => k.toLowerCase().includes(norm));
  }).slice(0, 5);
}

function useDebouncedValue<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return debounced;
}

export interface UseUnifiedSearchOptions {
  minQueryLength?: number;
  newsLimit?: number;
  stockLimit?: number;
}

export function useUnifiedSearch(options: UseUnifiedSearchOptions = {}) {
  const { minQueryLength = 1, newsLimit = 5, stockLimit = 6 } = options;

  const [query, setQuery] = useState("");
  const debouncedQuery = useDebouncedValue(query, 300);

  const stockSearch = useStockSearch(minQueryLength);
  const [news, setNews] = useState<NewsSearchItem[]>([]);
  const [newsStatus, setNewsStatus] = useState<SearchStatus>("idle");
  const [newsError, setNewsError] = useState<string | null>(null);
  const newsAbortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    const trimmed = debouncedQuery.trim();
    newsAbortRef.current?.abort();
    if (trimmed.length < minQueryLength) {
      return;
    }

    const controller = new AbortController();
    newsAbortRef.current = controller;

    (async () => {
      setNewsStatus("loading");
      setNewsError(null);
      try {
        const items = await searchNews(trimmed, newsLimit);
        if (controller.signal.aborted) return;
        setNews(
          items.slice(0, newsLimit).map((it) => ({
            kind: "news" as const,
            id: it.url || `${it.title}-${it.published_at}`,
            title: it.title,
            source: it.source || "Unknown",
            url: it.url || "",
            publishedAt: it.published_at || "",
            category: it.category ?? null,
            isMarketMoving: Boolean(it.is_market_moving),
          }))
        );
        setNewsStatus(items.length === 0 ? "empty" : "success");
      } catch (err) {
        if (controller.signal.aborted) return;
        setNews([]);
        setNewsError(getApiErrorMessage(err));
        setNewsStatus("error");
      }
    })();

    return () => controller.abort();
  }, [debouncedQuery, minQueryLength, newsLimit]);

  const trimmed = debouncedQuery.trim();
  const showPages = trimmed.length >= minQueryLength;

  const pageItems: PageSearchItem[] = showPages ? filterPages(trimmed) : [];

  const stockItems = stockSearch.results.slice(0, stockLimit).map((s) => ({
    ...s,
    kind: "stock" as const,
  }));

  const groups: SearchGroup[] = [];
  if (stockItems.length > 0) {
    groups.push({ label: "Stocks", items: stockItems });
  }
  if (news.length > 0) {
    groups.push({ label: "News", items: news });
  }
  if (pageItems.length > 0) {
    groups.push({ label: "Pages", items: pageItems });
  }

  const total = stockItems.length + news.length + pageItems.length;

  let status: SearchStatus = "idle";
  let error: string | null = null;
  if (trimmed.length < minQueryLength) {
    status = "idle";
  } else if (
    stockSearch.status === "loading" ||
    newsStatus === "loading"
  ) {
    status = "loading";
  } else if (
    stockSearch.status === "error" ||
    newsStatus === "error"
  ) {
    status = "error";
    error = stockSearch.error || newsError;
  } else if (total === 0) {
    status = "empty";
  } else {
    status = "success";
  }

  const clear = useCallback(() => {
    setQuery("");
    stockSearch.clearResults();
    setNews([]);
    setNewsStatus("idle");
    setNewsError(null);
  }, [stockSearch]);

  return {
    query,
    setQuery,
    debouncedQuery,
    status,
    error,
    groups,
    total,
    isStockLoading: stockSearch.status === "loading",
    isNewsLoading: newsStatus === "loading",
    clear,
  };
}
