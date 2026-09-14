"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  fetchHierarchyScores,
  fetchScoreHistory,
  fetchCoefficients,
  type HierarchyScores,
  type ScoreHistoryPoint,
  type CoefficientItem,
} from "@/lib/api/scoring";
import {
  fetchSubDimensionTrend,
  fetchAspectTrend,
  fetchSubAspectTrend,
  fetchCoefficientHistoryByLevel,
  type LevelTrendResponse,
  type LevelTrendPoint,
  type CoefficientHistoryByLevelResponse,
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
  type SnapshotResponse,
  type SnapshotIndexEntry,
} from "@/store/useDateStore";
import {
  flexHierarchyToLegacy,
  flexWeightsToLegacy,
  type FlexHierarchyScores,
  type FlexTrendPoint,
  type FlexWeights,
} from "@/lib/scoring-adapters";
import { num } from "@/lib/utils";

export type Level = 1 | 2 | 3 | 4;
export type ScoringTab = "HISTORICAL" | "INTRADAY";
export type ViewMode = "SIMPLE" | "EXPERT";
export type IntradayWindow = "6h" | "24h" | "7d";
export type DailyWindow = 30 | 90 | 365;

export interface DrillState {
  level: Level;
  selectedKey: string | null;
  selectedLabel: string | null;
}

export const LEVEL_LABELS: Record<Level, string> = {
  1: "Dimensions",
  2: "Sub-Dimensions",
  3: "Aspects",
  4: "Sub-Aspects",
};

export const PALETTE = [
  "#2563EB",
  "#10B981",
  "#F59E0B",
  "#EF4444",
  "#8B5CF6",
  "#EC4899",
  "#06B6D4",
  "#F97316",
];

export const DAILY_WINDOW_OPTIONS: DailyWindow[] = [30, 90, 365];
export const INTRADAY_WINDOW_OPTIONS: IntradayWindow[] = ["6h", "24h", "7d"];

function snapshotHierarchyToLegacy(snap: SnapshotResponse, tab: ScoringTab): HierarchyScores | null {
  const scores = tab === "HISTORICAL" ? snap.scores.daily : snap.scores.current;
  if (!scores) return null;
  const legacy = flexHierarchyToLegacy(scores as FlexHierarchyScores, snap.timestamp);
  return legacy as HierarchyScores;
}

function snapshotTrendsToLegacy(snap: SnapshotResponse, tab: ScoringTab): ScoreHistoryPoint[] {
  const series = (tab === "HISTORICAL" ? snap.trends?.daily ?? [] : snap.trends?.intraday ?? []) as unknown as FlexTrendPoint[];
  return series.map((pt) => {
    const levelScores = pt.level_scores ?? pt.scores ?? {};
    const dimScores: Record<string, number> = {};
    const subDimScores: Record<string, number> = {};
    const aspectScores: Record<string, number> = {};
    const subAspectScores: Record<string, number> = {};
    Object.entries(levelScores).forEach(([k, v]) => {
      const val = typeof v === "number" ? v : num(v);
      if (k.startsWith("L1_") || k.startsWith("dim_") || !/^(L2|L3|L4|sd_|asp|sa_)/.test(k)) dimScores[k] = val;
      if (k.startsWith("L2_") || k.startsWith("sd_")) subDimScores[k] = val;
      if (k.startsWith("L3_") || k.startsWith("asp_") || /^aspect_/.test(k)) aspectScores[k] = val;
      if (k.startsWith("L4_") || k.startsWith("sa_") || /^sub_aspect_/.test(k)) subAspectScores[k] = val;
    });
    const rawPt = series.find(
      (r) => (r.date ?? r.effective_at ?? r.time) === (pt.date ?? pt.effective_at)
    ) ?? {};
    return {
      date: pt.date ?? pt.effective_at,
      overall: num(pt.overall ?? 0),
      dimension_scores: (rawPt.dimension_scores as Record<string, number>) ?? (Object.keys(dimScores).length > 0 ? dimScores : {}),
      sub_dimension_scores: (rawPt.sub_dimension_scores as Record<string, number>) ?? subDimScores,
      aspect_scores: (rawPt.aspect_scores as Record<string, number>) ?? aspectScores,
      sub_aspect_scores: (rawPt.sub_aspect_scores as Record<string, number>) ?? subAspectScores,
    } as ScoreHistoryPoint;
  });
}

