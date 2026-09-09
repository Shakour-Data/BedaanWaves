"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { cn } from "@/lib/cn";
import { TarotCard } from "@/components/ui/TarotCard";
import { PageLoading } from "@/components/ui/PageLoading";
import { SpiderChart } from "@/components/charts/SpiderChart";
import { ColumnChart } from "@/components/charts/ColumnChart";
import { ScoreTrendChart } from "@/components/charts/ScoreTrendChart";
import { CoefficientChart } from "@/components/charts/CoefficientChart";
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
import { ScoreTripleBadge } from "@/components/scoring/ScoreTripleBadge";
import { AsOfStamp } from "@/components/scoring/AsOfStamp";
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

import { t } from "@/lib/i18n";
import { num } from "@/lib/utils";

type Level = 1 | 2 | 3 | 4;
type ScoringTab = "HISTORICAL" | "INTRADAY";
type ViewMode = "SIMPLE" | "EXPERT";
type IntradayWindow = "6h" | "24h" | "7d";
type DailyWindow = 30 | 90 | 365;

interface ScoreItemShape {
  key?: string;
  level_key?: string;
  label?: string;
  name?: string;
  score?: number;
  value?: number;
  level_score?: number;
  weight?: number;
  coefficient?: number;
  w?: number;
}

interface RawOverallShape {
  score?: number;
  grade?: string;
}

interface RawHierarchyScores {
  overall?: number | RawOverallShape | null;
  overallScore?: number;
  OVERALL?: RawOverallShape;
  grade?: string;
  level1?: ScoreItemShape[] | null;
  level2?: ScoreItemShape[] | null;
  level3?: ScoreItemShape[] | null;
  level4?: ScoreItemShape[] | null;
  dimensions?: ScoreItemShape[] | null;
  sub_dimensions?: ScoreItemShape[] | null;
  aspects?: ScoreItemShape[] | null;
  sub_aspects?: ScoreItemShape[] | null;
  [key: string]: unknown;
}

interface RawWeightShape {
  level1?: ScoreItemShape[];
  level2?: ScoreItemShape[];
  level3?: ScoreItemShape[];
  level4?: ScoreItemShape[];
  dimension?: Record<string, number>;
  sub_dimension?: Record<string, number>;
  aspect?: Record<string, number>;
  sub_aspect?: Record<string, number>;
  [key: string]: unknown;
}

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

const DAILY_WINDOW_OPTIONS: DailyWindow[] = [30, 90, 365];
const INTRADAY_WINDOW_OPTIONS: IntradayWindow[] = ["6h", "24h", "7d"];

function snapshotHierarchyToLegacy(snap: SnapshotResponse, tab: ScoringTab): HierarchyScores | null {
  const scores = (tab === "HISTORICAL" ? snap.scores.daily : snap.scores.current) as unknown as RawHierarchyScores;
  if (!scores) return null;
  const overallVal = scores.overall;
  const overallObj = typeof overallVal === 'object' && overallVal !== null ? overallVal : undefined;
  const resolvedOverall = num(
    overallObj?.score ?? scores.overallScore ?? scores.OVERALL?.score ?? 0
  );
  const resolvedGrade = overallObj?.grade ?? scores.grade ?? null;

  const toArray = (dict: object | undefined | null): ScoreItemShape[] => {
    if (!dict) return [];
    return Object.entries(dict).map(([key, value]) => ({
      key,
      label: key,
      name: key,
      score: typeof value === 'number' ? value : num(value),
      value: typeof value === 'number' ? value : num(value),
    }));
  };

  return {
    overallScore: resolvedOverall,
    grade: resolvedGrade ?? (resolvedOverall >= 70 ? "STRONG_BUY" : resolvedOverall >= 40 ? "HOLD" : "STRONG_SELL"),
    timestamp: snap.timestamp,
    level1: scores.level1 ?? toArray(scores.dimension ?? scores.dimensions),
    level2: scores.level2 ?? toArray(scores.sub_dimension ?? scores.sub_dimensions),
    level3: scores.level3 ?? toArray(scores.aspect ?? scores.aspects),
    level4: scores.level4 ?? toArray(scores.sub_aspect ?? scores.sub_aspects),
  } as HierarchyScores;
}

