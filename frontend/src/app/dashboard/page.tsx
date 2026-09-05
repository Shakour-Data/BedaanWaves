"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useSearchParams } from "next/navigation";
import { apiClient, getApiErrorMessage } from "@/lib/api";
import { cn } from "@/lib/cn";
import { fetchDashboardData, fetchGeneralDashboard, fetchTechnicalDashboard, fetchFundamentalDashboard, fetchNewsDashboard, fetchRiskDashboard, fetchBoardDashboard, fetchAiDashboard, fetchScoreTrend, fetchCoefficientHistory, fetchSubDimensionTrend, fetchAspectTrend, fetchSubAspectTrend } from "@/lib/api/dashboard";
import type { AssetRow, MarketStat, NewsItem } from "@/lib/dashboard-data";
import type { GeneralDashboardResponse, DimensionDashboardResponse, NewsDashboardResponse, BoardDashboardResponse, AiDashboardResponse, ScoreTrendResponse, LevelTrendResponse, CoefficientHistoryResponse } from "@/lib/api/dashboard";
import { StockDetailSkeleton } from "@/components/ux/SkeletonLoaders";
import { useUXStore } from "@/store/useUXStore";
import { useDateStore, useSelectedDate, useLatestAvailableDate, useEffectiveDate } from "@/store/useDateStore";
import { DateSelector } from "@/components/dashboard/DateSelector";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { SpiderChart } from "@/components/charts/SpiderChart";
import { ScoreTrendChart } from "@/components/charts/ScoreTrendChart";
import { CoefficientChart } from "@/components/charts/CoefficientChart";
import { ColumnChart } from "@/components/charts/ColumnChart";
import { BarChart } from "@/components/charts/BarChart";
import { DimensionDashboard } from "@/components/dashboard/DimensionDashboard";
import { NewsDashboard } from "@/components/dashboard/NewsDashboard";
import { BoardDashboard } from "@/components/dashboard/BoardDashboard";
import { AiDashboard } from "@/components/dashboard/AiDashboard";

type Tab = "general" | "technical" | "fundamental" | "news" | "risk" | "board" | "ai";

type ScoreTrendOptions = {
  latest?: boolean;
  endDate?: string;
};

const tabs: { id: Tab; label: string; shortcut: string }[] = [
  { id: "general", label: "General", shortcut: "G" },
  { id: "technical", label: "Technical", shortcut: "T" },
  { id: "fundamental", label: "Fundamental", shortcut: "F" },
  { id: "news", label: "News", shortcut: "N" },
  { id: "risk", label: "Risk", shortcut: "R" },
  { id: "board", label: "Board", shortcut: "B" },
  { id: "ai", label: "AI", shortcut: "A" },
];

const DIMENSION_LABELS: Record<string, string> = {
  fundamental: "Fundamental",
  technical: "Technical",
  sentiment: "Sentiment",
  risk: "Risk",
  macro: "Macro",
  ai: "AI",
};

const DIMENSION_COLORS = [
  "#2563EB",
  "#10B981",
  "#F59E0B",
  "#EF4444",
  "#8B5CF6",
  "#EC4899",
];

const COEFFICIENT_COLOR_BY_KEY: Record<string, string> = {
  fundamental: "#2563EB",
  technical: "#10B981",
  sentiment: "#F59E0B",
  risk: "#EF4444",
  macro: "#8B5CF6",
  ai: "#EC4899",
};

