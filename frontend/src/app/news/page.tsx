"use client";

import { useState, useEffect, useRef, useMemo, useCallback } from "react";
import { NewDashboardShell } from "@/components/layout/NewDashboardShell";
import { cn } from "@/lib/cn";
import { apiClient } from "@/lib/api";
import { t } from "@/lib/i18n";
import { formatTimeAgo } from "@/lib/utils";
import {
  useLiveData,
  LiveConnectionIndicator,
} from "@/hooks/useLiveData";
import {
  NewsCategoryFilter,
} from "@/components/news/NewsCategoryFilter";
import {
  NewsRegionFilter,
} from "@/components/news/NewsRegionFilter";
import { MarketMovingBanner } from "@/components/news/MarketMovingBanner";
import {
  getMarketNews,
  getNewsByCategory,
  getMarketMovingNews,
} from "@/lib/api/news";
import type {
  NewsItem,
  NewsCategory,
  NewsRegion,
  NewsPriority,
  NewsFilterState,
  NewsStreamPayload,
} from "@/lib/news-types";

interface LiveNewsItem extends NewsItem {
  isNewLive?: boolean;
  liveAddedAt?: number;
}

function getTopTopics(newsItems: NewsItem[]): { topic: string; count: number }[] {
  const wordCounts: Record<string, number> = {};
  newsItems.forEach((item) => {
    const words = item.title.split(/\s+/);
    words.forEach((word) => {
      const cleaned = word.replace(/[^\u0600-\u06FFa-zA-Z]/g, "").toLowerCase();
      if (cleaned.length > 3) {
        wordCounts[cleaned] = (wordCounts[cleaned] || 0) + 1;
      }
    });
  });
  return Object.entries(wordCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .map(([topic, count]) => ({ topic, count }));
}

interface NewsListWithBadgesProps {
  items: LiveNewsItem[];
}

function NewsListWithBadges({ items }: NewsListWithBadgesProps) {
  if (items.length === 0) {
    return <ul className="space-y-0" />;
  }

  return (
    <ul className="space-y-0">
      {items.map((item, index) => {
        const stableKey =
          item.id || `${item.title}-${item.source}-${index}`;
        return (
          <li
            key={stableKey}
            className={cn(
              "border-b border-[var(--color-border)] px-4 py-3 last:border-b-0 hover:bg-[var(--color-background)] transition-colors",
              item.isNewLive ? "bg-[var(--color-primary)]/5" : ""
            )}
          >
            <div className="flex items-start gap-2">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  {item.is_market_moving && (
                    <span className="shrink-0 inline-flex items-center rounded bg-red-100 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-red-700">
                      MOVING
                    </span>
                  )}
                  {item.category && (
                    <span className="shrink-0 inline-flex items-center rounded bg-[var(--color-muted)] px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wider text-[var(--color-text-secondary)]">
                      {item.category.replace("_", " ")}
                    </span>
                  )}
                </div>
                <p className="font-medium text-[var(--color-text-primary)] text-sm">
                  {item.title}
                </p>
                <div className="flex items-center gap-2 mt-1 text-xs text-[var(--color-text-secondary)]">
                  <span>{item.source}</span>
                  <span>•</span>
                  <span>{item.time}</span>
                  {item.region && (
                    <>
                      <span>•</span>
                      <span>{item.region}</span>
                    </>
                  )}
                </div>
              </div>
              {item.isNewLive ? (
                <span className="shrink-0 inline-flex items-center rounded bg-[var(--color-primary)] px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-white">
                  NEW
                </span>
              ) : null}
            </div>
          </li>
        );
      })}
    </ul>
  );
}

const INITIAL_FILTER: NewsFilterState = {
  category: "all",
  region: "all",
  priority: "all",
  marketMovingOnly: false,
  searchQuery: "",
};

export default function NewsPage() {
  const [filter, setFilter] = useState<NewsFilterState>(INITIAL_FILTER);
  const [newsItems, setNewsItems] = useState<LiveNewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const lastNewsEventRef = useRef<number | null>(null);
  const [lastNewsEventTs, setLastNewsEventTs] = useState<number | null>(null);
  const itemIdCounter = useRef(0);

  useEffect(() => {
    let active = true;
    setLoading(true);

    async function loadNews() {
      try {
        let items: NewsItem[] = [];

        if (filter.marketMovingOnly) {
          items = await getMarketMovingNews(50);
        } else if (filter.category !== "all") {
          items = await getNewsByCategory(filter.category as NewsCategory, {
            region: filter.region !== "all" ? filter.region as NewsRegion : undefined,
            priority: filter.priority !== "all" ? filter.priority as NewsPriority : undefined,
            limit: 100,
          });
        } else {
          items = await getMarketNews(50);
        }

        if (active) {
          const formatted: LiveNewsItem[] = items.map((item, idx) => ({
            ...item,
            time: formatTimeAgo(item.published_at),
            id: `rest-${idx}-${Date.now()}`,
          }));
          setNewsItems(formatted);
        }
      } catch {
        // ignore
      } finally {
        if (active) setLoading(false);
      }
    }

    loadNews();
    return () => { active = false; };
  }, [filter.category, filter.region, filter.priority, filter.marketMovingOnly]);

  useEffect(() => {
    const timer = setInterval(() => {
      const now = Date.now();
      setNewsItems((prev) => {
        let changed = false;
        const next = prev.map((it) => {
          if (it.isNewLive && it.liveAddedAt && now - it.liveAddedAt >= 60_000) {
            changed = true;
            return { ...it, isNewLive: false, liveAddedAt: undefined };
          }
          return it;
        });
        return changed ? next : prev;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const handleNewsData = useCallback(
    (payload: NewsStreamPayload) => {
      const incoming: LiveNewsItem[] = [];
      if (payload?.item) incoming.push(payload.item);
      if (payload?.items && Array.isArray(payload.items)) {
        for (const it of payload.items) incoming.push(it);
      }
      if (incoming.length === 0) return;

      const now = Date.now();
      lastNewsEventRef.current = now;
      setLastNewsEventTs(now);

      setNewsItems((prev) => {
        const next: LiveNewsItem[] = [];
        const seenTitles = new Set<string>();

        for (const inc of incoming) {
          itemIdCounter.current += 1;
          const enriched: LiveNewsItem = {
            title: inc.title,
            body: inc.body,
            source: inc.source || "Unknown",
            url: inc.url || "",
            published_at: inc.published_at || new Date().toISOString(),
            language: inc.language || "en",
            asset_id: inc.asset_id,
            time: inc.time || "just now",
            isNewLive: true,
            liveAddedAt: now,
            id: inc.id || `live-${itemIdCounter.current}-${now}`,
            category: inc.category,
            sub_category: inc.sub_category,
            region: inc.region,
            priority: inc.priority,
            is_market_moving: inc.is_market_moving,
          };
          next.push(enriched);
          seenTitles.add(enriched.title);
        }

        for (const existing of prev) {
          if (seenTitles.has(existing.title)) continue;
          next.push(existing);
        }
        return next.slice(0, 100);
      });
    },
    []
  );

  const newsLive = useLiveData<NewsStreamPayload>("news", {
    enabled: !loading,
    onData: handleNewsData,
  });

  const marketMovingCount = useMemo(
    () => newsItems.filter((n) => n.is_market_moving).length,
    [newsItems]
  );

  const filteredNews = useMemo(
    () => newsItems,
    [newsItems]
  );

  const setCategory = useCallback((cat: string | null) => {
    setFilter((prev) => ({
      ...prev,
      category: cat as NewsFilterState["category"],
      marketMovingOnly: false,
    }));
  }, []);

  const setRegion = useCallback((region: string | null) => {
    setFilter((prev) => ({
      ...prev,
      region: region as NewsFilterState["region"],
    }));
  }, []);

  if (loading) {
    return (
      <NewDashboardShell title={t("app.news.title")}>
        <div className="flex min-h-[40vh] items-center justify-center text-muted-foreground">
          {t("app.news.loading")}
        </div>
      </NewDashboardShell>
    );
  }

  return (
    <NewDashboardShell title={t("app.news.title")}>
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 animate-in fade-in duration-500">
        <div className="lg:col-span-1 space-y-4">
          <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--color-primary-soft)] text-[var(--color-primary)]">
                  <span className="text-sm font-bold">F</span>
                </div>
                <h3 className="font-semibold text-[var(--color-text-primary)] text-sm">Filters</h3>
              </div>
              <LiveConnectionIndicator
                health={newsLive.connectionHealth}
                dataAgeMs={newsLive.lastDataAgeMs}
                lastEventTs={lastNewsEventTs}
              />
            </div>

            <NewsCategoryFilter
              selected={filter.category}
              onChange={setCategory}
            />
          </div>

          <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5 shadow-sm">
            <div className="flex items-center gap-3 mb-4">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--color-primary-soft)] text-[var(--color-primary)]">
                <span className="text-sm">🌍</span>
              </div>
              <h3 className="font-semibold text-[var(--color-text-primary)] text-sm">Region</h3>
            </div>
            <NewsRegionFilter
              selected={filter.region}
              onChange={setRegion}
            />
          </div>

          <MarketMovingBanner
            count={marketMovingCount}
            onClick={() => setFilter((f) => ({ ...f, marketMovingOnly: !f.marketMovingOnly, category: "all" }))}
          />

          <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5 shadow-sm">
            <div className="flex items-center gap-3 mb-4">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--color-primary-soft)] text-[var(--color-primary)]">
                <span className="text-sm">🔥</span>
              </div>
              <h3 className="font-semibold text-[var(--color-text-primary)] text-sm">Trending Topics</h3>
            </div>
            <div className="space-y-2">
              {getTopTopics(newsItems).map((topic, i) => (
                <div key={i} className="flex items-center justify-between font-medium text-sm p-2 rounded-lg hover:bg-[var(--color-muted)] transition-colors">
                  <span className="flex-1 text-[var(--color-text-primary)]">{topic.topic}</span>
                  <span className="text-xs text-[var(--color-text-muted)] bg-[var(--color-muted)] px-2 py-0.5 rounded-full">{topic.count} news</span>
                </div>
              ))}
              {getTopTopics(newsItems).length === 0 && (
                <p className="text-sm text-[var(--color-text-muted)]">
                  No trending topics found
                </p>
              )}
            </div>
          </div>
        </div>

        <div className="lg:col-span-3">
          <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--color-primary-soft)] text-[var(--color-primary)]">
                  <span className="text-sm">📰</span>
                </div>
                <div>
                  <h3 className="font-semibold text-[var(--color-text-primary)] text-sm">
                    {filter.marketMovingOnly
                      ? "Market Moving News"
                      : filter.category !== "all"
                        ? `${filter.category.replace("_", " ")} News`
                        : "All News"}
                  </h3>
                </div>
              </div>
              <span className="text-xs text-[var(--color-text-muted)]">{filteredNews.length} articles</span>
            </div>
            <NewsListWithBadges items={filteredNews} />
          </div>
        </div>
      </div>
    </NewDashboardShell>
  );
}
