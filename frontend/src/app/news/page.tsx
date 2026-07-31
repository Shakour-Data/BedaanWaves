"use client";

import { useState, useEffect, useRouter } from "react";
import Link from "next/link";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { TarotCard } from "@/components/ui/TarotCard";
import { NewsList } from "@/components/dashboard/NewsList";
import { AssetTable } from "@/components/dashboard/AssetTable";
import { useAppStore } from "@/store/useAppStore";
import { cn } from "@/lib/cn";
import { apiClient } from "@/lib/api";
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
            time: formatTimeAgo(item.published_at || item.created_at),
          }));

          setNewItems(formattedNews);
        }
      } catch (error) {
        console.error("Failed to load news:", error);
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
    if (minutes < 1) return "همین الان";
    if (minutes < 60) return `${minutes} دقیقه پیش`;
    if (hours < 24) return `${hours} ساعت پیش`;
    return `${days} روز پیش`;
  };

  const sources = Array.from(new Set(newItems.map((item) => item.source)));
  const filteredNews = selectedSource ? newItems.filter((item) => item.source === selectedSource) : newItems;
  const trendingTopics = getTrendingTopics();

  if (loading) {
    return (
      <DashboardShell title="اخبار">
        <div className="flex min-h-[40vh] items-center justify-center text-muted-foreground">
          در حال بارگذاری اخبار...
        </div>
      </DashboardShell>
    );
  }

  return (
    <DashboardShell title="اخبار">
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        {/* News Filters */}
        <div className="lg:col-span-1 space-y-4">
          <TarotCard icon="🔍" title="فیلترها">
            <div className="space-y-2">
              <button
                onClick={() => setSelectedSource(null)}
                className={`w-full text-right px-3 py-2 rounded-lg text-sm transition-colors ${selectedSource === null ? "bg-secondary text-secondary-foreground" : "hover:bg-muted/50"}`}
              >
                همه اخبار
              </button>
              {sources.map((source) => (
                <button
                  key={source}
                  onClick={() => setSelectedSource(source)}
                  className={`w-full text-right px-3 py-2 rounded-lg text-sm transition-colors ${selectedSource === source ? "bg-secondary text-secondary-foreground" : "hover:bg-muted/50"}`}
                >
                  {source}
                </button>
              ))}
            </div>
          </TarotCard>

          {/* Super Topics */}
          <TarotCard icon="🔥" title="موضوعات داغ">
            <div className="space-y-2">
              {getTopTopics().map((topic, i) => (
                <div key={i} className="flex items-center justify-between font-medium text-sm">
                  <span className="flex-1">{topic.topic}</span>
                  <span className="text-xs text-muted-foreground">{topic.count} خبر</span>
                </div>
              ))}
            </div>
          </TarotCard>
        </div>

        {/* News List */}
        <div className="lg:col-span-3">
          <TarotCard icon="📰" title={selectedSource ? `اخبار از ${selectedSource}` : "همه اخبار"}>
            <NewsList items={filteredNews} />
          </TarotCard>
        </div>
      </div>
    </DashboardShell>
  );
}

function getTopTopics(): { topic: string; count: number }[] {
  // This would ideally pull from actual trend data
  // Fallback implementation
  return [];
}