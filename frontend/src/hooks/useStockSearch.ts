import { useState, useEffect, useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import type { StockSearchResult } from "./types";
import { apiClient, getApiErrorMessage } from "@/lib/api";
import { QK } from "@/lib/query-keys";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type SearchStatus = "idle" | "loading" | "success" | "error" | "empty";

export interface SearchState {
  query: string;
  results: StockSearchResult[];
  status: SearchStatus;
  error: string | null;
}

// ---------------------------------------------------------------------------
// Utility: Debounce
// ---------------------------------------------------------------------------

function useDebouncedValue<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debounced;
}

// ---------------------------------------------------------------------------
// API helper
// ---------------------------------------------------------------------------

async function apiSearch(query: string): Promise<StockSearchResult[]> {
  const params = new URLSearchParams({ q: query, limit: "20" });
  const res = await apiClient.get(`/stocks/search?${params.toString()}`);
  const items = res.data?.data ?? [];
  return items.map((item: Record<string, unknown>) => {
    const price = typeof item.price === "number" ? item.price : 0;
    const change = typeof item.change === "number" ? item.change : 0;
    const changePct =
      typeof item.change_percent === "number"
        ? item.change_percent
        : typeof item.changePct === "number"
        ? item.changePct
        : price > 0
        ? (change / price) * 100
        : 0;
    return {
      symbol: (item.symbol ?? item.ticker ?? "") as string,
      name: (item.name ?? item.security_name ?? "") as string,
      sector: (item.sector ?? "") as string,
      industry: (item.industry ?? "") as string,
      exchange: (item.exchange ?? "") as string,
      currency: (item.currency ?? "USD") as string,
      price,
      change,
      changePct,
      marketCap: typeof item.market_cap === "number" ? item.market_cap : undefined,
      peRatio: typeof item.pe_ratio === "number" ? item.pe_ratio : undefined,
    };
  });
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useStockSearch(minQueryLength = 1) {
  const [query, setQuery] = useState("");
  const debouncedQuery = useDebouncedValue(query, 300);
  const trimmed = debouncedQuery.trim();
  const canSearch = trimmed.length >= minQueryLength;

  const { data, isLoading, error } = useQuery<StockSearchResult[]>({
    queryKey: QK.stocksSearch(trimmed),
    queryFn: () => apiSearch(trimmed),
    enabled: canSearch,
    staleTime: 5 * 60 * 1000, // 5 min — replaces manual cache
    gcTime: 10 * 60 * 1000,
    retry: 1,
  });

  const results = data ?? [];
  const status: SearchStatus = !canSearch
    ? "idle"
    : isLoading
      ? "loading"
      : error
        ? "error"
        : results.length === 0
          ? "empty"
          : "success";

  const clearResults = useCallback(() => {
    setQuery("");
  }, []);

  return {
    query,
    results,
    status,
    error: error ? getApiErrorMessage(error) : null,
    setQuery,
    clearResults,
  };
}