function CoefficientFilterableChart({
  coefficients,
  filter,
  onFilterChange,
}: {
  coefficients: Array<{ key: string; label: string; weight: number }>;
  filter: Set<string>;
  onFilterChange: (next: Set<string>) => void;
}) {
  const toggle = (key: string) => {
    const next = new Set(filter);
    if (next.has(key)) next.delete(key);
    else next.add(key);
    onFilterChange(next);
  };
  const visible = coefficients.filter((c) => !filter.has(c.key));
  return (
    <div>
      <div className="mb-3 flex flex-wrap gap-2">
        {coefficients.map((c) => {
          const hidden = filter.has(c.key);
          return (
            <button
              key={c.key}
              type="button"
              onClick={() => toggle(c.key)}
              aria-pressed={!hidden}
              className={cn(
                "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium transition-opacity",
                hidden
                  ? "border-[var(--color-border)] bg-[var(--color-background)] opacity-50"
                  : "border-transparent bg-[var(--color-background)]"
              )}
            >
              <span
                className="inline-block h-2.5 w-2.5 rounded-full"
                style={{ backgroundColor: COEFFICIENT_COLOR_BY_KEY[c.key] ?? "#2563EB" }}
              />
              <span>{c.label}</span>
              <span className="text-[var(--color-text-secondary)]">{(c.weight * 100).toFixed(0)}%</span>
            </button>
          );
        })}
        {filter.size > 0 && (
          <button
            type="button"
            onClick={() => onFilterChange(new Set())}
            className="rounded-full border border-[var(--color-border)] px-2.5 py-1 text-xs font-medium text-[var(--color-text-secondary)] hover:bg-[var(--color-background)]"
          >
            Show all
          </button>
        )}
      </div>
      {visible.length === 0 ? (
        <p className="py-6 text-center text-xs text-[var(--color-text-secondary)]">
          All dimensions hidden — clear the filter to see the chart.
        </p>
      ) : (
        <CoefficientChart
          data={visible.map((c) => ({
            key: c.key,
            label: c.label,
            weight: c.weight,
          }))}
          height={Math.max(200, visible.length * 40 + 60)}
        />
      )}
    </div>
  );
}

function LevelTrendSection({
  title,
  description,
  response,
}: {
  title: string;
  description: string;
  response: LevelTrendResponse | null;
}) {
  if (!response) {
    return (
      <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] p-4">
        <div className="mb-2">
          <h3 className="text-sm font-semibold text-[var(--color-text-primary)]">{title}</h3>
          <p className="text-[11px] text-[var(--color-text-secondary)]">{description}</p>
        </div>
        <div className="flex items-center justify-center py-8">
          <div className="h-6 w-6 animate-spin rounded-full border-4 border-[var(--color-primary)] border-t-transparent" />
        </div>
      </div>
    );
  }

  if (response.series.length === 0) {
    return (
      <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] p-4">
        <div className="mb-2">
          <h3 className="text-sm font-semibold text-[var(--color-text-primary)]">{title}</h3>
          <p className="text-[11px] text-[var(--color-text-secondary)]">{description}</p>
        </div>
        <p className="py-6 text-center text-[var(--color-text-secondary)]">No data available</p>
      </div>
    );
  }

  const seriesKeys = response.keys.filter(
    (k) => response.series.some((pt) => (pt.avg_scores[k] ?? 0) > 0)
  );

  return (
    <div className="space-y-3">
      <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] p-4">
        <div className="mb-2">
          <h3 className="text-sm font-semibold text-[var(--color-text-primary)]">{title} — Trend</h3>
          <p className="text-[11px] text-[var(--color-text-secondary)]">{description}</p>
          {response.latest_date && (
            <p className="text-[10px] text-[var(--color-text-secondary)]">
              Last 30 days — ending {new Date(response.latest_date).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
            </p>
          )}
        </div>
        <ScoreTrendChart
          showLegend
          series={seriesKeys.map((key, i) => ({
            key,
            label: SUB_DIMENSION_KEY_LABELS[key] ?? key,
            color: DIMENSION_COLORS[i % DIMENSION_COLORS.length],
            data: response.series.map((pt) => ({ time: pt.date, value: pt.avg_scores[key] ?? 0 })),
          }))}
          height={260}
        />
      </div>
      <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] p-4">
        <div className="mb-2">
          <h3 className="text-sm font-semibold text-[var(--color-text-primary)]">{title} — Daily Change</h3>
          <p className="text-[11px] text-[var(--color-text-secondary)]">
            Day-over-day change summed across all series (green = up, red = down)
          </p>
        </div>
        <BarChart
          data={response.series.map((pt) => {
            const total = Object.values(pt.score_changes ?? {}).reduce((sum, v) => sum + v, 0);
            return { time: pt.date, value: total, color: total >= 0 ? "#10b981" : "#ef4444" };
          })}
          height={200}
        />
      </div>
    </div>
  );
}

