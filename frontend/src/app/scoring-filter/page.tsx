"use client";

import { useState, useEffect, useCallback } from "react";
import { FilterBuilder } from "@/components/filter/FilterBuilder";
import { ActiveFilters } from "@/components/filter/ActiveFilters";
import { IndustryQuickFilter } from "@/components/filter/IndustryQuickFilter";
import { fetchAdvancedFilter, fetchFilterableFields } from "@/lib/api/filter";
import type { FilterableField, AdvancedFilterResponse, FilterGroup, FilterCondition, Level } from "@/types/filter";
import { LEVEL_LABELS, LEVEL_COLORS } from "@/types/filter";
import { Spinner } from "@/components/ui/Spinner";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { useUXStore } from "@/store/useUXStore";

function useDebounce<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return debounced;
}

function createEmptyGroup(): FilterGroup {
  return {
    id: `g_${Date.now()}`,
    logic: "AND",
    conditions: [
      {
        id: `c_${Date.now()}`,
        field: "overall_score",
        operator: ">",
        value: 500,
        level: "overall",
      } as FilterCondition,
    ],
  };
}

export default function ScoringFilterPage() {
  const addToast = useUXStore((state) => state.addToast);

  const [fields, setFields] = useState<FilterableField[]>([]);
  const [query, setQuery] = useState<FilterGroup>(createEmptyGroup());
  const [results, setResults] = useState<AdvancedFilterResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [industryFilter, setIndustryFilter] = useState<string[]>([]);

  const debouncedQuery = useDebounce(query, 500);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setError(null);

    let cancelled = false;
    (async () => {
      try {
        const data = await fetchFilterableFields();
        if (!cancelled) setFields(data);
      } catch {
        if (!cancelled) addToast({ type: "error", message: "Failed to load filter fields" });
      }
    })();

    return () => { cancelled = true; };
  }, [addToast]);

  const applyFilter = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = {
        query: debouncedQuery,
        limit: 50,
        offset: 0,
        sort_by: "score",
        sort_dir: "desc" as const,
      };
      const data = await fetchAdvancedFilter(payload);
      setResults(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Filter failed";
      setError(message);
      addToast({ type: "error", message });
    } finally {
      setLoading(false);
    }
  }, [debouncedQuery, addToast]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    applyFilter();
  }, [applyFilter]);

  const handleApply = useCallback(() => {
    setQuery((q) => ({ ...q }));
  }, []);

  const handleClearAll = useCallback(() => {
    setQuery(createEmptyGroup());
    setIndustryFilter([]);
  }, []);

  const handleIndustryChange = useCallback((industries: string[]) => {
    setIndustryFilter(industries);
    if (industries.length === 0) return;
    setQuery((q) => {
      const withoutIndustry = q.conditions.filter(
        (c) => "logic" in c || c.field !== "industry",
      );
      const newCond = {
        id: `c_${Date.now()}`,
        field: "industry" as const,
        operator: "in_list" as const,
        value: industries,
        level: "overall" as Level,
      };
      return { ...q, conditions: [...withoutIndustry, newCond] };
    });
  }, []);

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
        <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">
          Advanced Scoring Filter
        </h1>
        <p className="mt-1 text-xs text-[var(--color-text-secondary)]">
          Build complex nested filters across Overall, Dimensions, Sub-Dimensions, Aspects, and Sub-Aspects.
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <IndustryQuickFilter
          fields={fields}
          selected={industryFilter}
          onChange={handleIndustryChange}
        />
        <button
          type="button"
          onClick={handleClearAll}
          className="rounded-lg px-4 py-2 text-sm font-medium text-[var(--color-error)] hover:bg-error/10"
        >
          Clear All Filters
        </button>
      </div>

      <FilterBuilder
        query={query}
        fields={fields}
        onChange={setQuery}
        onApply={handleApply}
        loading={loading}
      />

      <ActiveFilters
        applied={results?.applied_filters ?? []}
        onClearAll={handleClearAll}
      />

      {error && (
        <ErrorMessage
          message={error}
          actions={[{ label: "Retry", onAction: () => setQuery((q) => ({ ...q })) }]}
        />
      )}

      <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">
              Results
            </h2>
            {results && (
              <p className="text-xs text-[var(--color-text-secondary)] mt-1">
                {results.total} matches • {results.execution_time_ms}ms
              </p>
            )}
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Spinner size="lg" />
          </div>
        ) : results && results.results.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-[var(--color-border)]">
                  <th className="pb-2 font-semibold text-[var(--color-text-secondary)]">Symbol</th>
                  <th className="pb-2 font-semibold text-[var(--color-text-secondary)]">Name</th>
                  <th className="pb-2 font-semibold text-[var(--color-text-secondary)]">Level</th>
                  <th className="pb-2 font-semibold text-[var(--color-text-secondary)]">Score</th>
                  <th className="pb-2 font-semibold text-[var(--color-text-secondary)]">Change</th>
                  <th className="pb-2 font-semibold text-[var(--color-text-secondary)]">Industry</th>
                  <th className="pb-2 font-semibold text-[var(--color-text-secondary)]">Date</th>
                </tr>
              </thead>
              <tbody>
                {results.results.map((row) => (
                  <tr key={row.id as string} className="border-b border-[var(--color-border)] last:border-0">
                    <td className="py-3 font-mono text-[var(--color-primary)]">{row.symbol as string}</td>
                    <td className="py-3 text-[var(--color-text-primary)]">{row.name as string}</td>
                    <td className="py-3">
                      <span
                        className="inline-flex items-center rounded-full whitespace-nowrap border px-2 py-0.5 text-[10px] font-medium"
                        style={{
                          backgroundColor: `${LEVEL_COLORS[row.level as keyof typeof LEVEL_COLORS] ?? "#666"}15`,
                          color: LEVEL_COLORS[row.level as keyof typeof LEVEL_COLORS] ?? "#666",
                          borderColor: `${LEVEL_COLORS[row.level as keyof typeof LEVEL_COLORS] ?? "#666"}40`,
                        }}
                      >
                        {LEVEL_LABELS[row.level as keyof typeof LEVEL_LABELS] ?? row.level}
                      </span>
                    </td>
                    <td className="py-3 font-semibold text-[var(--color-text-primary)]">
                      {typeof row.score === "number" ? row.score.toFixed(2) : "—"}
                    </td>
                    <td className={`py-3 ${typeof row.score_change === "number" && row.score_change >= 0 ? "text-success" : "text-error"}`}>
                      {typeof row.score_change === "number" ? `${row.score_change >= 0 ? "+" : ""}${row.score_change.toFixed(2)}` : "—"}
                    </td>
                    <td className="py-3 text-[var(--color-text-secondary)]">{row.industry as string ?? "—"}</td>
                    <td className="py-3 text-[var(--color-text-secondary)]">{row.date as string ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="py-12 text-center text-sm text-[var(--color-text-secondary)]">
            No results match your filters. Try adjusting your criteria.
          </div>
        )}
      </div>
    </div>
  );
}
