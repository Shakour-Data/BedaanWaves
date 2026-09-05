"use client";

import { useEffect, useMemo, useState } from "react";
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
import { fetchCoefficientHistory } from "@/lib/api/dashboard";
import type { CoefficientHistoryResponse } from "@/lib/api/dashboard";

import { t } from "@/lib/i18n";
import { num } from "@/lib/utils";

type Level = 1 | 2 | 3;

interface DrillState {
  level: Level;
  selectedKey: string | null;
  selectedLabel: string | null;
}

const LEVEL_LABELS: Record<Level, string> = {
  1: t("app.scoring.hierarchy.dimensions"),
  2: t("app.scoring.hierarchy.sub_dimensions"),
  3: t("app.scoring.hierarchy.aspects"),
};

export default function StockScoringPage() {
  const params = useParams<{ symbol: string }>();
  const symbol = decodeURIComponent(
    Array.isArray(params.symbol) ? params.symbol[0] : params.symbol ?? ""
  );

  const [hierarchy, setHierarchy] = useState<HierarchyScores | null>(null);
  const [history, setHistory] = useState<ScoreHistoryPoint[] | null>(null);
  const [coefficients, setCoefficients] = useState<CoefficientItem[] | null>(null);
  const [coefficientHistory, setCoefficientHistory] = useState<CoefficientHistoryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [drill, setDrill] = useState<DrillState>({ level: 1, selectedKey: null, selectedLabel: null });
  const [trendFilter, setTrendFilter] = useState<string>("overall");

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
        const coeffHistory = await fetchCoefficientHistory(30, "NASDAQ", { latest: true }).catch(() => null);
        if (!active) return;
        setHierarchy(h);
        setHistory(hist);
        setCoefficients(coeff);
        if (coeffHistory) setCoefficientHistory(coeffHistory);
      } catch (e: unknown) {
        if (active) setError(e instanceof Error ? e.message : t("app.analysis.scoring_not_found"));
      } finally {
        if (active) setLoading(false);
      }
    }

    load();

    return () => {
      active = false;
    };
  }, [symbol]);

  const itemsForLevel = useMemo(() => {
    if (!hierarchy) return [];
    if (drill.level === 1) return hierarchy.level1;
    if (drill.level === 2) return hierarchy.level2;
    return hierarchy.level3;
  }, [hierarchy, drill.level]);

  useEffect(() => {
    if (itemsForLevel.length > 0 && !itemsForLevel.find((i) => i.key === trendFilter)) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setTrendFilter(itemsForLevel[0].key);
    }
  }, [itemsForLevel, trendFilter]);

  const currentCoefficients = useMemo(() => {
    if (!coefficients) return [];
    if (drill.level === 1) return coefficients.filter((c) => c.level === 1);
    if (drill.level === 2) return coefficients.filter((c) => c.level === 2 && c.key.startsWith(drill.selectedKey || ""));
    return coefficients.filter((c) => c.level === 2 && c.key.startsWith(drill.selectedKey || ""));
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

  // Compute day-over-day score deltas from history
  const scoreDeltas = useMemo(() => {
    if (!history || history.length < 2) return [];
    return history.slice(1).map((pt, i) => ({
      date: pt.date,
      value: pt.overall - (history[i].overall ?? 0),
      prev: history[i].overall,
      current: pt.overall,
    }));
  }, [history]);

  const handleDrillDown = (item: { key: string; label: string }) => {
    setDrill({
      level: (drill.level === 1 ? 2 : drill.level === 2 ? 3 : 3) as Level,
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
    return (
      <PageLoading />
    );
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

  return (
    <div className="flex flex-col gap-4">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Link href={`/stocks/${symbol}`} className="hover:text-foreground">
            {symbol}
          </Link>
          <span>/</span>
          <span className="text-foreground">{t("app.scoring.title")}</span>
        </div>

        <TarotCard icon="💎" title={t("app.scoring.overall_score", "en")}>
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
                {t("app.scoring.system_title", "en")}
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
          {drill.level >= 2 && (
            <>
              <span className="text-muted-foreground">/</span>
              <span className="text-foreground">{drill.selectedLabel || ""}</span>
            </>
          )}
        </div>

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <TarotCard title={`${LEVEL_LABELS[1]} (Dimensions)`}>
            {hierarchy.level1.length > 0 ? (
              <SpiderChart data={hierarchy.level1.map((i) => ({ label: i.label, value: i.score }))} size={320} />
            ) : (
              <div className="flex min-h-[240px] items-center justify-center text-muted-foreground">
                {t("app.analysis.no_data", "en")}
              </div>
            )}
          </TarotCard>

          {hierarchy.level2.length > 0 && (
            <TarotCard title={`${LEVEL_LABELS[2]} (Sub-Dimensions)`}>
              <SpiderChart data={hierarchy.level2.map((i) => ({ label: i.label, value: i.score }))} size={320} />
            </TarotCard>
          )}

          {hierarchy.level3.length > 0 && (
            <TarotCard title={`${LEVEL_LABELS[3]} (Aspects)`}>
              <SpiderChart data={hierarchy.level3.map((i) => ({ label: i.label, value: i.score }))} size={320} />
            </TarotCard>
          )}
        </div>

        {drill.level === 1 && history && history.length > 0 && (
          <div className="space-y-4">
            <TarotCard title="Dimension Score Trends (30-Day)">
              <ScoreTrendChart
                showLegend
                series={hierarchy.level1.map((dim, i) => ({
                  key: dim.key,
                  label: dim.label,
                  color: ["#2563EB", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6", "#EC4899"][i % 6],
                  data: history.map((pt) => ({
                    time: pt.date,
                    value: num(pt[dim.key] !== undefined ? pt[dim.key] : pt.overall),
                  })),
                }))}
                height={280}
              />
            </TarotCard>

            <TarotCard title="Dimension Score Changes (Daily Delta)">
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
                {hierarchy.level1.map((dim, i) => (
                  <div key={dim.key} className="rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] p-3">
                    <div className="mb-1 flex items-center gap-2">
                      <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: ["#2563EB", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6", "#EC4899"][i % 6] }} />
                      <span className="text-xs font-medium text-[var(--color-text-secondary)]">{dim.label}</span>
                    </div>
                    <ColumnChart
                      data={history.slice(1).map((pt, j) => ({
                        time: pt.date,
                        value: num(pt[dim.key] !== undefined ? pt[dim.key] : pt.overall) - num(history[j][dim.key] !== undefined ? history[j][dim.key] : history[j].overall),
                        color: (num(pt[dim.key] !== undefined ? pt[dim.key] : pt.overall) - num(history[j][dim.key] !== undefined ? history[j][dim.key] : history[j].overall)) >= 0 ? "#10b981" : "#ef4444",
                      }))}
                      height={140}
                    />
                  </div>
                ))}
              </div>
            </TarotCard>
          </div>
        )}

        {drill.level === 1 && (
          <TarotCard title="Sub-Level Trends (30-Day)">
            <p className="text-xs text-muted-foreground mb-3">
              Historical 30-day trend data for sub-dimensions, aspects, and sub-aspects is not yet available. Current snapshot scores are shown in the spider charts above and drill-down cards below.
            </p>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] p-4">
                <h3 className="text-sm font-semibold text-[var(--color-text-primary)] mb-2">Sub-Dimension Trend Placeholder</h3>
                <p className="text-[11px] text-[var(--color-text-secondary)]">
                  Line chart of each sub-dimension score trend will appear here when per-day sub-dimension history is exposed by the scoring pipeline.
                </p>
              </div>
              <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] p-4">
                <h3 className="text-sm font-semibold text-[var(--color-text-primary)] mb-2">Aspect Trend Placeholder</h3>
                <p className="text-[11px] text-[var(--color-text-secondary)]">
                  Line chart of each aspect score trend will appear here when per-day aspect history is exposed by the scoring pipeline.
                </p>
              </div>
            </div>
          </TarotCard>
        )}

        <TarotCard title="Score Changes">
          <div className="mb-2">
            <p className="text-xs text-muted-foreground">Day-over-day change in overall score across the 30-day window</p>
          </div>
          {scoreDeltas.length > 0 ? (
            <ColumnChart
              data={scoreDeltas.map((d) => ({
                time: d.date,
                value: d.value,
                color: d.value >= 0 ? "#10b981" : "#ef4444",
              }))}
              height={220}
              valueFormatter={(v) => (v >= 0 ? "+" : "") + v.toFixed(2)}
            />
          ) : (
            <div className="flex min-h-[160px] items-center justify-center text-muted-foreground">
              No delta data available
            </div>
          )}
        </TarotCard>

        <TarotCard title={t("app.scoring.weight", "en")}>
          {currentCoefficients.length > 0 ? (
            <CoefficientChart
              data={currentCoefficients.map((c) => ({
                key: c.key,
                label: c.label,
                weight: c.weight,
              }))}
              height={280}
            />
          ) : (
            <div className="flex min-h-[120px] items-center justify-center text-muted-foreground">
              {t("app.analysis.no_data", "en")}
            </div>
          )}
        </TarotCard>

        {coefficientHistory && coefficientHistory.series.length > 0 && (
          <div className="space-y-4">
            <TarotCard title="Coefficient Weight Trend (30-Day)">
              <ScoreTrendChart
                series={coefficientHistory.dimensions.map((dim, i) => ({
                  key: dim,
                  label: dim.charAt(0).toUpperCase() + dim.slice(1),
                  color: ["#2563EB", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6", "#EC4899"][i % 6],
                  data: coefficientHistory.series.map((p) => ({
                    time: p.date,
                    value: p.dimensions?.[dim] ?? 0,
                  })),
                }))}
                showLegend
                height={260}
              />
            </TarotCard>

            <TarotCard title="Coefficient Weight Changes (Daily Delta)">
              <ColumnChart
                data={coefficientHistory.series.map((p) => ({
                  time: p.date,
                  value: Object.values(p.dimension_changes ?? {}).reduce((sum, v) => sum + v, 0),
                  color: Object.values(p.dimension_changes ?? {}).reduce((sum, v) => sum + v, 0) >= 0 ? "#10b981" : "#ef4444",
                }))}
                height={200}
                valueFormatter={(v) => (v >= 0 ? "+" : "") + v.toFixed(4)}
              />
            </TarotCard>
          </div>
        )}

        {coefficients && coefficients.length > 0 && (
          <div className="space-y-4">
            <TarotCard title="Sub-Level Coefficients (Current Snapshot)">
              <p className="text-xs text-muted-foreground mb-3">
                Static weights for sub-dimensions (level 2) and aspects (level 3). Historical coefficient trends for sub-levels are not yet available.
              </p>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                {([2, 3] as const).map((level) => {
                  const items = coefficients.filter((c) => c.level === level);
                  if (items.length === 0) return null;
                  const label = level === 2 ? "Sub-Dimensions" : "Aspects";
                  return (
                    <div key={level} className="rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] p-4">
                      <h3 className="text-sm font-semibold text-[var(--color-text-primary)] mb-2">{label}</h3>
                      <div className="space-y-2">
                        {items.map((c) => (
                          <div key={c.key} className="flex items-center justify-between text-xs">
                            <span className="text-[var(--color-text-secondary)]">{c.label}</span>
                            <span className="font-mono text-[var(--color-text-primary)]">{(c.weight * 100).toFixed(1)}%</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            </TarotCard>
          </div>
        )}

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
                  {t("app.scoring.weight", "en")}: {(item.weight * 100).toFixed(1)}%
                </div>
              </div>
            </TarotCard>
          ))}
        </div>
      </div>
  );
}