const SUB_DIMENSION_KEY_LABELS: Record<string, string> = {
  valuation: "Valuation",
  profitability: "Profitability",
  growth: "Growth",
  liquidity: "Liquidity",
  efficiency: "Efficiency",
  corporate_actions: "Corporate Actions",
  moving_averages: "Moving Averages",
  momentum: "Momentum",
  volatility: "Volatility",
  volume: "Volume",
  trend: "Trend",
  news_sentiment: "News Sentiment",
  social_sentiment: "Social Sentiment",
  analyst_sentiment: "Analyst Sentiment",
  market_risk: "Market Risk",
  credit_risk: "Credit Risk",
  operational_risk: "Operational Risk",
  liquidity_risk: "Liquidity Risk",
  gdp: "GDP",
  inflation: "Inflation",
  interest_rates: "Interest Rates",
  exchange_rates: "Exchange Rates",
  commodity_prices: "Commodity Prices",
  ml_prediction: "ML Prediction",
  pattern_recognition: "Pattern Recognition",
  anomaly_detection: "Anomaly Detection",
};

export default function DashboardPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const tabParam = searchParams.get("tab") as Tab | null;
  const subParam = searchParams.get("sub");
  const [activeTab, setActiveTab] = useState<Tab>(tabParam && tabs.some(t => t.id === tabParam) ? tabParam : "general");
  const [activeSub, setActiveSub] = useState<string | null>(subParam);
  const [generalData, setGeneralData] = useState<GeneralDashboardResponse | null>(null);
  const [marketStats, setMarketStats] = useState<MarketStat[]>([]);
  const [topStocks, setTopStocks] = useState<AssetRow[]>([]);
  const [news, setNews] = useState<NewsItem[]>([]);
  const [scoreTrend, setScoreTrend] = useState<ScoreTrendResponse | null>(null);
  const [scoreTrendLoading, setScoreTrendLoading] = useState(true);
  const [subDimensionTrend, setSubDimensionTrend] = useState<LevelTrendResponse | null>(null);
  const [aspectTrend, setAspectTrend] = useState<LevelTrendResponse | null>(null);
  const [subAspectTrend, setSubAspectTrend] = useState<LevelTrendResponse | null>(null);
  const [subLevelChartsOpen, setSubLevelChartsOpen] = useState(false);
  const [coefficientHistory, setCoefficientHistory] = useState<CoefficientHistoryResponse | null>(null);
  const [coefficientHistoryLoading, setCoefficientHistoryLoading] = useState(true);
  const [coefficientFilter, setCoefficientFilter] = useState<Set<string>>(() => new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const addToast = useUXStore((state) => state.addToast);
  
  // Date Store Integration - Fix for data inconsistency
  const selectedDate = useSelectedDate();
  const latestAvailableDate = useLatestAvailableDate();
  const setLatestAvailableDate = useDateStore((state) => state.setLatestAvailableDate);
  const effectiveDate = useEffectiveDate();

  const loadDashboard = useCallback(async () => {
    // eslint-disable-next-line
    setLoading(true);
    // eslint-disable-next-line
    setError(null);

    try {
      // Fetch general dashboard with effective date if available
      const general = await fetchGeneralDashboard(!!effectiveDate).catch(() => null);
      
      // Update latest date from general data
      if (general?.latest_date) {
        // eslint-disable-next-line
        setLatestAvailableDate(general.latest_date);
      }
      
      const dashboardData = await fetchDashboardData(general ?? undefined);

      // eslint-disable-next-line
      setMarketStats(dashboardData.marketStats);
      const uniqueTop = dashboardData.topMovers.reduce<AssetRow[]>((acc, stock) => {
        if (!acc.some((s) => s.symbol === stock.symbol)) acc.push(stock);
        return acc;
      }, []);
      // eslint-disable-next-line
      setTopStocks(uniqueTop.slice(0, 5));
      // eslint-disable-next-line
      setNews(dashboardData.news);
      // eslint-disable-next-line
      setGeneralData(general);
    } catch (err) {
      const message = getApiErrorMessage(err);
      // eslint-disable-next-line
      setError(message);
      addToast({ type: "error", message });
    } finally {
      // eslint-disable-next-line
      setLoading(false);
    }
  }, [addToast, effectiveDate, fetchGeneralDashboard, fetchDashboardData, setLatestAvailableDate]);

  const loadScoreTrend = useCallback(async () => {
    // eslint-disable-next-line
    setScoreTrendLoading(true);
    try {
      const options: ScoreTrendOptions = effectiveDate
        ? { endDate: effectiveDate }
        : { latest: true };
      const data = await fetchScoreTrend(30, "NASDAQ", options);
      // eslint-disable-next-line
      setScoreTrend(data);
    } catch (err) {
      const message = getApiErrorMessage(err);
      // eslint-disable-next-line
      setError(message);
      addToast({ type: "error", message });
    } finally {
      // eslint-disable-next-line
      setScoreTrendLoading(false);
    }
  }, [effectiveDate, addToast]);

  const loadCoefficientHistory = useCallback(async () => {
    // eslint-disable-next-line
    setCoefficientHistoryLoading(true);
    try {
      const options: ScoreTrendOptions = effectiveDate
        ? { endDate: effectiveDate }
        : { latest: true };
      const data = await fetchCoefficientHistory(30, "NASDAQ", options);
      // eslint-disable-next-line
      setCoefficientHistory(data);
    } catch (err) {
      const message = getApiErrorMessage(err);
      // eslint-disable-next-line
      setError(message);
      addToast({ type: "error", message });
    } finally {
      // eslint-disable-next-line
      setCoefficientHistoryLoading(false);
    }
  }, [effectiveDate, addToast]);

  useEffect(() => {
    // eslint-disable-next-line
    loadScoreTrend();
    // eslint-disable-next-line
    loadCoefficientHistory();
  }, [loadScoreTrend, loadCoefficientHistory]);

  useEffect(() => {
    // eslint-disable-next-line
    loadDashboard();
  }, [loadDashboard]);

  useEffect(() => {
    const tab = searchParams.get("tab") as Tab | null;
    if (tab && tabs.some(t => t.id === tab) && tab !== activeTab) {
      // eslint-disable-next-line
      setActiveTab(tab);
    }
  }, [searchParams, activeTab]);

  useEffect(() => {
    const sub = searchParams.get("sub");
    if (sub !== activeSub) {
      // eslint-disable-next-line
      setActiveSub(sub);
    }
  }, [searchParams, activeSub]);

  const loadSubLevelTrends = useCallback(async (latestDate: string | null) => {
    const options: ScoreTrendOptions = latestDate
      ? { endDate: latestDate }
      : { latest: true };
    const [subDim, asp, subAsp] = await Promise.allSettled([
      fetchSubDimensionTrend(30, "NASDAQ", options),
      fetchAspectTrend(30, "NASDAQ", options),
      fetchSubAspectTrend(30, "NASDAQ", options),
    ]);
    if (subDim.status === "fulfilled") {
      // eslint-disable-next-line
      setSubDimensionTrend(subDim.value);
    }
    if (asp.status === "fulfilled") {
      // eslint-disable-next-line
      setAspectTrend(asp.value);
    }
    if (subAsp.status === "fulfilled") {
      // eslint-disable-next-line
      setSubAspectTrend(subAsp.value);
    }
  }, []);

  useEffect(() => {
    if (!subLevelChartsOpen) return;
    if (generalData?.latest_date) {
      loadSubLevelTrends(generalData.latest_date);
    } else {
      loadSubLevelTrends(null);
    }
  }, [generalData?.latest_date, subLevelChartsOpen, loadSubLevelTrends]);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) {
        return;
      }
      const key = event.key.toLowerCase();
      const tab = tabs.find((t) => t.shortcut.toLowerCase() === key);
      if (tab) {
        setActiveTab(tab.id);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const handleDimensionClick = (label: string) => {
    const map: Record<string, Tab> = {
      Fundamental: "fundamental",
      Technical: "technical",
      Sentiment: "news",
      Risk: "risk",
      "AI": "ai",
      Macro: "general",
    };
    const target = map[label];
    if (target) {
      router.push(`/dashboard?tab=${target}`);
    }
  };

  const handleTabChange = (tabId: Tab) => {
    setActiveTab(tabId);
    setActiveSub(null);
    router.push(`/dashboard?tab=${tabId}`, { scroll: false });
  };

  const handleSubChange = (sub: string | null) => {
    setActiveSub(sub);
    const params = new URLSearchParams();
    params.set("tab", activeTab);
    if (sub) params.set("sub", sub);
    router.push(`/dashboard?${params.toString()}`, { scroll: false });
  };

  const spiderData = generalData ? [
    { label: "Fundamental", value: generalData.dimensions.fundamental?.avg_score || 0 },
    { label: "Technical", value: generalData.dimensions.technical?.avg_score || 0 },
    { label: "Sentiment", value: generalData.dimensions.sentiment?.avg_score || 0 },
    { label: "Risk", value: generalData.dimensions.risk?.avg_score || 0 },
    { label: "Macro", value: generalData.dimensions.macro?.avg_score || 0 },
    { label: "AI", value: generalData.dimensions.ai?.avg_score || 0 },
  ] : [];

  if (loading) {
    return (
      <StockDetailSkeleton />
    );
  }

  if (error) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <ErrorMessage
          message={error}
          actions={[{ label: "Retry", onAction: () => { setError(null); loadDashboard(); } }]}
          moreHelpSteps={["Check your internet connection", "Verify the API service is running"]}
          helpTitle="Troubleshooting steps"
        />
      </div>
    );
  }

  const renderTabContent = () => {
    switch (activeTab) {
      case "general":
        return (
          <div className="space-y-6 animate-in fade-in duration-300">
            <div className="mb-8 grid gap-4 md:grid-cols-4">
              {marketStats.length > 0 ? (
                marketStats.map((stat, i) => (
                  <div key={i} className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm hover:shadow-md transition-shadow">
                    <p className="text-sm font-medium text-[var(--color-text-secondary)]">{stat.label}</p>
                    <p className="mt-2 text-2xl font-bold text-[var(--color-text-primary)] tabular-nums">{stat.value}</p>
                  </div>
                ))
              ) : (
                <>
                  <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
                    <p className="text-sm font-medium text-[var(--color-text-secondary)]">Nasdaq Composite</p>
                    <p className="mt-2 text-2xl font-bold text-[var(--color-text-primary)] tabular-nums">—</p>
                  </div>
                  <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
                    <p className="text-sm font-medium text-[var(--color-text-secondary)]">Active Symbols</p>
                    <p className="mt-2 text-2xl font-bold text-[var(--color-text-primary)] tabular-nums">—</p>
                  </div>
                  <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
                    <p className="text-sm font-medium text-[var(--color-text-secondary)]">Top Gainer</p>
                    <p className="mt-2 text-2xl font-bold text-[var(--color-text-primary)] tabular-nums">—</p>
                  </div>
                  <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
                    <p className="text-sm font-medium text-[var(--color-text-secondary)]">Top Loser</p>
                    <p className="mt-2 text-2xl font-bold text-[var(--color-text-primary)] tabular-nums">—</p>
                  </div>
                </>
              )}
            </div>

            {generalData && spiderData.length > 0 && (
              <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
                <div className="mb-4">
                  <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">6D Score Overview</h2>
                  <p className="text-xs text-[var(--color-text-secondary)]">Click a dimension on the chart to open its dashboard</p>
                </div>
                <div className="flex flex-wrap items-center gap-8">
                  <SpiderChart data={spiderData} size={280} color="#2563EB" onLabelClick={handleDimensionClick} />
                  <div className="flex-1 min-w-[200px]">
                    <div className="space-y-3">
                      {Object.entries(generalData.dimensions).map(([key, val]) => {
                        const d = val.distribution ?? { strong: 0, neutral: 0, weak: 0 };
                        return (
                          <button
                            key={key}
                            onClick={() => handleDimensionClick(key)}
                            className="flex w-full flex-col gap-1 rounded-lg p-2 transition-colors hover:bg-[var(--color-background)]"
                          >
                            <div className="flex w-full items-center justify-between">
                              <span className="capitalize text-sm font-medium text-[var(--color-text-secondary)]">{key}</span>
                              <div className="flex items-center gap-3">
                                <div className="h-2 w-32 rounded-full bg-[var(--color-border)] overflow-hidden">
                                  <div
                                    className="h-full bg-[var(--color-primary)] transition-all"
                                    style={{ width: `${Math.min(val.avg_score, 100)}%` }}
                                  />
                                </div>
                                <span className="text-sm font-bold text-[var(--color-text-primary)] w-12 text-right">
                                  {val.avg_score.toFixed(1)}
                                </span>
                              </div>
                            </div>
                            <div className="flex w-full items-center gap-2 pl-1 text-[10px] text-[var(--color-text-secondary)]">
                              <span title="range">range {val.min_score?.toFixed(0) ?? "—"}–{val.max_score?.toFixed(0) ?? "—"}</span>
                              <span title="standard deviation">±{(val.stdev ?? 0).toFixed(1)}</span>
                              <span className="ml-auto flex items-center gap-1">
                                <span className="rounded bg-[var(--color-success)]/15 text-[var(--color-success)] px-1.5 py-0.5">{d.strong} strong</span>
                                <span className="rounded bg-[var(--color-warning)]/15 text-[var(--color-warning)] px-1.5 py-0.5">{d.neutral} neutral</span>
                                <span className="rounded bg-[var(--color-error)]/15 text-[var(--color-error)] px-1.5 py-0.5">{d.weak} weak</span>
                              </span>
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                </div>
              </div>
            )}

            <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
              <div className="mb-4 flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-semibold text-[var(--color-text-primary)]">30-Day Trend</h2>
                  {scoreTrend?.latest_date && (
                    <p className="text-[10px] text-[var(--color-text-secondary)] mt-1">
                      Latest data: {new Date(scoreTrend.latest_date).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric"})}
                    </p>
                  )}
                  <p className="text-xs text-[var(--color-text-secondary)]">
                    Daily averages across {scoreTrend?.series?.[0]?.symbol_count?.toLocaleString("en-US") ?? "—"} NASDAQ symbols
                    {scoreTrend?.market ? ` (${scoreTrend.market})` : ""}
                  </p>
                </div>
                {scoreTrend && (
                  <span className="text-xs text-[var(--color-text-secondary)]">
                    {scoreTrend.count} data points
                  </span>
                )}
              </div>
              {scoreTrendLoading ? (
                <div className="flex items-center justify-center py-12">
                  <div className="h-8 w-8 animate-spin rounded-full border-4 border-[var(--color-primary)] border-t-transparent" />
                </div>
              ) : scoreTrend && scoreTrend.series.length > 0 ? (
                <div className="space-y-4">
                  <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] p-4">
                    <div className="mb-2">
                      <h3 className="text-sm font-semibold text-[var(--color-text-primary)]">Overall Market Score Trend</h3>
                      <p className="text-[11px] text-[var(--color-text-secondary)]">Average overall score (0–100)</p>
                    </div>
                    <ScoreTrendChart
                      showLegend
                      series={[{
                        key: "avg_score",
                        label: "Overall Score",
                        color: "#2563EB",
                        data: scoreTrend.series.map((p) => ({ time: p.date, value: p.avg_score })),
                      }]}
                      height={220}
                    />
                  </div>

                  <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] p-4">
                    <div className="mb-2">
                      <h3 className="text-sm font-semibold text-[var(--color-text-primary)]">Scores for All 6 Dimensions</h3>
                      <p className="text-[11px] text-[var(--color-text-secondary)]">
                        Click a chip below to toggle a dimension on or off
                      </p>
                    </div>
                    <ScoreTrendChart
                      showLegend
                      series={(scoreTrend.dimensions ?? Object.keys(scoreTrend.series[0]?.avg_dimensions ?? {}))
                        .map((dim, i) => ({
                          key: dim,
                          label: DIMENSION_LABELS[dim] ?? dim,
                          color: DIMENSION_COLORS[i % DIMENSION_COLORS.length],
                          data: scoreTrend.series.map((p) => ({
                            time: p.date,
                            value: p.avg_dimensions?.[dim] ?? 0,
                          })),
                        }))}
                      height={240}
                    />
                  </div>

                  <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] p-4">
                    <div className="mb-2">
                      <h3 className="text-sm font-semibold text-[var(--color-text-primary)]">Score Changes for All 6 Dimensions</h3>
                      <p className="text-[11px] text-[var(--color-text-secondary)]">
                        Day-over-day delta per dimension — toggle chips to filter
                      </p>
                    </div>
                    <ScoreTrendChart
                      showLegend
                      series={(scoreTrend.dimensions ?? Object.keys(scoreTrend.series[0]?.dimension_changes ?? {}))
                        .map((dim, i) => ({
                          key: dim,
                          label: `${DIMENSION_LABELS[dim] ?? dim} Δ`,
                          color: DIMENSION_COLORS[i % DIMENSION_COLORS.length],
                          data: scoreTrend.series.map((p) => ({
                            time: p.date,
                            value: p.dimension_changes?.[dim] ?? 0,
                          })),
                        }))}
                      height={240}
                    />
                  </div>
                </div>
              ) : (
                <p className="text-center text-[var(--color-text-secondary)] py-8">No trend data available</p>
              )}
            </div>

            {generalData?.coefficients && generalData.coefficients.length > 0 && (
              <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
                <div className="mb-4">
                  <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">Dimension Coefficients</h2>
                  <p className="text-xs text-[var(--color-text-secondary)]">
                    Static weights used to compute the overall score. Click any chip below to filter the bar chart.
                  </p>
                </div>
                <CoefficientFilterableChart
                  coefficients={generalData.coefficients}
                  filter={coefficientFilter}
                  onFilterChange={setCoefficientFilter}
                />
              </div>
            )}

            <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
              <button
                type="button"
                onClick={() => setSubLevelChartsOpen((prev) => !prev)}
                aria-expanded={subLevelChartsOpen}
                className="flex w-full items-center justify-between text-left"
              >
                <div>
                  <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">
                    Sub-Level Score Trends
                    <span className="ml-2 text-[10px] font-normal text-[var(--color-text-secondary)]">
                      {subLevelChartsOpen ? "Click to collapse" : "Click to expand"}
                    </span>
                  </h2>
                  <p className="text-xs text-[var(--color-text-secondary)]">
                    30-day trend + daily delta for sub-dimensions, aspects, and sub-aspects. Anchored to the same date as the 6D spider chart above.
                  </p>
                </div>
                <span className="text-xl text-[var(--color-text-secondary)]">{subLevelChartsOpen ? "−" : "+"}</span>
              </button>
              {subLevelChartsOpen && (
                <div className="mt-4 space-y-4">
                  <LevelTrendSection
                    title="Sub-Dimension Score Trend"
                    description="Mean across all NASDAQ symbols per taxonomy key (valuation, momentum, gdp, …)"
                    response={subDimensionTrend}
                  />
                  <LevelTrendSection
                    title="Aspect Score Trend"
                    description="Mean across all NASDAQ symbols per aspect key"
                    response={aspectTrend}
                  />
                  <LevelTrendSection
                    title="Sub-Aspect Score Trend"
                    description="Mean across all NASDAQ symbols per sub-aspect key"
                    response={subAspectTrend}
                  />
                </div>
              )}
            </div>

            {coefficientHistory && coefficientHistory.series.length > 0 && (
              <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
                <div className="mb-4">
                  <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">Coefficient History (30-Day)</h2>
                  <p className="text-xs text-[var(--color-text-secondary)]">
                    Daily dimension weight snapshots with delta column chart.
                  </p>
                </div>
                <ScoreTrendChart
                  showLegend
                  series={coefficientHistory.dimensions.map((dim, i) => ({
                    key: dim,
                    label: DIMENSION_LABELS[dim] ?? dim,
                    color: DIMENSION_COLORS[i % DIMENSION_COLORS.length],
                    data: coefficientHistory.series.map((p) => ({
                      time: p.date,
                      value: p.dimensions?.[dim] ?? 0,
                    })),
                  }))}
                  height={240}
                />
                <div className="mt-4">
                  <h3 className="text-sm font-semibold text-[var(--color-text-primary)]">Coefficient Weight Changes (Daily Delta)</h3>
                  <ColumnChart
                    data={coefficientHistory.series.map((p) => ({
                      time: p.date,
                      value: Object.values(p.dimension_changes ?? {}).reduce((sum, v) => sum + v, 0),
                      color: (Object.values(p.dimension_changes ?? {}).reduce((sum, v) => sum + v, 0)) >= 0 ? "#10b981" : "#ef4444",
                    }))}
                    height={200}
                  />
                </div>
              </div>
            )}

            <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">Top NASDAQ Stocks</h2>
                <Link href="/stocks" className="text-sm font-medium text-[var(--color-primary)] hover:underline">
                  View All
                </Link>
              </div>
              <div className="space-y-2">
                {topStocks.length > 0 ? (
                  topStocks.map((stock, index) => (
                    <Link
                      key={`${stock.symbol}-${index}`}
                      href={`/stocks/${stock.symbol}`}
                      className="flex items-center gap-4 rounded-lg border border-transparent p-4 transition-all hover:border-[var(--color-border)] hover:bg-[var(--color-background)]"
                    >
                      <div className={cn(
                        "flex h-8 w-8 shrink-0 items-center justify-center rounded text-sm font-bold",
                        index === 0 ? "bg-[var(--color-warning)] text-white" :
                        index === 1 ? "bg-gray-400 text-white" :
                        index === 2 ? "bg-amber-700 text-white" :
                        "bg-gray-200 text-gray-600 dark:bg-gray-800 dark:text-gray-400"
                      )}>
                        {index + 1}
                      </div>
                      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded bg-[var(--color-primary)]/10 text-sm font-bold text-[var(--color-primary)]">
                        {stock.symbol.slice(0, 2)}
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-[var(--color-text-primary)]">{stock.symbol}</span>
                          <span className="truncate text-xs text-[var(--color-text-secondary)]">{stock.name}</span>
                        </div>
                      </div>
                      <div className="shrink-0 text-right">
                        <p className="font-semibold text-[var(--color-text-primary)]">
                          {stock.price > 0 ? `$${stock.price.toFixed(2)}` : "—"}
                        </p>
                        <p className={cn("text-xs", stock.changePct >= 0 ? "text-[var(--color-success)]" : "text-[var(--color-error)]")}>
                          {stock.changePct !== 0
                            ? `${stock.changePct >= 0 ? "+" : ""}${stock.changePct.toFixed(2)}%`
                            : `Score ${(stock as unknown as { overall_score?: number }).overall_score?.toFixed(1) ?? "—"}`}
                        </p>
                      </div>
                    </Link>
                  ))
                ) : (
                  <p className="text-center text-[var(--color-text-secondary)] py-8">No stock data available</p>
                )}
              </div>
            </div>

            <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-[var(--color-text-primary)] mb-4">Market News</h2>
              {news.length > 0 ? (
                <div className="space-y-3">
                  {news.slice(0, 5).map((item, i) => (
                    <div key={i} className="p-3 rounded-lg bg-[var(--color-background)]">
                      <p className="font-medium text-[var(--color-text-primary)] text-sm">{item.title}</p>
                      <div className="flex items-center gap-2 mt-1 text-xs text-[var(--color-text-secondary)]">
                        <span>{item.source}</span>
                        <span>•</span>
                        <span>{item.time}</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-center text-[var(--color-text-secondary)] py-8">No news available</p>
              )}
            </div>
          </div>
        );

      case "technical":
        return <DimensionDashboard dimension="technical" fetchFn={fetchTechnicalDashboard} color="#2563EB" activeSub={activeSub} onSubChange={handleSubChange} />;

      case "fundamental":
        return <DimensionDashboard dimension="fundamental" fetchFn={fetchFundamentalDashboard} color="#10B981" activeSub={activeSub} onSubChange={handleSubChange} />;

      case "news":
        return <NewsDashboard />;

      case "risk":
        return <DimensionDashboard dimension="risk" fetchFn={fetchRiskDashboard} color="#EF4444" activeSub={activeSub} onSubChange={handleSubChange} />;

      case "board":
        return <BoardDashboard />;

      case "ai":
        return <AiDashboard />;

      default:
        return null;
    }
  };

  return (
    <div className="space-y-6">
      <div className="sticky top-0 z-30 bg-background/80 backdrop-blur-xl border-b border-border">
        <div className="px-4 lg:px-6 pt-4 pb-2">
          <div className="mb-3">
            <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">Dashboards</h1>
            <p className="text-xs text-[var(--color-text-secondary)]">Select a dashboard below</p>
          </div>
          <div className="flex items-center gap-1 rounded-xl border border-[var(--color-border)] bg-[var(--color-background)] p-1">
            {tabs.map((tab) => {
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => handleTabChange(tab.id)}
                  className={cn(
                    "relative flex-1 rounded-lg px-3 py-2.5 text-center text-sm font-medium transition-all",
                    isActive
                      ? "bg-[var(--color-primary)] text-white shadow-sm"
                      : "text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-border)]"
                  )}
                >
                  {tab.label}
                </button>
              );
            })}
          </div>
          <p className="mt-2 text-[10px] text-[var(--color-text-secondary)]">
            Shortcuts: G T F N R B A
          </p>
        </div>
      </div>

      {renderTabContent()}
    </div>
  );
}
