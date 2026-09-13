import { apiClient } from "../api";
import type {
  NewsItem,
  NewsCategory,
  NewsRegion,
  NewsPriority,
} from "@/lib/news-types";

export async function getMarketNews(limit = 20): Promise<NewsItem[]> {
  const res = await apiClient.get<{ data: NewsItem[] }>("/news/market?limit=" + limit);
  return res.data?.data || [];
}

export async function getNewsByCategory(
  category: NewsCategory,
  options?: {
    region?: NewsRegion;
    priority?: NewsPriority;
    limit?: number;
    symbol?: string;
  }
): Promise<NewsItem[]> {
  const params = new URLSearchParams();
  params.set("limit", String(options?.limit || 50));
  if (options?.region) params.set("region", options.region);
  if (options?.priority) params.set("priority", options.priority);
  if (options?.symbol) params.set("symbol", options.symbol);

  const res = await apiClient.get<{ data: NewsItem[] }>(
    `/news/category/${category}?${params.toString()}`
  );
  return res.data?.data || [];
}

export async function getMarketMovingNews(limit = 20): Promise<NewsItem[]> {
  const res = await apiClient.get<{ data: NewsItem[] }>("/news/market-moving?limit=" + limit);
  return res.data?.data || [];
}

export async function searchNews(query: string, limit = 20): Promise<NewsItem[]> {
  const res = await apiClient.get<{ data: NewsItem[] }>(
    `/news/search?q=${encodeURIComponent(query)}&limit=${limit}`
  );
  return res.data?.data || [];
}

export async function getNewsCategories(): Promise<Record<string, number>> {
  const res = await apiClient.get<{ data: Record<string, number> }>("/news/categories");
  return res.data?.data || {};
}

export async function getNewsRegions(): Promise<Record<string, number>> {
  const res = await apiClient.get<{ data: Record<string, number> }>("/news/regions");
  return res.data?.data || {};
}