function snapshotTrendsToLegacy(snap: SnapshotResponse, tab: ScoringTab): ScoreHistoryPoint[] {
  const series = tab === "HISTORICAL" ? snap.trends?.daily ?? [] : snap.trends?.intraday ?? [];
  return series.map((pt) => {
    const dateStr = pt.date ?? pt.effective_at;
    const levelScores = pt.level_scores ?? {};
    const dimScores: Record<string, number> = {};
    const subDimScores: Record<string, number> = {};
    const aspectScores: Record<string, number> = {};
    const subAspectScores: Record<string, number> = {};
    Object.entries(levelScores).forEach(([k, v]) => {
      const val = typeof v === 'number' ? v : num(v);
      if (!k.includes('_')) {
        dimScores[k] = val;
      } else if (k.includes('_aspect_') && k.includes('_detail_')) {
        subAspectScores[k] = val;
      } else if (k.includes('_aspect_')) {
        aspectScores[k] = val;
      } else {
        subDimScores[k] = val;
      }
    });
    return {
      date: dateStr,
      overall: num(pt.overall ?? 0),
      dimension_scores: dimScores,
      sub_dimension_scores: subDimScores,
      aspect_scores: aspectScores,
      sub_aspect_scores: subAspectScores,
    } as ScoreHistoryPoint;
  });
}

function snapshotWeightsToLegacy(snap: SnapshotResponse): CoefficientItem[] {
  const weights = snap.weights as unknown as RawWeightShape;
  if (!weights) return [];
  const result: CoefficientItem[] = [];
  const levels = ["level1", "level2", "level3", "level4"] as const;
  levels.forEach((lvlKey, lvlIdx) => {
    const arr = weights[lvlKey] as ScoreItemShape[] | undefined;
    if (Array.isArray(arr)) {
      arr.forEach((it) => {
        result.push({
          level: (lvlIdx + 1) as 1 | 2 | 3 | 4,
          key: it.key ?? it.level_key ?? it.label ?? "",
          label: it.label ?? it.name ?? it.key ?? "",
          weight: num(it.weight ?? it.value ?? 0),
        });
      });
    }
  });
  return result;
}

