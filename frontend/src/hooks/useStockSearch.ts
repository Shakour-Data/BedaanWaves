import { useState, useEffect, useRef, useCallback } from "react";
import type { StockSearchResult } from "./types";
import { apiClient } from "@/lib/api";

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

const searchCache = new Map<string, StockSearchResult[]>();

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

async function apiSearch(query: string): Promise<StockSearchResult[]> {
  const params = new URLSearchParams({ q: query, limit: "20" });
  const res = await apiClient.get(`/stocks/search?${params.toString()}`);
  const items = res.data?.data ?? [];
  return items.map((item: Record<string, unknown>) => ({
    symbol: (item.symbol ?? item.ticker ?? "") as string,
    name: (item.name ?? item.security_name ?? "") as string,
    sector: (item.sector ?? "") as string,
    price: typeof item.price === "number" ? item.price : 0,
    change: typeof item.change === "number" ? item.change : 0,
  }));
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

    if (trimmed.length < minQueryLength) {
      setSearchState((prev) => ({ ...prev, results: [], status: trimmed.length === 0 ? "idle" : "idle" }));
      return;
    }

    const cacheKey = trimmed.toLowerCase();

    // Return cached result if available
    if (searchCache.has(cacheKey)) {
      setSearchState((prev) => ({
        ...prev,
        query: trimmed,
        results: searchCache.get(cacheKey)!,
        status: "success",
        error: null,
      }));
      return;
    }

    // Set loading state
    setSearchState((prev) => ({
      ...prev,
      query: trimmed,
      status: "loading",
      error: null,
    }));

    // Abort any in-flight request
    abortControllerRef.current?.abort();
    const controller = new AbortController();
    abortControllerRef.current = controller;

    let cancelled = false;

    async function performSearch() {
      try {
        let results: StockSearchResult[] = [];

        try {
          const apiResults = await apiSearch(trimmed);
          if (!cancelled && !controller.signal.aborted) {
            results = apiResults;
          }
        } catch (err) {
          if (!cancelled && !controller.signal.aborted) {
            throw err;
          }
        }

        if (cancelled || controller.signal.aborted) return;

        // Cache the result
        searchCache.set(cacheKey, results);

        if (isMountedRef.current) {
          setSearchState((prev) => ({
            ...prev,
            query: trimmed,
            results,
            status: results.length === 0 ? "empty" : "success",
            error: null,
          }));
        }
      } catch (err) {
        if (cancelled || controller.signal.aborted) return;
        if (isMountedRef.current) {
          setSearchState((prev) => ({
            ...prev,
            query: trimmed,
            results: [],
            status: "error",
            error: err instanceof Error ? err.message : "Search failed",
          }));
        }
      }
    }

    performSearch();

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
