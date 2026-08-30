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

  const formatTimeAgo = (dateStr: string): string => {
    const diff = Date.now() - new Date(dateStr).getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    if (minutes < 1) return t("app.alerts.time.now", "en");
    if (minutes < 60) return `${minutes} ${t("app.alerts.time.minutes_ago", "en")}`;
    if (hours < 24) return `${hours} ${t("app.alerts.time.hours_ago", "en")}`;
    return `${days} ${t("app.alerts.time.days_ago", "en")}`;
  };

  const sources = Array.from(new Set(newItems.map((item) => item.source)));
  const filteredNews = selectedSource ? newItems.filter((item) => item.source === selectedSource) : newItems;
  const trendingTopics = getTrendingTopics(newItems);
  const topTopics = getTopTopics(newItems);

  if (loading) {
    return (
      <NewDashboardShell title={t("app.news.title", "en")}>
        <div className="flex min-h-[40vh] items-center justify-center text-muted-foreground">
          {t("app.news.loading", "en")}
        </div>
      </NewDashboardShell>
    );
  }

  return (
    <NewDashboardShell title={t("app.news.title", "en")}>
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        {/* News Filters */}
        <div className="lg:col-span-1 space-y-4">
          <TarotCard icon="Search" title={false ? "فیلترها" : "Filters"}>
            <div className="space-y-2">
              <button
                onClick={() => setSelectedSource(null)}
                className={cn(
                  "w-full text-right px-3 py-2 rounded-lg text-sm transition-colors",
                   selectedSource === null ? "bg-error text-white shadow-md" : "hover:bg-muted/50 text-muted-foreground"
                )}
              >
                {false ? "همه اخبار" : "All News"}
              </button>
              {sources.map((source) => (
                <button
                  key={source}
                  onClick={() => setSelectedSource(source)}
                  className={cn(
                    "w-full text-right px-3 py-2 rounded-lg text-sm transition-colors",
                     selectedSource === source ? "bg-error text-white shadow-md" : "hover:bg-muted/50 text-muted-foreground"
                  )}
                >
                  {source}
                </button>
              ))}
            </div>
          </TarotCard>

          {/* Trending Topics */}
          <TarotCard icon="🔥" title={false ? "موضوعات داغ" : "Trending Topics"}>
            <div className="space-y-2">
              {topTopics.map((topic, i) => (
                <div key={i} className="flex items-center justify-between font-medium text-sm">
                  <span className="flex-1">{topic.topic}</span>
                  <span className="text-xs text-muted-foreground">{topic.count} {false ? "خبر" : "news"}</span>
                </div>
              ))}
              {topTopics.length === 0 && (
                <p className="text-sm text-muted-foreground">
                  {false ? "موضوع داغی یافت نشد" : "No trending topics found"}
                </p>
              )}
            </div>
          </TarotCard>
        </div>

        {/* News List */}
        <div className="lg:col-span-3">
          <TarotCard 
            icon="📰" 
            title={selectedSource 
              ? (false ? `اخبار از ${selectedSource}` : `News from ${selectedSource}`) 
              : (false ? "همه اخبار" : "All News")
            }
          >
            <NewsList items={filteredNews} />
          </TarotCard>
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
