"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { cn } from "@/lib/cn";
import { NewDashboardShell } from "@/components/layout/NewDashboardShell";
import { PageLoading } from "@/components/ui/PageLoading";
import { TarotCard } from "@/components/ui/TarotCard";
import { SpiderChart } from "@/components/charts/SpiderChart";
import { ScoreTrendChart } from "@/components/charts/ScoreTrendChart";
import { ColumnChart } from "@/components/charts/ColumnChart";
import { BarChart } from "@/components/charts/BarChart";
import { DonutChart } from "@/components/charts/DonutChart";
import { AsOfStamp } from "@/components/scoring/AsOfStamp";
import { ScoreTripleBadge } from "@/components/scoring/ScoreTripleBadge";
import {
  fetchCoefficientHistory,
  fetchCoefficientHistoryByLevel,
  fetchSubDimensionTrend,
  fetchAspectTrend,
  fetchSubAspectTrend,
  type CoefficientHistoryResponse,
  type CoefficientHistoryByLevelResponse,
  type LevelTrendResponse,
  type WeightSnapshot,
} from "@/lib/api/dashboard";
import {
  useSnapshot,
  useSnapshotId,
  useSnapshotTimestamp,
  useSnapshotLoading,
  useSnapshotIndex,
  useLoadSnapshot,
  useLoadSnapshotIndex,
  useSelectSnapshotById,
} from "@/store/useDateStore";

type Level = 1 | 2 | 3 | 4;
type Tab = "general" | "fundamental" | "technical" | "sentiment" | "risk" | "macro" | "ai";

const V2_HIERARCHY: Record<string, string> = {
  valuation: "fundamental", profitability: "fundamental", growth: "fundamental", liquidity: "fundamental",
  trend: "technical", momentum: "technical", volatility: "technical", volume: "technical",
  news: "sentiment",
  market_risk: "risk",
  rates: "macro", commodity: "macro",
  ml_signal: "ai",
};

const V2_ASPECT_TO_SUBDIM: Record<string, string> = {
  pe_band: "valuation", roe_block: "profitability", growth_block: "growth", liquidity_block: "liquidity",
  trend_block: "trend", momentum_block: "momentum", volatility_block: "volatility", volume_block: "volume",
  news_block: "news", risk_block: "market_risk", rates_block: "rates", commodity_block: "commodity",
  ml_block: "ml_signal",
};

const V2_SUBASPECT_TO_ASPECT: Record<string, string> = {
  pe_ratio: "pe_band", pb_ratio: "pe_band", ev_ebitda: "pe_band",
  roe: "roe_block", roa: "roe_block", profit_margin: "roe_block",
  revenue_growth: "growth_block", eps_growth: "growth_block",
  current_ratio: "liquidity_block", quick_ratio: "liquidity_block",
  macd_histogram: "trend_block", bb_width: "trend_block",
  rsi_14: "momentum_block",
  realized_vol_30d: "volatility_block", atr_value: "volatility_block",
  volume_ratio: "volume_block",
  news_sentiment_avg: "news_block", news_volume: "news_block",
  volatility_z: "risk_block", max_drawdown: "risk_block",
  treasury_yield_10y: "rates_block", dollar_index: "rates_block",
  oil_price: "commodity_block", gold_price: "commodity_block",
  expected_return: "ml_block", confidence: "ml_block",
};

interface DrillState {
  level: Level;
  selectedKey: string | null;
  selectedLabel: string | null;
}

const LEVEL_LABELS: Record<Level, string> = {
  1: "Dimensions",
  2: "Sub-Dimensions",
  3: "Aspects",
  4: "Sub-Aspects",
};

const PALETTE = [
  "#2563EB",
  "#10B981",
  "#F59E0B",
  "#EF4444",
  "#8B5CF6",
  "#EC4899",
  "#06B6D4",
  "#F97316",
];

