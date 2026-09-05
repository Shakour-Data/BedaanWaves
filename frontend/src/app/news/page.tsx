"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { NewDashboardShell } from "@/components/layout/NewDashboardShell";
import { TarotCard } from "@/components/ui/TarotCard";
import { NewsList } from "@/components/dashboard/NewsList";
import { AssetTable } from "@/components/dashboard/AssetTable";
import { useAppStore } from "@/store/useAppStore";
import { cn } from "@/lib/cn";
import { apiClient } from "@/lib/api";
import { t } from "@/lib/i18n";
import { useAuthStore } from "@/store/useAuthStore";
import type { NewsItem, AssetRow } from "@/lib/dashboard-data";
import { formatTimeAgo } from "@/lib/utils";

export default function NewsPage() {
  
  const [newItems, setNewItems] = useState<NewsItem[]>([]);
  const [selectedSource, setSelectedSource] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    let active = true;

    async function loadNews() {
      setLoading(true);
      try {
        // Fetch market news
        const newsRes = await apiClient.get<any>("/news/market?limit=20");
        
        if (active) {
          const newsItems: NewsItem[] = (newsRes.data || {}).data || [];
          const formattedNews: NewsItem[] = newsItems.map((item: any) => ({
            title: item.title,
            source: item.source || "Unknown",
            time: formatTimeAgo(item.published_at || item.created_at) }));

          setNewItems(formattedNews);
        }
      } catch (error) {
        // Handle error silently
      } finally {
        if (active) setLoading(false);
      }
    }

    loadNews();
    return () => { active = false; };
  }, []);

  const sources = Array.from(new Set(newItems.map((item) => item.source)));
  const filteredNews = selectedSource ? newItems.filter((item) => item.source === selectedSource) : newItems;
  const trendingTopics = getTrendingTopics(newItems);
  const topTopics = getTopTopics(newItems);

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
        {/* News Filters */}
        <div className="lg:col-span-1 space-y-4">
          <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5 shadow-sm">
            <div className="flex items-center gap-3 mb-4">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--color-primary-soft)] text-[var(--color-primary)]">
                <span className="text-sm font-bold">F</span>
              </div>
              <h3 className="font-semibold text-[var(--color-text-primary)] text-sm">Filters</h3>
            </div>
            <div className="space-y-1">
              <button
                onClick={() => setSelectedSource(null)}
                className={cn(
                  "w-full text-right px-3 py-2 rounded-lg text-sm font-medium transition-all",
                   selectedSource === null ? "bg-[var(--color-primary)] text-white shadow-md" : "text-[var(--color-text-secondary)] hover:bg-[var(--color-muted)] hover:text-[var(--color-text-primary)]"
                )}
              >
                All News
              </button>
              {sources.map((source) => (
                <button
                  key={source}
                  onClick={() => setSelectedSource(source)}
                  className={cn(
                    "w-full text-right px-3 py-2 rounded-lg text-sm font-medium transition-all",
                     selectedSource === source ? "bg-[var(--color-primary)] text-white shadow-md" : "text-[var(--color-text-secondary)] hover:bg-[var(--color-muted)] hover:text-[var(--color-text-primary)]"
                  )}
                >
                  {source}
                </button>
              ))}
            </div>
          </div>

          {/* Trending Topics */}
          <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5 shadow-sm">
            <div className="flex items-center gap-3 mb-4">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--color-primary-soft)] text-[var(--color-primary)]">
                <span className="text-sm">🔥</span>
              </div>
              <h3 className="font-semibold text-[var(--color-text-primary)] text-sm">Trending Topics</h3>
            </div>
            <div className="space-y-2">
              {topTopics.map((topic, i) => (
                <div key={i} className="flex items-center justify-between font-medium text-sm p-2 rounded-lg hover:bg-[var(--color-muted)] transition-colors">
                  <span className="flex-1 text-[var(--color-text-primary)]">{topic.topic}</span>
                  <span className="text-xs text-[var(--color-text-muted)] bg-[var(--color-muted)] px-2 py-0.5 rounded-full">{topic.count} news</span>
                </div>
              ))}
              {topTopics.length === 0 && (
                <p className="text-sm text-[var(--color-text-muted)]">
                  No trending topics found
                </p>
              )}
            </div>
          </div>
        </div>

        {/* News List */}
        <div className="lg:col-span-3">
          <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--color-primary-soft)] text-[var(--color-primary)]">
                  <span className="text-sm">📰</span>
                </div>
                <div>
                  <h3 className="font-semibold text-[var(--color-text-primary)] text-sm">
                    {selectedSource 
                      ? `News from ${selectedSource}` 
                      : "All News"
                    }
                  </h3>
                </div>
              </div>
              <span className="text-xs text-[var(--color-text-muted)]">{filteredNews.length} articles</span>
            </div>
            <NewsList items={filteredNews} />
          </div>
        </div>
      </div>
    </NewDashboardShell>
  );
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

function getTrendingTopics(newsItems: NewsItem[]): { topic: string; count: number }[] {
  return getTopTopics(newsItems);
}
