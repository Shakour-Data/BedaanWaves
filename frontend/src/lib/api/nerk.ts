/**
 * nerk-api.ts
 * ---------------------------------------------------------------------------
 * Data access layer for the Neark (نزدک) index pages.
 */

import { apiClient } from "@/lib/api";

export interface NerkConstituent {
  id: string;
  symbol: string;
  name: string;
  sector: string | null;
  asset_class: string;
  market: string;
  active: boolean;
  price: number;
  change_pct: number;
  nerk_weight: number | null;
}

export interface NerkOverviewResponse {
  status: string;
  index: string;
  exchange: string;
  market_overview: {
    market: string;
    total_symbols: number;
    active_symbols: number;
    currency: string;
    timezone: string;
    index: string;
    last_updated: string;
    constituents_count: number;
    avg_change_pct: number;
    gainers_count: number;
    losers_count: number;
  };
  constituents_count: number;
  top_gainers: Array<{
    symbol: string;
    name: string;
    price: number;
    change_pct: number;
  }>;
  top_losers: Array<{
    symbol: string;
    name: string;
    price: number;
    change_pct: number;
  }>;
  avg_change_pct: number;
  timestamp: string;
}

export interface NerkPriceHistoryResponse {
  status: string;
  symbol: string;
  name: string;
  market: string;
  period: string;
  count: number;
  data: Array<{
    timestamp: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
    turnover?: number;
    adjusted_close?: number;
  }>;
  timestamp: string;
}

export async function fetchNerkConstituents(): Promise<NerkConstituent[]> {
  const { data } = await apiClient.get("/api/v1/nerk/constituents");
  return data.data ?? [];
}

export async function fetchNerkOverview(): Promise<NerkOverviewResponse> {
  const { data } = await apiClient.get("/api/v1/nerk/overview");
  return data;
}

export async function fetchNerkPriceHistory(
  symbol: string,
  period: string = "1y"
): Promise<NerkPriceHistoryResponse> {
  const { data } = await apiClient.get(`/api/v1/nerk/price-history/${encodeURIComponent(symbol)}`, {
    params: { period },
  });
  return data;
}