function snapshotWeightsToLegacy(snap: SnapshotResponse): CoefficientItem[] {
  const weights = snap.weights;
  if (!weights) return [];
  return flexWeightsToLegacy(weights as FlexWeights) as CoefficientItem[];
}

export function useScoringData(symbol: string) {
  const snapshot = useSnapshot();
  const snapshotId = useSnapshotId();
  const snapshotTimestamp = useSnapshotTimestamp();
  const snapshotLoading = useSnapshotLoading();
  const snapshotIndex = useSnapshotIndex();
  const loadSnapshot = useLoadSnapshot();
  const loadSnapshotIndex = useLoadSnapshotIndex();
  const selectSnapshotById = useSelectSnapshotById();

  const [hierarchy, setHierarchy] = useState<HierarchyScores | null>(null);
  const [history, setHistory] = useState<ScoreHistoryPoint[] | null>(null);
  const [coefficients, setCoefficients] = useState<CoefficientItem[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [drill, setDrill] = useState<DrillState>({ level: 1, selectedKey: null, selectedLabel: null });

  const [scoringTab, setScoringTab] = useState<ScoringTab>("HISTORICAL");
  const [viewMode, setViewMode] = useState<ViewMode>("SIMPLE");
  const [windowDaily, setWindowDaily] = useState<DailyWindow>(30);
  const [windowIntraday, setWindowIntraday] = useState<IntradayWindow>("24h");
  const [sliderIndex, setSliderIndex] = useState(0);

  const [subDimTrend, setSubDimTrend] = useState<LevelTrendResponse | null>(null);
  const [aspectTrend, setAspectTrend] = useState<LevelTrendResponse | null>(null);
  const [subAspectTrend, setSubAspectTrend] = useState<LevelTrendResponse | null>(null);
  const [subDimCoeffHistory, setSubDimCoeffHistory] = useState<CoefficientHistoryByLevelResponse | null>(null);
  const [aspectCoeffHistory, setAspectCoeffHistory] = useState<CoefficientHistoryByLevelResponse | null>(null);
  const [subAspectCoeffHistory, setSubAspectCoeffHistory] = useState<CoefficientHistoryByLevelResponse | null>(null);

  useEffect(() => {
    if (!symbol) return;
    loadSnapshotIndex({ hourly_limit: 168, daily_limit: 90 });
  }, [symbol, loadSnapshotIndex]);

  useEffect(() => {
    if (!symbol) return;
    let active = true;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const winDaily = windowDaily;
        const winIntra = windowIntraday;
        const snapPromise = loadSnapshot({ symbol, window_daily: winDaily, window_intraday: winIntra });
        const legacyPromise = Promise.all([
          fetchHierarchyScores(symbol),
          fetchScoreHistory(symbol, winDaily),
          fetchCoefficients(symbol),
        ]);

        const [snap, legacy] = await Promise.all([snapPromise, legacyPromise]);

        if (!active) return;

        if (snap) {
          const derivedHierarchy = snapshotHierarchyToLegacy(snap, scoringTab);
          const derivedHistory = snapshotTrendsToLegacy(snap, scoringTab);
          const derivedCoeff = snapshotWeightsToLegacy(snap);
          setHierarchy(derivedHierarchy ?? legacy[0]);
          setHistory(derivedHistory.length > 0 ? derivedHistory : legacy[1]);
          setCoefficients(derivedCoeff.length > 0 ? derivedCoeff : legacy[2]);
        } else {
          const [h, hist, coeff] = legacy;
          setHierarchy(h);
          setHistory(hist);
          setCoefficients(coeff);
        }
      } catch (e: unknown) {
        if (active) setError(e instanceof Error ? e.message : "Failed to load scoring data");
      } finally {
        if (active) setLoading(false);
      }
    }

    load();
    return () => { active = false; };
  }, [symbol, windowDaily, windowIntraday, loadSnapshot, scoringTab]);

  useEffect(() => {
    if (!hierarchy) return;
    const hierarchyData = hierarchy;
    let active = true;

    async function load() {
      const latestDate = hierarchyData.timestamp ? new Date(hierarchyData.timestamp).toISOString().split("T")[0] : null;
      const baseOptions = latestDate ? { endDate: latestDate } : { latest: true };

      const [subDim, asp, subAsp, subDimCoeff, aspCoeff, subAspCoeff] = await Promise.allSettled([
        fetchSubDimensionTrend(windowDaily, "NASDAQ", baseOptions),
        fetchAspectTrend(windowDaily, "NASDAQ", baseOptions),
        fetchSubAspectTrend(windowDaily, "NASDAQ", baseOptions),
        fetchCoefficientHistoryByLevel("sub_dimension", windowDaily, "NASDAQ", drill.level >= 2 ? { ...baseOptions, parent: drill.selectedKey || undefined } : baseOptions),
        fetchCoefficientHistoryByLevel("aspect", windowDaily, "NASDAQ", drill.level >= 3 ? { ...baseOptions, parent: drill.selectedKey || undefined } : baseOptions),
        fetchCoefficientHistoryByLevel("sub_aspect", windowDaily, "NASDAQ", drill.level >= 4 ? { ...baseOptions, parent: drill.selectedKey || undefined } : baseOptions),
      ]);

      if (!active) return;
      if (subDim.status === "fulfilled") setSubDimTrend(subDim.value);
      if (asp.status === "fulfilled") setAspectTrend(asp.value);
      if (subAsp.status === "fulfilled") setSubAspectTrend(subAsp.value);
      if (subDimCoeff.status === "fulfilled") setSubDimCoeffHistory(subDimCoeff.value);
      if (aspCoeff.status === "fulfilled") setAspectCoeffHistory(aspCoeff.value);
      if (subAspCoeff.status === "fulfilled") setSubAspectCoeffHistory(subAspCoeff.value);
    }

    load();
    return () => { active = false; };
  }, [hierarchy, drill.level, drill.selectedKey, windowDaily]);

  const mergedSnapshotIndex: SnapshotIndexEntry[] = useMemo(() => {
    if (!snapshotIndex) return [];
    const hourly = Array.isArray(snapshotIndex.hourly) ? snapshotIndex.hourly : [];
    const daily = Array.isArray(snapshotIndex.daily) ? snapshotIndex.daily : [];
    const all = [...hourly, ...daily].filter(
      (e) => e && typeof e.effectiveAt === "string" && typeof e.snapshotId === "string"
    );
    all.sort((a, b) => new Date(b.effectiveAt).getTime() - new Date(a.effectiveAt).getTime());
    return all;
  }, [snapshotIndex]);

  useEffect(() => {
    if (!mergedSnapshotIndex || mergedSnapshotIndex.length === 0) return;
    if (sliderIndex >= 0 && sliderIndex < mergedSnapshotIndex.length) {
      const entry = mergedSnapshotIndex[sliderIndex];
      if (entry.snapshotId && entry.snapshotId !== snapshotId) {
        selectSnapshotById(entry.snapshotId);
      }
    }
  }, [sliderIndex, mergedSnapshotIndex, snapshotId, selectSnapshotById]);

  const itemsForLevel = useMemo(() => {
    if (!hierarchy) return [];
    if (drill.level === 1) return hierarchy.level1;
    if (drill.level === 2) return hierarchy.level2;
    if (drill.level === 3) return hierarchy.level3;
    return hierarchy.level4;
  }, [hierarchy, drill.level]);

  const currentCoefficients = useMemo(() => {
    if (!coefficients) return [];
    if (drill.level === 1) return coefficients.filter((c) => c.level === 1);
    if (drill.level === 2) return coefficients.filter((c) => c.level === 2 && c.key.startsWith(drill.selectedKey || ""));
    if (drill.level === 3) return coefficients.filter((c) => c.level === 3 && c.key.startsWith(drill.selectedKey || ""));
    return coefficients.filter((c) => c.level === 4 && c.key.startsWith(drill.selectedKey || ""));
  }, [coefficients, drill.level, drill.selectedKey]);

  const spiderData = useMemo(() => itemsForLevel.map((i) => ({ label: i.label, value: i.score })), [itemsForLevel]);

  const l1TrendSeries = useMemo(() => {
    if (!history || !hierarchy || drill.level !== 1) return [];
    return hierarchy.level1.map((dim, i) => ({
      key: dim.key,
      label: dim.label,
      color: PALETTE[i % PALETTE.length],
      data: history.map((pt) => ({
        time: pt.date,
        value: num(pt.dimension_scores?.[dim.key] ?? pt.overall),
      })),
    }));
  }, [history, hierarchy, drill.level]);

  const l1ChangeData = useMemo(() => {
    if (!history || !hierarchy || history.length < 2 || drill.level !== 1) return [];
    return hierarchy.level1.map((dim, i) => ({
      key: dim.key,
      label: dim.label,
      color: PALETTE[i % PALETTE.length],
      data: history.slice(1).map((pt, j) => ({
        time: pt.date,
        value: num(pt.dimension_scores?.[dim.key] ?? pt.overall) - num(history[j].dimension_scores?.[dim.key] ?? history[j].overall),
      })),
    }));
  }, [history, hierarchy, drill.level]);

  const scoreMapForLevel = useCallback((pt: ScoreHistoryPoint): Record<string, number | string> | undefined => {
    if (drill.level === 1) return pt.dimension_scores;
    if (drill.level === 2) return pt.sub_dimension_scores;
    if (drill.level === 3) return pt.aspect_scores;
    return pt.sub_aspect_scores;
  }, [drill.level]);

  const perStockTrendSeries = useMemo(() => {
    if (!history || !itemsForLevel.length) return [];
    return itemsForLevel.map((item, i) => ({
      key: item.key,
      label: item.label,
      color: PALETTE[i % PALETTE.length],
      data: history.map((pt) => ({
        time: pt.date,
        value: num(scoreMapForLevel(pt)?.[item.key] ?? pt.overall),
      })),
    }));
  }, [history, itemsForLevel, scoreMapForLevel]);

  const perStockChangeSeries = useMemo(() => {
    if (!history || history.length < 2 || !itemsForLevel.length) return [];
    return itemsForLevel.map((item, i) => ({
      key: item.key,
      label: item.label,
      color: PALETTE[i % PALETTE.length],
      data: history.slice(1).map((pt, j) => ({
        time: pt.date,
        value: num(scoreMapForLevel(pt)?.[item.key] ?? pt.overall) - num(scoreMapForLevel(history[j])?.[item.key] ?? history[j].overall),
      })),
    }));
  }, [history, itemsForLevel, scoreMapForLevel]);

  const perStockChangeFlat = useMemo(() => {
    if (!perStockChangeSeries.length) return [];
    const selected = perStockChangeSeries[0];
    return selected.data.map((pt) => ({
      time: pt.time,
      value: pt.value,
      color: pt.value >= 0 ? "#10b981" : "#ef4444",
    }));
  }, [perStockChangeSeries]);

  const trendResponse = useMemo((): LevelTrendResponse | null => {
    if (drill.level === 1) return null;
    if (drill.level === 2) return subDimTrend;
    if (drill.level === 3) return aspectTrend;
    return subAspectTrend;
  }, [drill.level, subDimTrend, aspectTrend, subAspectTrend]);

  const coeffHistoryResponse = useMemo((): CoefficientHistoryByLevelResponse | null => {
    if (drill.level === 1) return null;
    if (drill.level === 2) return subDimCoeffHistory;
    if (drill.level === 3) return aspectCoeffHistory;
    return subAspectCoeffHistory;
  }, [drill.level, subDimCoeffHistory, aspectCoeffHistory, subAspectCoeffHistory]);

  const trendSeriesForLevel = useMemo(() => {
    if (!trendResponse || trendResponse.series.length === 0) return [];
    const keys = trendResponse.keys.filter((k) => trendResponse.series.some((pt: LevelTrendPoint) => (pt.avg_scores[k] ?? 0) > 0));
    return keys.map((key, i) => ({
      key,
      label: key,
      color: PALETTE[i % PALETTE.length],
      data: trendResponse.series.map((pt: LevelTrendPoint) => ({ time: pt.date, value: pt.avg_scores[key] ?? 0 })),
    }));
  }, [trendResponse]);

  const changeSeriesForLevel = useMemo(() => {
    if (!trendResponse || trendResponse.series.length === 0) return [];
    return trendResponse.series.map((pt: LevelTrendPoint) => {
      const total = Object.values(pt.score_changes ?? {}).reduce((sum, v) => sum + v, 0);
      return { time: pt.date, value: total, color: total >= 0 ? "#10b981" : "#ef4444" };
    });
  }, [trendResponse]);

  const coeffSeriesForLevel = useMemo(() => {
    if (!coeffHistoryResponse || coeffHistoryResponse.series.length === 0) return [];
    const dims = coeffHistoryResponse.series[0]?.metrics ? Object.keys(coeffHistoryResponse.series[0].metrics) : [];
    return dims.map((dim, i) => ({
      key: dim,
      label: dim,
      color: PALETTE[i % PALETTE.length],
      data: coeffHistoryResponse.series.map((p) => ({
        time: p.date,
        value: p.metrics?.[dim] ?? 0,
      })),
    }));
  }, [coeffHistoryResponse]);

  const coeffChangeSeries = useMemo(() => {
    if (!coeffHistoryResponse || coeffHistoryResponse.series.length === 0) return [];
    return coeffHistoryResponse.series.map((p) => {
      const total = Object.values(p.metric_changes ?? {}).reduce((sum, v) => sum + v, 0);
      return { time: p.date, value: total, color: total >= 0 ? "#10b981" : "#ef4444" };
    });
  }, [coeffHistoryResponse]);

  const handleDrillDown = useCallback((item: { key: string; label: string }) => {
    setDrill({
      level: Math.min(drill.level + 1, 4) as Level,
      selectedKey: item.key,
      selectedLabel: item.label,
    });
  }, [drill.level]);

  const handleBreadcrumb = useCallback((level: Level) => {
    setDrill((prev) => ({
      level,
      selectedKey: level === 1 ? null : prev.selectedKey,
      selectedLabel: level === 1 ? null : prev.selectedLabel,
    }));
  }, []);

  const overallScoreText = scoringTab === "HISTORICAL"
    ? `${windowDaily}-DAY ${LEVEL_LABELS[1]} TREND`
    : `${windowIntraday} INTRADAY ${LEVEL_LABELS[1]} TREND`;

  const trendWindowLabel = scoringTab === "HISTORICAL" ? `${windowDaily}-Day` : windowIntraday;

  return {
    // Snapshot state
    snapshot, snapshotId, snapshotTimestamp, snapshotLoading,
    // Data state
    hierarchy, history, coefficients, loading, error,
    // UI state
    drill, scoringTab, viewMode, windowDaily, windowIntraday, sliderIndex,
    // Setters
    setScoringTab, setViewMode, setWindowDaily, setWindowIntraday, setSliderIndex,
    // Computed
    mergedSnapshotIndex, itemsForLevel, currentCoefficients, spiderData,
    l1TrendSeries, l1ChangeData, perStockTrendSeries, perStockChangeSeries, perStockChangeFlat,
    trendSeriesForLevel, changeSeriesForLevel, coeffSeriesForLevel, coeffChangeSeries,
    overallScoreText, trendWindowLabel,
    // Actions
    handleDrillDown, handleBreadcrumb,
  };
}