export default function StockScoringPage() {
  const params = useParams<{ symbol: string }>();
  const symbol = decodeURIComponent(
    Array.isArray(params.symbol) ? params.symbol[0] : params.symbol ?? ""
  );

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

    return () => {
      active = false;
    };
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

    return () => {
      active = false;
    };
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

  const getTrendResponse = (): LevelTrendResponse | null => {
    if (drill.level === 1) return null;
    if (drill.level === 2) return subDimTrend;
    if (drill.level === 3) return aspectTrend;
    return subAspectTrend;
  };

  const getCoeffHistory = (): CoefficientHistoryByLevelResponse | null => {
    if (drill.level === 1) return null;
    if (drill.level === 2) return subDimCoeffHistory;
    if (drill.level === 3) return aspectCoeffHistory;
    return subAspectCoeffHistory;
  };

  const trendResponse = getTrendResponse();
  const coeffHistoryResponse = getCoeffHistory();

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

  const handleDrillDown = (item: { key: string; label: string }) => {
    setDrill({
      level: Math.min(drill.level + 1, 4) as Level,
      selectedKey: item.key,
      selectedLabel: item.label,
    });
  };

  const handleBreadcrumb = (level: Level) => {
    setDrill({
      level,
      selectedKey: level === 1 ? null : drill.selectedKey,
      selectedLabel: level === 1 ? null : drill.selectedLabel,
    });
  };

  const overallScoreText = scoringTab === "HISTORICAL"
    ? `${windowDaily}-DAY ${LEVEL_LABELS[1]} TREND`
    : `${windowIntraday} INTRADAY ${LEVEL_LABELS[1]} TREND`;

  const trendWindowLabel = scoringTab === "HISTORICAL" ? `${windowDaily}-Day` : windowIntraday;

  if (loading || snapshotLoading) {
    return <PageLoading />;
  }

  if (error || !hierarchy) {
    return (
      <TarotCard icon="[!]" title={t("app.analysis.scoring_not_found")}>
        <p className="text-sm text-muted-foreground">{error || t("app.analysis.scoring_not_found")}</p>
        <Link href={`/stocks/${symbol}`} className="mt-3 inline-block text-sm text-secondary hover:underline">
          ← {t("app.stocks.detail.back_to_list")}
        </Link>
      </TarotCard>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between gap-2 text-sm text-muted-foreground">
        <div className="flex items-center gap-2">
          <Link href={`/stocks/${symbol}`} className="hover:text-foreground">
            {symbol}
          </Link>
          <span>/</span>
          <span className="text-foreground">{t("app.scoring.title")}</span>
        </div>
        <AsOfStamp
          effectiveAt={snapshotTimestamp ?? hierarchy.timestamp ?? null}
          snapshotId={snapshotId ?? null}
          variant="compact"
        />
      </div>

      <div
        role="tablist"
        aria-label="Scoring view mode"
        className="flex items-center justify-between gap-3 flex-wrap rounded-xl border border-[var(--color-border)] bg-[var(--color-background)] p-3"
      >
        <div className="flex items-center gap-1 rounded-lg bg-[var(--color-neutral)] p-1">
          {(["HISTORICAL", "INTRADAY"] as ScoringTab[]).map((tab) => (
            <button
              key={tab}
              role="tab"
              type="button"
              aria-selected={scoringTab === tab}
              aria-controls={`scoring-panel-${tab}`}
              id={`scoring-tab-${tab}`}
              onClick={() => setScoringTab(tab)}
              className={cn(
                "rounded-md px-4 py-1.5 text-sm font-semibold transition",
                scoringTab === tab
                  ? "bg-[var(--color-background)] text-[var(--color-primary)] shadow-sm border border-[var(--color-border)]"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              {tab === "HISTORICAL" ? "◷ HISTORICAL" : "⚡ INTRADAY"}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          {scoringTab === "HISTORICAL" ? (
            <div className="flex items-center gap-1 rounded-lg bg-[var(--color-neutral)] p-1" role="group" aria-label="Historical window">
              {DAILY_WINDOW_OPTIONS.map((w) => (
                <button
                  key={w}
                  type="button"
                  onClick={() => setWindowDaily(w)}
                  className={cn(
                    "rounded-md px-3 py-1 text-xs font-semibold transition",
                    windowDaily === w
                      ? "bg-[var(--color-background)] text-[var(--color-primary)] border border-[var(--color-border)] shadow-sm"
                      : "text-muted-foreground hover:text-foreground"
                  )}
                  aria-pressed={windowDaily === w}
                >
                  {w}D
                </button>
              ))}
            </div>
          ) : (
            <div className="flex items-center gap-1 rounded-lg bg-[var(--color-neutral)] p-1" role="group" aria-label="Intraday window">
              {INTRADAY_WINDOW_OPTIONS.map((w) => (
                <button
                  key={w}
                  type="button"
                  onClick={() => setWindowIntraday(w)}
                  className={cn(
                    "rounded-md px-3 py-1 text-xs font-semibold transition",
                    windowIntraday === w
                      ? "bg-[var(--color-background)] text-[var(--color-primary)] border border-[var(--color-border)] shadow-sm"
                      : "text-muted-foreground hover:text-foreground"
                  )}
                  aria-pressed={windowIntraday === w}
                >
                  {w.toUpperCase()}
                </button>
              ))}
            </div>
          )}

          <div className="flex items-center gap-1 rounded-lg bg-[var(--color-neutral)] p-1" role="group" aria-label="View complexity">
            {(["SIMPLE", "EXPERT"] as ViewMode[]).map((m) => (
              <button
                key={m}
                type="button"
                onClick={() => setViewMode(m)}
                className={cn(
                  "rounded-md px-3 py-1 text-xs font-semibold transition",
                  viewMode === m
                    ? "bg-[var(--color-background)] text-[var(--color-primary)] border border-[var(--color-border)] shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                )}
                aria-pressed={viewMode === m}
              >
                {m}
              </button>
            ))}
          </div>
        </div>
      </div>

      {mergedSnapshotIndex && mergedSnapshotIndex.length > 0 && (
        <TarotCard title="[SR] SNAPSHOT REPLAY — Drag to travel in time">
          <div className="flex flex-col gap-3">
            <div className="flex items-center justify-between gap-3 text-xs">
              <span className="font-mono text-muted-foreground">
                EARLIEST · {mergedSnapshotIndex[mergedSnapshotIndex.length - 1]?.effectiveAt?.slice(0, 16)?.replace("T", " ") ?? "—"}
                <span className="ml-2 uppercase text-[10px] text-[var(--color-text-secondary)]">
                  {mergedSnapshotIndex[mergedSnapshotIndex.length - 1]?.tier ?? ""}
                </span>
              </span>
              <span className="font-semibold text-[var(--color-primary)]">
                {mergedSnapshotIndex[sliderIndex]?.effectiveAt?.slice(0, 16)?.replace("T", " ") ?? "NOW"}
                {mergedSnapshotIndex[sliderIndex]?.snapshotId && (
                  <span className="ml-2 font-mono text-[10px] text-muted-foreground">
                    #{mergedSnapshotIndex[sliderIndex].snapshotId.slice(0, 8)}
                  </span>
                )}
                <span className="ml-2 uppercase text-[10px] text-[var(--color-text-secondary)]">
                  {mergedSnapshotIndex[sliderIndex]?.tier ?? ""}
                </span>
              </span>
              <span className="font-mono text-muted-foreground">
                LATEST · {mergedSnapshotIndex[0]?.effectiveAt?.slice(0, 16)?.replace("T", " ") ?? "—"}
                <span className="ml-2 uppercase text-[10px] text-[var(--color-text-secondary)]">
                  {mergedSnapshotIndex[0]?.tier ?? ""}
                </span>
              </span>
            </div>
            <input
              type="range"
              min={0}
              max={mergedSnapshotIndex.length - 1}
              value={sliderIndex}
              onChange={(e) => setSliderIndex(parseInt(e.target.value, 10))}
              aria-label="Snapshot time travel slider"
              aria-valuemin={0}
              aria-valuemax={mergedSnapshotIndex.length - 1}
              aria-valuenow={sliderIndex}
              className="w-full h-2 bg-[var(--color-neutral)] rounded-full appearance-none cursor-pointer accent-[var(--color-primary)]"
            />
            <div className="text-[10px] text-muted-foreground">
              {mergedSnapshotIndex.length} snapshots available · Drag slider to replay historical scoring states at exact parity across all widgets.
            </div>
          </div>
        </TarotCard>
      )}

      <TarotCard title="✦ THREE-FRAME SCORE REFERENCE">
        <div className="flex flex-col gap-3">
          {snapshot ? (
            <ScoreTripleBadge
              scores={snapshot.scores}
              deltas={snapshot.deltas}
              showDailyDelta={scoringTab === "HISTORICAL"}
              size="lg"
            />
          ) : (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              {["PREV DAY", "PREV HOUR", "CURRENT"].map((lbl, i) => (
                <div
                  key={lbl}
                  role="group"
                  aria-label={`${lbl} score frame. Snapshot pipeline pending.`}
                  className={cn(
                    "flex flex-col items-start rounded-xl border border-dashed border-[var(--color-border)] bg-[var(--color-neutral)]/30 px-5 py-4",
                    i === 2 && "border-[var(--color-primary)]/20 ring-1 ring-[var(--color-primary)]/5"
                  )}
                >
                  <div className="flex w-full items-center justify-between">
                    <span className="text-sm uppercase tracking-wider font-semibold text-[var(--color-text-secondary)]">{lbl}</span>
                    {i === 2 && (
                      <span className="rounded px-1.5 py-0.5 bg-[var(--color-primary)]/10 text-[var(--color-primary)] font-semibold text-sm">
                        LIVE
                      </span>
                    )}
                  </div>
                  <div className="mt-1 text-3xl font-bold tabular-nums text-[var(--color-text-secondary)]">
                    {i === 2 && hierarchy ? hierarchy.overallScore : "—"}
                  </div>
                  <div className="mt-1 text-sm text-[var(--color-text-secondary)]/80">
                    {i === 2
                      ? hierarchy?.grade?.replace("_", " ") ?? "Pending snapshot"
                      : "Pending snapshot pipeline"}
                  </div>
                </div>
              ))}
            </div>
          )}
          {!snapshot && (
            <div className="rounded-lg border border-dashed border-[var(--color-border)] bg-[var(--color-neutral)]/40 p-3 text-xs text-muted-foreground">
              ◇ NOTE: Snapshot pipeline has not yet produced rows for this symbol. The CURRENT frame above is derived from the legacy daily REST endpoint (single-frame score only). Three-frame PREV-DAY / PREV-HOUR / CURRENT parity activates once HourlyScoreRecompute and DailyScoreRecalculation scheduler jobs populate ScoringSnapshot tier rows.
            </div>
          )}
        </div>
      </TarotCard>

      <TarotCard icon="[AN]" title={`${symbol} · ${overallScoreText}`}>
        <div className="flex items-center gap-4 flex-wrap">
          <div
            className={cn(
              "text-4xl font-black rounded-full h-24 w-24 flex items-center justify-center border-8 shadow-inner",
              hierarchy.overallScore >= 70 ? "text-success border-success/20" : hierarchy.overallScore >= 40 ? "text-warning border-warning/20" : "text-error border-error/20"
            )}
            aria-label={`Overall score ${hierarchy.overallScore}`}
          >
            {hierarchy.overallScore}
          </div>
          <div>
            <div className="text-lg font-bold">{hierarchy.grade?.replace("_", " ")}</div>
            <div className="text-xs text-muted-foreground">
              {t("app.scoring.system_title")}
            </div>
          </div>
        </div>
      </TarotCard>

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

      <div
        id={`scoring-panel-${scoringTab}`}
        role="tabpanel"
        aria-labelledby={`scoring-tab-${scoringTab}`}
        className="grid grid-cols-1 gap-4"
      >
        {viewMode === "EXPERT" ? (
          <>
            {([1, 2, 3, 4] as Level[]).map((lvl) => {
              const levelItems = lvl === 1 ? hierarchy.level1 : lvl === 2 ? hierarchy.level2 : lvl === 3 ? hierarchy.level3 : hierarchy.level4;
              if (!levelItems || levelItems.length === 0) return null;
              const levelSpider = levelItems.map((i) => ({ label: i.label, value: i.score }));
              const levelTrend = history && history.length > 0 ? levelItems.map((item, i) => ({
                key: item.key,
                label: item.label,
                color: PALETTE[i % PALETTE.length],
                data: history.map((pt) => ({
                  time: pt.date,
                  value: num(
                    lvl === 1 ? pt.dimension_scores?.[item.key] :
                    lvl === 2 ? pt.sub_dimension_scores?.[item.key] :
                    lvl === 3 ? pt.aspect_scores?.[item.key] :
                    pt.sub_aspect_scores?.[item.key] ?? pt.overall
                  ),
                })),
              })) : [];
              const levelChange = history && history.length >= 2 ? levelItems.map((item, i) => ({
                key: item.key,
                label: item.label,
                color: PALETTE[i % PALETTE.length],
                data: history.slice(1).map((pt, j) => {
                  const getVal = (p: ScoreHistoryPoint) => num(
                    lvl === 1 ? p.dimension_scores?.[item.key] :
                    lvl === 2 ? p.sub_dimension_scores?.[item.key] :
                    lvl === 3 ? p.aspect_scores?.[item.key] :
                    p.sub_aspect_scores?.[item.key] ?? p.overall
                  );
                  return { time: pt.date, value: getVal(pt) - getVal(history[j]) };
                }),
              })) : [];
              const levelWeights = lvl === 1 ? coefficients?.filter((c) => c.level === 1) :
                lvl === 2 ? coefficients?.filter((c) => c.level === 2) :
                lvl === 3 ? coefficients?.filter((c) => c.level === 3) :
                coefficients?.filter((c) => c.level === 4);

              return (
                <div key={lvl} className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                  <TarotCard title={`${LEVEL_LABELS[lvl]} · Spider`}>
                    {levelSpider.length > 0 ? (
                      <div className="flex justify-center">
                        <SpiderChart
                          data={levelSpider}
                          size={320}
                          color={PALETTE[lvl - 1]}
                          onLabelClick={lvl < 4 ? (label) => {
                            const it = levelItems.find((i) => i.label === label);
                            if (it) handleDrillDown(it);
                          } : undefined}
                        />
                      </div>
                    ) : (
                      <div className="flex min-h-[240px] items-center justify-center text-muted-foreground">No data</div>
                    )}
                  </TarotCard>

                  <TarotCard title={`${LEVEL_LABELS[lvl]} · Trend (${trendWindowLabel})`}>
                    {levelTrend.length > 0 ? (
                      <ScoreTrendChart series={levelTrend} height={260} showLegend />
                    ) : (
                      <div className="flex min-h-[240px] items-center justify-center text-muted-foreground">No data</div>
                    )}
                  </TarotCard>

                  <TarotCard title={`${LEVEL_LABELS[lvl]} · Delta`}>
                    {levelChange.length > 0 ? (
                      lvl === 1 ? (
                        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                          {levelChange.slice(0, 6).map((series) => (
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
                          data={(levelChange[0]?.data ?? []).map((pt) => ({ time: pt.time, value: pt.value, color: pt.value >= 0 ? "#10b981" : "#ef4444" }))}
                          height={200}
                          valueFormatter={(v) => (v >= 0 ? "+" : "") + v.toFixed(2)}
                        />
                      )
                    ) : (
                      <div className="flex min-h-[200px] items-center justify-center text-muted-foreground">No data</div>
                    )}
                  </TarotCard>

                  <TarotCard title={`${LEVEL_LABELS[lvl]} · Weights`}>
                    {levelWeights && levelWeights.length > 0 ? (
                      <CoefficientChart
                        data={levelWeights.map((c) => ({ key: c.key, label: c.label, weight: c.weight }))}
                        height={260}
                      />
                    ) : (
                      <div className="flex min-h-[200px] items-center justify-center text-muted-foreground">No data</div>
                    )}
                  </TarotCard>
                </div>
              );
            })}
          </>
        ) : (
          <>
            <TarotCard title={`${LEVEL_LABELS[drill.level]} — Spider Chart`}>
              {spiderData.length > 0 ? (
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
              ) : (
                <div className="flex min-h-[240px] items-center justify-center text-muted-foreground">
                  No data available
                </div>
              )}
            </TarotCard>

            {l1TrendSeries.length > 0 && drill.level === 1 && (
              <TarotCard title={`${LEVEL_LABELS[1]} — Score Trend (${trendWindowLabel})`}>
                <ScoreTrendChart
                  showLegend
                  series={l1TrendSeries}
                  height={280}
                />
              </TarotCard>
            )}

            {l1ChangeData.length > 0 && drill.level === 1 && (
              <TarotCard title={`${LEVEL_LABELS[1]} — Score Changes (${scoringTab === "HISTORICAL" ? "Daily" : "Periodic"} Delta)`}>
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {l1ChangeData.map((series) => (
                    <div key={series.key} className="rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] p-3">
                      <div className="mb-1 flex items-center gap-2">
                        <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: series.color }} />
                        <span className="text-xs font-medium text-[var(--color-text-secondary)]">{series.label}</span>
                      </div>
                      <ColumnChart
                        data={series.data}
                        height={140}
                        valueFormatter={(v) => (v >= 0 ? "+" : "") + v.toFixed(2)}
                      />
                    </div>
                  ))}
                </div>
              </TarotCard>
            )}

            {perStockTrendSeries.length > 0 && drill.level > 1 && (
              <TarotCard title={`${LEVEL_LABELS[drill.level]} — Score Trend (${trendWindowLabel})`}>
                <ScoreTrendChart
                  showLegend
                  series={perStockTrendSeries}
                  height={280}
                />
              </TarotCard>
            )}

            {perStockChangeFlat.length > 0 && drill.level > 1 && (
              <TarotCard title={`${LEVEL_LABELS[drill.level]} — Score Changes (${scoringTab === "HISTORICAL" ? "Daily" : "Periodic"} Delta)`}>
                <ColumnChart
                  data={perStockChangeFlat}
                  height={220}
                  valueFormatter={(v) => (v >= 0 ? "+" : "") + v.toFixed(2)}
                />
              </TarotCard>
            )}

            {trendSeriesForLevel.length > 0 && drill.level > 1 && perStockTrendSeries.length === 0 && (
              <TarotCard title={`${LEVEL_LABELS[drill.level]} — Score Trend (${trendWindowLabel}) — Market`}>
                <ScoreTrendChart
                  showLegend
                  series={trendSeriesForLevel}
                  height={280}
                />
              </TarotCard>
            )}

            {changeSeriesForLevel.length > 0 && drill.level > 1 && perStockChangeSeries.length === 0 && (
              <TarotCard title={`${LEVEL_LABELS[drill.level]} — Score Changes (${scoringTab === "HISTORICAL" ? "Daily" : "Periodic"} Delta) — Market`}>
                <ColumnChart
                  data={changeSeriesForLevel}
                  height={220}
                  valueFormatter={(v) => (v >= 0 ? "+" : "") + v.toFixed(2)}
                />
              </TarotCard>
            )}

            {currentCoefficients.length > 0 && (
              <TarotCard title={`${LEVEL_LABELS[drill.level]} — Coefficients (Weights)`}>
                <CoefficientChart
                  data={currentCoefficients.map((c) => ({
                    key: c.key,
                    label: c.label,
                    weight: c.weight,
                  }))}
                  height={280}
                />
              </TarotCard>
            )}

            {coeffSeriesForLevel.length > 0 && (
              <TarotCard title={`${LEVEL_LABELS[drill.level]} — Coefficient Trend (${trendWindowLabel})`}>
                <ScoreTrendChart
                  showLegend
                  series={coeffSeriesForLevel}
                  height={260}
                />
              </TarotCard>
            )}

            {coeffChangeSeries.length > 0 && (
              <TarotCard title={`${LEVEL_LABELS[drill.level]} — Coefficient Changes (${scoringTab === "HISTORICAL" ? "Daily" : "Periodic"} Delta)`}>
                <ColumnChart
                  data={coeffChangeSeries}
                  height={200}
                  valueFormatter={(v) => (v >= 0 ? "+" : "") + v.toFixed(4)}
                />
              </TarotCard>
            )}
          </>
        )}
      </div>

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
                  <span className="font-bold text-lg">{item.score}</span>
                  <div className="h-1.5 flex-1 mx-2 bg-border rounded-full overflow-hidden">
                    <div
                      className={cn(
                        "h-full rounded-full",
                        item.score >= 70 ? "bg-green-600" : item.score >= 40 ? "bg-yellow-500" : "bg-red-600"
                      )}
                      style={{ width: `${item.score}%` }}
                    />
                  </div>
                </div>
              </div>
              <div className="text-xs text-muted-foreground">
                Weight: {(item.weight * 100).toFixed(1)}%
              </div>
            </div>
          </TarotCard>
        ))}
      </div>
    </div>
  );
}
