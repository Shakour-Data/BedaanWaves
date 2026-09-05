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
  type CoefficientHistoryByLevelResponse,
} from "@/lib/api/dashboard";

import { t } from "@/lib/i18n";
import { num } from "@/lib/utils";

type Level = 1 | 2 | 3 | 4;

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

export default function StockScoringPage() {
  const params = useParams<{ symbol: string }>();
  const symbol = decodeURIComponent(
    Array.isArray(params.symbol) ? params.symbol[0] : params.symbol ?? ""
  );

  const [hierarchy, setHierarchy] = useState<HierarchyScores | null>(null);
  const [history, setHistory] = useState<ScoreHistoryPoint[] | null>(null);
  const [coefficients, setCoefficients] = useState<CoefficientItem[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [drill, setDrill] = useState<DrillState>({ level: 1, selectedKey: null, selectedLabel: null });
  const [trendFilter, setTrendFilter] = useState<string>("overall");

  const [subDimTrend, setSubDimTrend] = useState<LevelTrendResponse | null>(null);
  const [aspectTrend, setAspectTrend] = useState<LevelTrendResponse | null>(null);
  const [subAspectTrend, setSubAspectTrend] = useState<LevelTrendResponse | null>(null);
  const [subDimCoeffHistory, setSubDimCoeffHistory] = useState<CoefficientHistoryByLevelResponse | null>(null);
  const [aspectCoeffHistory, setAspectCoeffHistory] = useState<CoefficientHistoryByLevelResponse | null>(null);
  const [subAspectCoeffHistory, setSubAspectCoeffHistory] = useState<CoefficientHistoryByLevelResponse | null>(null);

  useEffect(() => {
    if (!symbol) return;
    let active = true;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [h, hist, coeff] = await Promise.all([
          fetchHierarchyScores(symbol),
          fetchScoreHistory(symbol, 30),
          fetchCoefficients(symbol),
        ]);
        if (!active) return;
        setHierarchy(h);
        setHistory(hist);
        setCoefficients(coeff);
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
  }, [symbol]);

  const loadSubLevelData = useCallback(async () => {
    if (!hierarchy) return;
    const latestDate = hierarchy.timestamp ? new Date(hierarchy.timestamp).toISOString().split("T")[0] : null;
    const baseOptions = latestDate ? { endDate: latestDate } : { latest: true };

    const [subDim, asp, subAsp, subDimCoeff, aspCoeff, subAspCoeff] = await Promise.allSettled([
      fetchSubDimensionTrend(30, "NASDAQ", drill.level >= 2 ? { ...baseOptions, parent: drill.selectedKey || undefined } : baseOptions),
      fetchAspectTrend(30, "NASDAQ", drill.level >= 3 ? { ...baseOptions, parent: drill.selectedKey || undefined } : baseOptions),
      fetchSubAspectTrend(30, "NASDAQ", drill.level >= 4 ? { ...baseOptions, parent: drill.selectedKey || undefined } : baseOptions),
      fetchCoefficientHistoryByLevel("sub_dimension", 30, "NASDAQ", drill.level >= 2 ? { ...baseOptions, parent: drill.selectedKey || undefined } : baseOptions),
      fetchCoefficientHistoryByLevel("aspect", 30, "NASDAQ", drill.level >= 3 ? { ...baseOptions, parent: drill.selectedKey || undefined } : baseOptions),
      fetchCoefficientHistoryByLevel("sub_aspect", 30, "NASDAQ", drill.level >= 4 ? { ...baseOptions, parent: drill.selectedKey || undefined } : baseOptions),
    ]);

    if (subDim.status === "fulfilled") setSubDimTrend(subDim.value);
    if (asp.status === "fulfilled") setAspectTrend(asp.value);
    if (subAsp.status === "fulfilled") setSubAspectTrend(subAsp.value);
    if (subDimCoeff.status === "fulfilled") setSubDimCoeffHistory(subDimCoeff.value);
    if (aspCoeff.status === "fulfilled") setAspectCoeffHistory(aspCoeff.value);
    if (subAspCoeff.status === "fulfilled") setSubAspectCoeffHistory(subAspCoeff.value);
  }, [hierarchy, drill.level, drill.selectedKey]);

  useEffect(() => {
    loadSubLevelData();
  }, [loadSubLevelData]);

  const itemsForLevel = useMemo(() => {
    if (!hierarchy) return [];
    if (drill.level === 1) return hierarchy.level1;
    if (drill.level === 2) return hierarchy.level2;
    if (drill.level === 3) return hierarchy.level3;
    return hierarchy.level4;
  }, [hierarchy, drill.level]);

  useEffect(() => {
    if (itemsForLevel.length > 0 && !itemsForLevel.find((i) => i.key === trendFilter)) {
      setTrendFilter(itemsForLevel[0].key);
    }
  }, [itemsForLevel, trendFilter]);

  const currentCoefficients = useMemo(() => {
    if (!coefficients) return [];
    if (drill.level === 1) return coefficients.filter((c) => c.level === 1);
    if (drill.level === 2) return coefficients.filter((c) => c.level === 2 && c.key.startsWith(drill.selectedKey || ""));
    if (drill.level === 3) return coefficients.filter((c) => c.level === 3 && c.key.startsWith(drill.selectedKey || ""));
    return coefficients.filter((c) => c.level === 4 && c.key.startsWith(drill.selectedKey || ""));
  }, [coefficients, drill.level, drill.selectedKey]);

  const trendSeries = useMemo(() => {
    if (!history) return [];
    return [
      {
        key: trendFilter,
        label: itemsForLevel.find((i) => i.key === trendFilter)?.label || trendFilter,
        color: "#2563EB",
        data: history.map((pt) => ({
          time: pt.date,
          value: num(pt[trendFilter] !== undefined ? pt[trendFilter] : pt.overall),
        })),
      },
    ];
  }, [history, trendFilter, itemsForLevel]);

  const spiderData = useMemo(() => itemsForLevel.map((i) => ({ label: i.label, value: i.score })), [itemsForLevel]);

  const scoreDeltas = useMemo(() => {
    if (!history || history.length < 2) return [];
    return history.slice(1).map((pt, i) => ({
      date: pt.date,
      value: num(pt[trendFilter] !== undefined ? pt[trendFilter] : pt.overall) - num(history[i][trendFilter] !== undefined ? history[i][trendFilter] : history[i].overall),
    }));
  }, [history, trendFilter]);

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

  if (loading) {
    return <PageLoading />;
  }

  if (error || !hierarchy) {
    return (
      <TarotCard icon="⚠️" title={t("app.analysis.scoring_not_found")}>
        <p className="text-sm text-muted-foreground">{error || t("app.analysis.scoring_not_found")}</p>
        <Link href={`/stocks/${symbol}`} className="mt-3 inline-block text-sm text-secondary hover:underline">
          ← {t("app.stocks.detail.back_to_list")}
        </Link>
      </TarotCard>
    );
  }

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
    const keys = trendResponse.keys.filter((k) => trendResponse.series.some((pt) => (pt.avg_scores[k] ?? 0) > 0));
    return keys.map((key, i) => ({
      key,
      label: key,
      color: PALETTE[i % PALETTE.length],
      data: trendResponse.series.map((pt) => ({ time: pt.date, value: pt.avg_scores[key] ?? 0 })),
    }));
  }, [trendResponse]);

  const changeSeriesForLevel = useMemo(() => {
    if (!trendResponse || trendResponse.series.length === 0) return [];
    return trendResponse.series.map((pt) => {
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

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Link href={`/stocks/${symbol}`} className="hover:text-foreground">
          {symbol}
        </Link>
        <span>/</span>
        <span className="text-foreground">{t("app.scoring.title")}</span>
      </div>

      <TarotCard icon="💎" title={t("app.scoring.overall_score")}>
        <div className="flex items-center gap-4">
          <div
            className={cn(
              "text-4xl font-black rounded-full h-24 w-24 flex items-center justify-center border-8 shadow-inner",
              hierarchy.overallScore >= 70 ? "text-success border-success/20" : hierarchy.overallScore >= 40 ? "text-warning border-warning/20" : "text-error border-error/20"
            )}
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

      <div className="grid grid-cols-1 gap-4">
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

        {trendSeriesForLevel.length > 0 && (
          <TarotCard title={`${LEVEL_LABELS[drill.level]} — Score Trend (30-Day)`}>
            <ScoreTrendChart
              showLegend
              series={trendSeriesForLevel}
              height={280}
            />
          </TarotCard>
        )}

        {changeSeriesForLevel.length > 0 && (
          <TarotCard title={`${LEVEL_LABELS[drill.level]} — Score Changes (Daily Delta)`}>
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
          <TarotCard title={`${LEVEL_LABELS[drill.level]} — Coefficient Trend (30-Day)`}>
            <ScoreTrendChart
              showLegend
              series={coeffSeriesForLevel}
              height={260}
            />
          </TarotCard>
        )}

        {coeffChangeSeries.length > 0 && (
          <TarotCard title={`${LEVEL_LABELS[drill.level]} — Coefficient Changes (Daily Delta)`}>
            <ColumnChart
              data={coeffChangeSeries}
              height={200}
              valueFormatter={(v) => (v >= 0 ? "+" : "") + v.toFixed(4)}
            />
          </TarotCard>
        )}
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {itemsForLevel.map((item) => (
          <TarotCard
            key={item.key}
            className="cursor-pointer transition hover:border-[var(--color-primary)]/30"
            onClick={() => handleDrillDown(item)}
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
