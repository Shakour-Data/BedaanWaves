import { useState, useEffect, useRef, useCallback } from "react";
import type { StockSearchResult } from "./types";
import { apiClient, getApiErrorMessage } from "@/lib/api";

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
// In-memory cache: Map<query_lowercase, StockSearchResult[]>
// ---------------------------------------------------------------------------

const searchCache = new Map<string, { results: StockSearchResult[]; timestamp: number }>();
const CACHE_TTL_MS = 5 * 60 * 1000;
const MAX_CACHE_ENTRIES = 100;

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
// Utility: Debounce
// ---------------------------------------------------------------------------

async function apiSearch(query: string, signal?: AbortSignal): Promise<StockSearchResult[]> {
  const params = new URLSearchParams({ q: query, limit: "20" });
  const res = await apiClient.get(`/stocks/search?${params.toString()}`, {
    signal,
  });
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
  const [searchState, setSearchState] = useState<SearchState>({
    query: "",
    results: [],
    status: "idle",
    error: null,
  });

  const debouncedQuery = useDebouncedValue(searchState.query, 300);
  const abortControllerRef = useRef<AbortController | null>(null);
  const isMountedRef = useRef(true);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      isMountedRef.current = false;
      abortControllerRef.current?.abort();
    };
  }, []);

  // Fetch logic
  useEffect(() => {
    const trimmed = debouncedQuery.trim();

    abortControllerRef.current?.abort();

    if (trimmed.length < minQueryLength) {
      setSearchState((prev) => ({ ...prev, results: [], status: "idle" }));
      return;
    }

    const cacheKey = trimmed.toLowerCase();

    const cached = searchCache.get(cacheKey);
    if (cached && Date.now() - cached.timestamp < CACHE_TTL_MS) {
      setSearchState((prev) => ({
        ...prev,
        query: trimmed,
        results: cached.results,
        status: "success",
        error: null,
      }));
      return;
    }

    setSearchState((prev) => ({
      ...prev,
      query: trimmed,
      status: "loading",
      error: null,
    }));

    const controller = new AbortController();
    abortControllerRef.current = controller;

    let cancelled = false;

    async function performSearch() {
      try {
        const apiResults = await apiSearch(trimmed, controller.signal);
        if (cancelled || controller.signal.aborted) return;

        searchCache.set(cacheKey, { results: apiResults, timestamp: Date.now() });
        while (searchCache.size > MAX_CACHE_ENTRIES) {
          const oldestKey = searchCache.keys().next().value;
          if (oldestKey === undefined) break;
          searchCache.delete(oldestKey);
        }

        if (!isMountedRef.current) return;
        setSearchState((prev) => ({
          ...prev,
          query: trimmed,
          results: apiResults,
          status: apiResults.length === 0 ? "empty" : "success",
          error: null,
        }));
      } catch (err) {
        if (cancelled || controller.signal.aborted || !isMountedRef.current) return;
        setSearchState((prev) => ({
          ...prev,
          query: trimmed,
          results: [],
          status: "error",
          error: getApiErrorMessage(err),
        }));
      }
    }

    void performSearch();

    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [debouncedQuery, minQueryLength]);

  // Expose a manual search setter (bypasses debounce if needed)
  const setQuery = useCallback((q: string) => {
    setSearchState((prev) => ({ ...prev, query: q }));
  }, []);

  const clearResults = useCallback(() => {
    setSearchState({ query: "", results: [], status: "idle", error: null });
  }, []);

  return {
    ...searchState,
    setQuery,
    clearResults,
  };
}
