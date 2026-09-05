/**
 * watchlist.ts
 * ---------------------------------------------------------------------------
 * Data access layer for user watchlists and watchlist items.
 */

import { apiClient } from "@/lib/api";

export interface WatchlistItem {
  id: string;
  watchlist_id: string;
  asset_id: string;
  note: string | null;
  alert_threshold_pct: number | null;
  created_at: string;
  asset?: {
    symbol: string;
    name: string;
    market: string;
  };
}

export interface Watchlist {
  id: string;
  user_id: string;
  name: string;
  description: string | null;
  is_default: boolean;
  items: WatchlistItem[];
  created_at: string;
  updated_at: string;
}

export interface CreateWatchlistPayload {
  name: string;
  description?: string | null;
  is_default?: boolean;
}

export interface UpdateWatchlistPayload {
  name?: string;
  description?: string | null;
  is_default?: boolean;
}

export interface CreateWatchlistItemPayload {
  asset_id: string;
  note?: string | null;
  alert_threshold_pct?: number | null;
}

export interface UpdateWatchlistItemPayload {
  note?: string | null;
  alert_threshold_pct?: number | null;
}

export async function fetchWatchlists(): Promise<Watchlist[]> {
  const res = await apiClient.get<Watchlist[]>("/watchlists");
  return res.data;
}

export async function fetchWatchlist(watchlistId: string): Promise<Watchlist> {
  const res = await apiClient.get<Watchlist>(`/watchlists/${watchlistId}`);
  return res.data;
}

export async function createWatchlist(payload: CreateWatchlistPayload): Promise<Watchlist> {
  const res = await apiClient.post<Watchlist>("/watchlists", payload);
  return res.data;
}

export async function updateWatchlist(
  watchlistId: string,
  payload: UpdateWatchlistPayload
): Promise<Watchlist> {
  const res = await apiClient.put<Watchlist>(`/watchlists/${watchlistId}`, payload);
  return res.data;
}

export async function deleteWatchlist(watchlistId: string): Promise<void> {
  await apiClient.delete(`/watchlists/${watchlistId}`);
}

export async function addWatchlistItem(
  watchlistId: string,
  payload: CreateWatchlistItemPayload
): Promise<WatchlistItem> {
  const res = await apiClient.post<WatchlistItem>(`/watchlists/${watchlistId}/items`, payload);
  return res.data;
}

export async function updateWatchlistItem(
  watchlistId: string,
  itemId: string,
  payload: UpdateWatchlistItemPayload
): Promise<WatchlistItem> {
  const res = await apiClient.put<WatchlistItem>(`/watchlists/${watchlistId}/items/${itemId}`, payload);
  return res.data;
}

export async function removeWatchlistItem(watchlistId: string, itemId: string): Promise<void> {
  await apiClient.delete(`/watchlists/${watchlistId}/items/${itemId}`);
}