const TABS: { id: Tab; label: string; marker: string }[] = [
  { id: "general", label: "General", marker: "G" },
  { id: "fundamental", label: "Fundamental", marker: "F" },
  { id: "technical", label: "Technical", marker: "T" },
  { id: "sentiment", label: "Sentiment", marker: "S" },
  { id: "risk", label: "Risk", marker: "R" },
  { id: "macro", label: "Macro", marker: "M" },
  { id: "ai", label: "AI", marker: "A" },
];

function getParentKey(key: string, level: Level): string | null {
  if (level === 1) return null;
  if (level === 2) {
    return V2_HIERARCHY[key] || null;
  }
  if (level === 3) {
    return V2_ASPECT_TO_SUBDIM[key] || null;
  }
  if (level === 4) {
    return V2_SUBASPECT_TO_ASPECT[key] || null;
  }
  return null;
}

function getLabel(key: string): string {
  const parts = key.split("_");
  return parts.map((p) => p.charAt(0).toUpperCase() + p.slice(1)).join(" ");
}

export default function DashboardPage() {
  const searchParams = useSearchParams();
  const initialTab = (searchParams.get("tab") as Tab) || "general";
  const [activeTab, setActiveTab] = useState<Tab>(TABS.find((t) => t.id === initialTab) ? initialTab : "general");
  const [selectedSymbol, setSelectedSymbol] = useState<string>("");
  const [symbolInput, setSymbolInput] = useState<string>("");

  const snapshot = useSnapshot();
  const snapshotId = useSnapshotId();
  const snapshotTimestamp = useSnapshotTimestamp();
  const snapshotLoading = useSnapshotLoading();
  const snapshotIndex = useSnapshotIndex();
  const loadSnapshot = useLoadSnapshot();
  const loadSnapshotIndex = useLoadSnapshotIndex();
  const selectSnapshotById = useSelectSnapshotById();

  const [drill, setDrill] = useState<DrillState>({ level: 1, selectedKey: null, selectedLabel: null });

  const [subDimTrend, setSubDimTrend] = useState<LevelTrendResponse | null>(null);
  const [aspectTrend, setAspectTrend] = useState<LevelTrendResponse | null>(null);
  const [subAspectTrend, setSubAspectTrend] = useState<LevelTrendResponse | null>(null);
  const [subDimCoeffHistory, setSubDimCoeffHistory] = useState<CoefficientHistoryByLevelResponse | null>(null);
  const [aspectCoeffHistory, setAspectCoeffHistory] = useState<CoefficientHistoryByLevelResponse | null>(null);
  const [subAspectCoeffHistory, setSubAspectCoeffHistory] = useState<CoefficientHistoryByLevelResponse | null>(null);
  const [coeffHistory, setCoeffHistory] = useState<CoefficientHistoryResponse | null>(null);

  useEffect(() => {
    loadSnapshotIndex({ hourly_limit: 168, daily_limit: 90 });
  }, [loadSnapshotIndex]);

  useEffect(() => {
    async function load() {
      await loadSnapshot({
        window_daily: 30,
        window_intraday: "24h",
        symbol: selectedSymbol || undefined,
      });
    }
    load();
  }, [loadSnapshot, activeTab, selectedSymbol]);

  useEffect(() => {
    if (!snapshot) return;
    let active = true;
    async function load() {
      const latestDate = snapshotTimestamp ? new Date(snapshotTimestamp).toISOString().split("T")[0] : null;
      const baseOptions = latestDate ? { endDate: latestDate } : { latest: true };

      const [subDim, asp, subAsp, subDimCoeff, aspCoeff, subAspCoeff, coeff] = await Promise.allSettled([
        fetchSubDimensionTrend(30, "NASDAQ", baseOptions),
        fetchAspectTrend(30, "NASDAQ", baseOptions),
        fetchSubAspectTrend(30, "NASDAQ", baseOptions),
        fetchCoefficientHistoryByLevel("sub_dimension", 30, "NASDAQ", drill.level >= 2 ? { ...baseOptions, parent: drill.selectedKey || undefined } : baseOptions),
        fetchCoefficientHistoryByLevel("aspect", 30, "NASDAQ", drill.level >= 3 ? { ...baseOptions, parent: drill.selectedKey || undefined } : baseOptions),
        fetchCoefficientHistoryByLevel("sub_aspect", 30, "NASDAQ", drill.level >= 4 ? { ...baseOptions, parent: drill.selectedKey || undefined } : baseOptions),
        fetchCoefficientHistory(30, "NASDAQ", baseOptions),
      ]);

      if (!active) return;
      if (subDim.status === "fulfilled") setSubDimTrend(subDim.value);
      if (asp.status === "fulfilled") setAspectTrend(asp.value);
      if (subAsp.status === "fulfilled") setSubAspectTrend(subAsp.value);
      if (subDimCoeff.status === "fulfilled") setSubDimCoeffHistory(subDimCoeff.value);
      if (aspCoeff.status === "fulfilled") setAspectCoeffHistory(aspCoeff.value);
      if (subAspCoeff.status === "fulfilled") setSubAspectCoeffHistory(subAspCoeff.value);
      if (coeff.status === "fulfilled") setCoeffHistory(coeff.value);
    }
    load();
    return () => { active = false; };
  }, [snapshot, drill.level, drill.selectedKey]);

  const mergedSnapshotIndex = useMemo(() => {
    if (!snapshotIndex) return [];
    const hourly = Array.isArray(snapshotIndex.hourly) ? snapshotIndex.hourly : [];
    const daily = Array.isArray(snapshotIndex.daily) ? snapshotIndex.daily : [];
    const all = [...hourly, ...daily].filter(
      (e) => e && typeof e.effectiveAt === "string" && typeof e.snapshotId === "string"
    );
    all.sort((a, b) => new Date(b.effectiveAt).getTime() - new Date(a.effectiveAt).getTime());
    return all;
  }, [snapshotIndex]);

  const [sliderIndex, setSliderIndex] = useState(0);

  useEffect(() => {
    if (!mergedSnapshotIndex || mergedSnapshotIndex.length === 0) return;
    if (sliderIndex >= 0 && sliderIndex < mergedSnapshotIndex.length) {
      const entry = mergedSnapshotIndex[sliderIndex];
      if (entry.snapshotId && entry.snapshotId !== snapshotId) {
        selectSnapshotById(entry.snapshotId);
      }
    }
  }, [sliderIndex, mergedSnapshotIndex, snapshotId, selectSnapshotById]);

  const hierarchyScores = useMemo(() => {
    if (!snapshot) return null;
    return snapshot.scores.daily;
  }, [snapshot]);

  const weights = useMemo<WeightSnapshot | null>(() => {
    if (!snapshot) return null;
    return snapshot.weights;
  }, [snapshot]);

  const itemsForLevel = useMemo(() => {
    if (!hierarchyScores) return [];
    if (drill.level === 1) {
      return Object.entries(hierarchyScores.dimension || {}).map(([key, value]) => ({
        key,
        label: getLabel(key),
        score: value,
      }));
    }
    if (drill.level === 2) {
      const parent = drill.selectedKey || "";
      return Object.entries(hierarchyScores.sub_dimension || {}).map(([key, value]) => {
        const keyParent = getParentKey(key, 2);
        if (keyParent !== parent && parent) return null;
        return {
          key,
          label: getLabel(key.replace(`${parent}_`, "").replace("_", " ")),
          score: value,
        };
      }).filter(Boolean) as { key: string; label: string; score: number }[];
    }
    if (drill.level === 3) {
      const parent = drill.selectedKey || "";
      return Object.entries(hierarchyScores.aspect || {}).map(([key, value]) => {
        const keyParent = getParentKey(key, 3);
        if (keyParent !== parent && parent) return null;
        return {
          key,
          label: getLabel(key.replace(`${parent}_`, "").replace("_aspect_", " Aspect ")),
          score: value,
        };
      }).filter(Boolean) as { key: string; label: string; score: number }[];
    }
    const parent = drill.selectedKey || "";
    return Object.entries(hierarchyScores.sub_aspect || {}).map(([key, value]) => {
      const keyParent = getParentKey(key, 4);
      if (keyParent !== parent && parent) return null;
      return {
        key,
        label: getLabel(key.replace(`${parent}_`, "").replace("_detail_", " Detail ")),
        score: value,
      };
    }).filter(Boolean) as { key: string; label: string; score: number }[];
  }, [hierarchyScores, drill.level, drill.selectedKey]);

  const spiderData = useMemo(() => itemsForLevel.map((i) => ({ label: i.label, value: i.score })), [itemsForLevel]);

  const level1TrendSeries = useMemo(() => {
    if (!snapshot || drill.level !== 1) return [];
    const dailyPoints = snapshot.trends.daily || [];
    const dims = Object.keys(hierarchyScores?.dimension || {});
    return dims.map((dim, i) => ({
      key: dim,
      label: getLabel(dim),
      color: PALETTE[i % PALETTE.length],
      data: dailyPoints.map((pt) => ({
        time: pt.date,
        value: (pt.level_scores && typeof pt.level_scores[dim] === 'number') ? pt.level_scores[dim] : (pt.overall ?? 0),
      })),
    }));
  }, [snapshot, drill.level, hierarchyScores]);

  const level1ChangeSeries = useMemo(() => {
    if (!snapshot || drill.level !== 1) return [];
    const dailyPoints = snapshot.trends.daily || [];
    const dims = Object.keys(hierarchyScores?.dimension || {});
    return dims.map((dim, i) => {
      const series = dailyPoints.map((pt, idx) => {
        const curr = (pt.level_scores && typeof pt.level_scores[dim] === 'number') ? pt.level_scores[dim] : (pt.overall ?? 0);
        const prev = idx > 0 ? ((dailyPoints[idx - 1].level_scores && typeof dailyPoints[idx - 1].level_scores[dim] === 'number') ? dailyPoints[idx - 1].level_scores[dim] : (dailyPoints[idx - 1].overall ?? 0)) : curr;
        return { time: pt.date, value: curr - prev };
      });
      return {
        key: dim,
        label: getLabel(dim),
        color: PALETTE[i % PALETTE.length],
        data: series,
      };
    });
  }, [snapshot, drill.level, hierarchyScores]);

  const trendSeriesForLevel = useMemo(() => {
    if (!hierarchyScores || !itemsForLevel.length) return [];
    if (drill.level === 1) return level1TrendSeries;
    const trendResponse = drill.level === 2 ? subDimTrend : drill.level === 3 ? aspectTrend : subAspectTrend;
    if (!trendResponse || trendResponse.series.length === 0) return [];
    const keys = trendResponse.keys.filter((k) => trendResponse.series.some((pt) => (pt.avg_scores[k] ?? 0) > 0));
    return keys.map((key, i) => ({
      key,
      label: getLabel(key),
      color: PALETTE[i % PALETTE.length],
      data: trendResponse.series.map((pt) => ({ time: pt.date, value: pt.avg_scores[key] ?? 0 })),
    }));
  }, [hierarchyScores, itemsForLevel, drill.level, level1TrendSeries, subDimTrend, aspectTrend, subAspectTrend]);

  const changeSeriesForLevel = useMemo(() => {
    if (!hierarchyScores || !itemsForLevel.length) return [];
    if (drill.level === 1) {
      return level1ChangeSeries.flatMap((series) => series.data.map((pt) => ({ ...pt, color: pt.value >= 0 ? "#10b981" : "#ef4444" })));
    }
    const trendResponse = drill.level === 2 ? subDimTrend : drill.level === 3 ? aspectTrend : subAspectTrend;
    if (!trendResponse || trendResponse.series.length === 0) return [];
    return trendResponse.series.map((pt) => {
      const total = Object.values(pt.score_changes ?? {}).reduce((sum, v) => sum + v, 0);
      return { time: pt.date, value: total, color: total >= 0 ? "#10b981" : "#ef4444" };
    });
  }, [hierarchyScores, itemsForLevel, drill.level, level1ChangeSeries, subDimTrend, aspectTrend, subAspectTrend]);

  const coeffSeriesForLevel = useMemo(() => {
    if (!hierarchyScores || drill.level === 1) return [];
    const coeffHistory = drill.level === 2 ? subDimCoeffHistory : drill.level === 3 ? aspectCoeffHistory : subAspectCoeffHistory;
    if (!coeffHistory || coeffHistory.series.length === 0) return [];
    const dims = coeffHistory.series[0]?.metrics ? Object.keys(coeffHistory.series[0].metrics) : [];
    return dims.map((dim, i) => ({
      key: dim,
      label: getLabel(dim),
      color: PALETTE[i % PALETTE.length],
      data: coeffHistory.series.map((p) => ({ time: p.date, value: p.metrics?.[dim] ?? 0 })),
    }));
  }, [hierarchyScores, drill.level, subDimCoeffHistory, aspectCoeffHistory, subAspectCoeffHistory]);

  const coeffChangeSeries = useMemo(() => {
    if (!hierarchyScores || drill.level === 1) return [];
    const coeffHistory = drill.level === 2 ? subDimCoeffHistory : drill.level === 3 ? aspectCoeffHistory : subAspectCoeffHistory;
    if (!coeffHistory || coeffHistory.series.length === 0) return [];
    return coeffHistory.series.map((p) => {
      const total = Object.values(p.metric_changes ?? {}).reduce((sum, v) => sum + v, 0);
      return { time: p.date, value: total, color: total >= 0 ? "#10b981" : "#ef4444" };
    });
  }, [hierarchyScores, drill.level, subDimCoeffHistory, aspectCoeffHistory, subAspectCoeffHistory]);

  const level1CoeffChangeSeries = useMemo(() => {
    if (!coeffHistory || drill.level !== 1) return [];
    return coeffHistory.series.map((pt) => {
      const total = Object.values(pt.dimension_changes ?? {}).reduce((sum, v) => sum + v, 0);
      return { time: pt.date, value: total, color: total >= 0 ? "#10b981" : "#ef4444" };
    });
  }, [coeffHistory, drill.level]);

  const donutDataForLevel = useMemo(() => {
    if (!weights) return [];
    if (drill.level === 1) {
      return Object.entries(weights.dimension || {}).map(([key, value], i) => ({
        label: getLabel(key),
        value,
        color: PALETTE[i % PALETTE.length],
      }));
    }
    if (drill.level === 2) {
      const parent = drill.selectedKey || "";
      const entries = Object.entries(weights.sub_dimension || {});
      const filtered = parent ? entries.filter(([k]) => getParentKey(k, 2) === parent) : entries;
      return filtered.map(([key, value], i) => ({
        label: getLabel(key.replace(`${parent}_`, "").replace("_", " ")),
        value,
        color: PALETTE[i % PALETTE.length],
      }));
    }
    if (drill.level === 3) {
      const parent = drill.selectedKey || "";
      const entries = Object.entries(weights.aspect || {});
      const filtered = parent ? entries.filter(([k]) => getParentKey(k, 3) === parent) : entries;
      return filtered.map(([key, value], i) => ({
        label: getLabel(key.replace(`${parent}_`, "").replace("_aspect_", " Aspect ")),
        value,
        color: PALETTE[i % PALETTE.length],
      }));
    }
    const parent = drill.selectedKey || "";
    const entries = Object.entries(weights.sub_aspect || {});
    const filtered = parent ? entries.filter(([k]) => getParentKey(k, 4) === parent) : entries;
    return filtered.map(([key, value], i) => ({
      label: getLabel(key.replace(`${parent}_`, "").replace("_detail_", " Detail ")),
      value,
      color: PALETTE[i % PALETTE.length],
    }));
  }, [weights, drill.level, drill.selectedKey]);

  const handleDrillDown = useCallback((item: { key: string; label: string }) => {
    setDrill({
      level: Math.min(drill.level + 1, 4) as Level,
      selectedKey: item.key,
      selectedLabel: item.label,
    });
  }, [drill.level]);

  const handleBreadcrumb = useCallback((level: Level) => {
    setDrill({
      level,
      selectedKey: level === 1 ? null : drill.selectedKey,
      selectedLabel: level === 1 ? null : drill.selectedLabel,
    });
  }, [drill.selectedKey, drill.selectedLabel]);

  const handleTabChange = (tab: Tab) => {
    setActiveTab(tab);
    setDrill({ level: 1, selectedKey: null, selectedLabel: null });
  };

  const handleSymbolSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const sym = symbolInput.trim().toUpperCase();
    if (sym) {
      setSelectedSymbol(sym);
      setDrill({ level: 1, selectedKey: null, selectedLabel: null });
    }
  };

  const handleClearSymbol = () => {
    setSelectedSymbol("");
    setSymbolInput("");
    setDrill({ level: 1, selectedKey: null, selectedLabel: null });
  };

  if (snapshotLoading) {
    return (
      <NewDashboardShell title="Dashboard">
        <PageLoading />
      </NewDashboardShell>
    );
  }

  return (
    <NewDashboardShell title="Hierarchical Dashboard">
      <div className="flex flex-col gap-6 animate-in fade-in duration-500">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="flex-1">
            <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">
              Hierarchical Market Dashboard
            </h1>
            <div className="mt-2">
              <AsOfStamp
                effectiveAt={snapshotTimestamp ?? null}
                snapshotId={snapshotId ?? null}
                loading={snapshotLoading}
                variant="emphasis"
              />
            </div>
          </div>
          <form onSubmit={handleSymbolSubmit} className="flex items-center gap-2">
            <input
              type="text"
              value={symbolInput}
              onChange={(e) => setSymbolInput(e.target.value)}
              placeholder="Symbol (e.g. AAPL)"
              className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] focus:border-[var(--color-primary)] focus:outline-none"
            />
            <button
              type="submit"
              className="rounded-xl border border-[var(--color-primary)] bg-[var(--color-primary)] px-4 py-2 text-sm font-semibold text-white"
            >
              Go
            </button>
            {selectedSymbol && (
              <button
                type="button"
                onClick={handleClearSymbol}
                className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]"
              >
                Clear
              </button>
            )}
          </form>
        </div>

        {snapshot && (
          <section className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
            <div className="mb-3 flex items-center justify-between">
              <div>
                <h2 className="text-base font-semibold text-[var(--color-text-primary)]">
                  THREE-FRAME SCORE REFERENCE
                </h2>
                <p className="mt-0.5 text-xs text-[var(--color-text-secondary)]">
                  PREV DAY (00:00 UTC) · PREV HOUR · CURRENT LIVE · source snapshot #{snapshotId?.slice(0, 8) ?? "—"}
                  {selectedSymbol && ` · Symbol: ${selectedSymbol}`}
                </p>
              </div>
            </div>
            <ScoreTripleBadge
              scores={snapshot.scores}
              deltas={snapshot.deltas}
              showDailyDelta
              size="md"
            />
          </section>
        )}

        <div className="flex gap-2 overflow-x-auto pb-2">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => handleTabChange(tab.id)}
              className={cn(
                "inline-flex items-center gap-2 rounded-xl border px-4 py-2.5 text-sm font-semibold transition-all whitespace-nowrap",
                activeTab === tab.id
                  ? "border-[var(--color-primary)] bg-[var(--color-primary)] text-white shadow-lg shadow-[var(--color-primary)]/20"
                  : "border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text-secondary)] hover:border-[var(--color-primary)]/30 hover:text-[var(--color-text-primary)]"
              )}
            >
              <span>{tab.marker}</span>
              {tab.label}
            </button>
          ))}
        </div>

        {mergedSnapshotIndex && mergedSnapshotIndex.length > 0 && (
          <TarotCard title="[SR] SNAPSHOT REPLAY — Drag to travel in time">
            <div className="flex flex-col gap-3">
              <div className="flex items-center justify-between gap-3 text-xs">
                <span className="font-mono text-muted-foreground">
                  EARLIEST · {mergedSnapshotIndex[mergedSnapshotIndex.length - 1]?.effectiveAt?.slice(0, 16)?.replace("T", " ") ?? "—"}
                </span>
                <span className="font-semibold text-[var(--color-primary)]">
                  {mergedSnapshotIndex[sliderIndex]?.effectiveAt?.slice(0, 16)?.replace("T", " ") ?? "NOW"}
                </span>
                <span className="font-mono text-muted-foreground">
                  LATEST · {mergedSnapshotIndex[0]?.effectiveAt?.slice(0, 16)?.replace("T", " ") ?? "—"}
                </span>
              </div>
              <input
                type="range"
                min={0}
                max={mergedSnapshotIndex.length - 1}
                value={sliderIndex}
                onChange={(e) => setSliderIndex(parseInt(e.target.value, 10))}
                aria-label="Snapshot time travel slider"
                className="w-full h-2 bg-[var(--color-neutral)] rounded-full appearance-none cursor-pointer accent-[var(--color-primary)]"
              />
            </div>
          </TarotCard>
        )}

        {drill.level > 1 && (
          <div className="flex items-center gap-2 text-sm">
            <button
              type="button"
              onClick={() => handleBreadcrumb(1)}
              className={cn(
                "rounded-full px-3 py-1 transition",
                drill.level === 1
                  ? "bg-primary/10 font-semibold text-primary"
                  : "text-muted-foreground hover:bg-neutral"
              )}
            >
              {LEVEL_LABELS[1]}
            </button>
            {drill.level >= 2 && drill.selectedLabel && (
              <>
                <span className="text-muted-foreground">/</span>
                <button
                  type="button"
                  onClick={() => handleBreadcrumb(2)}
                  className={cn(
                    "rounded-full px-3 py-1 transition",
                    drill.level === 2
                      ? "bg-primary/10 font-semibold text-primary"
                      : "text-muted-foreground hover:bg-neutral"
                  )}
                >
                  {drill.selectedLabel}
                </button>
              </>
            )}
            {drill.level >= 3 && drill.selectedLabel && (
              <>
                <span className="text-muted-foreground">/</span>
                <button
                  type="button"
                  onClick={() => handleBreadcrumb(3)}
                  className={cn(
                    "rounded-full px-3 py-1 transition",
                    drill.level === 3
                      ? "bg-primary/10 font-semibold text-primary"
                      : "text-muted-foreground hover:bg-neutral"
                  )}
                >
                  {drill.selectedLabel}
                </button>
              </>
            )}
            {drill.level >= 4 && drill.selectedLabel && (
              <>
                <span className="text-muted-foreground">/</span>
                <span className="text-foreground">{drill.selectedLabel}</span>
              </>
            )}
          </div>
        )}

        {spiderData.length > 0 && (
          <TarotCard title={`${LEVEL_LABELS[drill.level]} — Spider Chart (Radar)`}>
            <div className="flex justify-center">
              <SpiderChart
                data={spiderData}
                size={360}
                color={PALETTE[0]}
                onLabelClick={drill.level < 4 ? (label) => {
                  const item = itemsForLevel.find((i) => i.label === label);
                  if (item) handleDrillDown(item);
                } : undefined}
              />
            </div>
          </TarotCard>
        )}

        {trendSeriesForLevel.length > 0 && (
          <TarotCard title={`${LEVEL_LABELS[drill.level]} — Score Trend (30-Day)`}>
            <ScoreTrendChart showLegend series={trendSeriesForLevel} height={280} />
          </TarotCard>
        )}

        {changeSeriesForLevel.length > 0 && (
          <TarotCard title={`${LEVEL_LABELS[drill.level]} — Score Changes (Daily Delta)`}>
            {drill.level === 1 ? (
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
                {level1ChangeSeries.map((series) => (
                  <div key={series.key} className="rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] p-3">
                    <div className="mb-1 flex items-center gap-2">
                      <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: series.color }} />
                      <span className="text-xs font-medium text-[var(--color-text-secondary)]">{series.label}</span>
                    </div>
                    <ColumnChart data={series.data} height={120} valueFormatter={(v) => (v >= 0 ? "+" : "") + v.toFixed(2)} />
                  </div>
                ))}
              </div>
            ) : (
              <ColumnChart
                data={changeSeriesForLevel}
                height={220}
                valueFormatter={(v) => (v >= 0 ? "+" : "") + v.toFixed(2)}
              />
            )}
          </TarotCard>
        )}

        {donutDataForLevel.length > 0 && (
          <TarotCard title={`${LEVEL_LABELS[drill.level]} — Weights (Donut)`}>
            <div className="flex justify-center">
              <DonutChart data={donutDataForLevel} size={280} thickness={50} />
            </div>
          </TarotCard>
        )}

        {coeffSeriesForLevel.length > 0 && (
          <TarotCard title={`${LEVEL_LABELS[drill.level]} — Coefficient Trend (30-Day)`}>
            <ScoreTrendChart showLegend series={coeffSeriesForLevel} height={260} />
          </TarotCard>
        )}

        {(drill.level === 1 ? coeffChangeSeries.length > 0 || level1CoeffChangeSeries.length > 0 : coeffChangeSeries.length > 0) && (
          <TarotCard title={`${LEVEL_LABELS[drill.level]} — Coefficient Changes (Daily Delta)`}>
            {drill.level === 1 && coeffHistory ? (
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div>
                  <h4 className="text-sm font-semibold mb-2 text-[var(--color-text-secondary)]">Column View</h4>
                  <ColumnChart
                    data={level1CoeffChangeSeries}
                    height={200}
                    valueFormatter={(v) => (v >= 0 ? "+" : "") + v.toFixed(4)}
                  />
                </div>
                <div>
                  <h4 className="text-sm font-semibold mb-2 text-[var(--color-text-secondary)]">Horizontal Bar View</h4>
                  <BarChart
                    data={level1CoeffChangeSeries}
                    height={200}
                  />
                </div>
              </div>
            ) : (
              <ColumnChart
                data={coeffChangeSeries}
                height={200}
                valueFormatter={(v) => (v >= 0 ? "+" : "") + v.toFixed(4)}
              />
            )}
          </TarotCard>
        )}

        {itemsForLevel.length > 0 && (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {itemsForLevel.map((item) => (
              <TarotCard
                key={item.key}
                className="cursor-pointer transition hover:border-[var(--color-primary)]/30"
                onClick={() => handleDrillDown(item)}
                aria-label={`Drill down into ${item.label}`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-xs text-muted-foreground uppercase">{item.label}</div>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="font-bold text-lg">{item.score?.toFixed(1)}</span>
                      <div className="h-1.5 flex-1 mx-2 bg-border rounded-full overflow-hidden">
                        <div
                          className={cn(
                            "h-full rounded-full",
                            (item.score ?? 0) >= 70 ? "bg-green-600" : (item.score ?? 0) >= 40 ? "bg-yellow-500" : "bg-red-600"
                          )}
                          style={{ width: `${Math.max(0, Math.min(100, item.score ?? 0))}%` }}
                        />
                      </div>
                    </div>
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {drill.level < 4 ? "Click to drill →" : "Lowest level"}
                  </div>
                </div>
              </TarotCard>
            ))}
          </div>
        )}
      </div>
    </NewDashboardShell>
  );
}
