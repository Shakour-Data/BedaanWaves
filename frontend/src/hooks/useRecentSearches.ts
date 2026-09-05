import { useState, useEffect, useCallback } from "react";
import { apiClient, getApiErrorMessage } from "@/lib/api";

export interface RecentSearchesState {
  recent: string[];
  loading: boolean;
  error: string | null;
}

export function useRecentSearches() {
  const [state, setState] = useState<RecentSearchesState>({
    recent: [],
    loading: true,
    error: null,
  });

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const res = await apiClient.get<{ recent_searches?: string[] }>(
          "/settings/recent-searches"
        );
        const list = Array.isArray(res.data?.recent_searches)
          ? res.data.recent_searches
          : [];
        if (!cancelled) {
          setState({ recent: list, loading: false, error: null });
        }
      } catch (err) {
        if (!cancelled) {
          setState({ recent: [], loading: false, error: getApiErrorMessage(err) });
        }
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  const addRecent = useCallback(async (query: string) => {
    const value = query.trim().toUpperCase();
    if (!value) return;
    try {
      const res = await apiClient.post<{ recent_searches?: string[] }>(
        "/settings/recent-searches",
        { query: value }
      );
      const list = Array.isArray(res.data?.recent_searches)
        ? res.data.recent_searches
        : [];
      setState((prev) => ({ ...prev, recent: list, error: null }));
    } catch (err) {
      setState((prev) => ({ ...prev, error: getApiErrorMessage(err) }));
    }
  }, []);

  return { ...state, addRecent };
}
