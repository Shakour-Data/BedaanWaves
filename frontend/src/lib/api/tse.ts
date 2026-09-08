/**
 * tse-api.ts
 * ---------------------------------------------------------------------------
 * Data access layer for the Tehran Stock Exchange (TSE) / Neark index pages.
 */

import { apiClient } from "@/lib/api";

export interface TseConstituent {
  symbol: string;
  name: string;
  sector: string | null;
  asset_class: string;
  market: string;
  active: boolean;
}

export interface TseOverviewResponse {
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

export interface TseMarketOverviewResponse {
  status: string;
  data: {
    market: string;
    total_symbols: number;
    active_symbols: number;
    currency: string;
    timezone: string;
    index: string;
    last_updated: string;
  };
  timestamp: string;
}

export interface TsePriceHistoryResponse {
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

export async function fetchNerkConstituents(): Promise<TseConstituent[]> {
  const { data } = await apiClient.get("/api/v1/tse/nerk/constituents");
  return data.data ?? [];
}

export async function fetchNerkOverview(): Promise<TseOverviewResponse> {
  const { data } = await apiClient.get("/api/v1/tse/nerk/overview");
  return data;
}

export async function fetchNerkPriceHistory(
  symbol: string,
  period: string = "1y"
): Promise<TsePriceHistoryResponse> {
  const { data } = await apiClient.get(`/api/v1/tse/nerk/price-history/${encodeURIComponent(symbol)}`, {
    params: { period },
  });
  return data;
}

export async function fetchTseSymbols(
  limit: number = 100,
  offset: number = 0
): Promise<{ total: number; data: TseConstituent[] }> {
  const { data } = await apiClient.get("/api/v1/tse/symbols", {
    params: { limit, offset },
  });
  return { total: data.total ?? 0, data: data.data ?? [] };
}

export async function fetchTseMarketOverview(): Promise<TseMarketOverviewResponse> {
  const { data } = await apiClient.get("/api/v1/tse/market-overview");
  return data;
}
