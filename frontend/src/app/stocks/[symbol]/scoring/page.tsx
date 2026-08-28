"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { cn } from "@/lib/cn";
import { TarotCard } from "@/components/ui/TarotCard";
import { PageLoading } from "@/components/ui/PageLoading";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { SpiderChart } from "@/components/charts/SpiderChart";
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

import { t } from "@/lib/i18n";

type Level = 1 | 2 | 3;

interface DrillState {
  level: Level;
  selectedKey: string | null;
  selectedLabel: string | null;
}

const LEVEL_LABELS: Record<Level, string> = {
  1: t("app.scoring.hierarchy.dimensions", "en"),
  2: t("app.scoring.hierarchy.sub_dimensions", "en"),
  3: t("app.scoring.hierarchy.aspects", "en"),
};

function num(value: unknown): number {
  if (value === null || value === undefined) return 0;
  const n = typeof value === "number" ? value : parseFloat(String(value));
  return Number.isFinite(n) ? n : 0;
}

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
        if (active) setError(e instanceof Error ? e.message : t("app.analysis.scoring_not_found", "en"));
      } finally {
        if (active) setLoading(false);
      }
    }

    load();

    return () => {
      active = false;
    };
  }, [symbol]);

  useEffect(() => {
    if (itemsForLevel.length > 0 && !itemsForLevel.find((i) => i.key === trendFilter)) {
      setTrendFilter(itemsForLevel[0].key);
    }
  }, [itemsForLevel, trendFilter]);

  const itemsForLevel = useMemo(() => {
    if (!hierarchy) return [];
    if (drill.level === 1) return hierarchy.level1;
    if (drill.level === 2) return hierarchy.level2;
    return hierarchy.level3;
  }, [hierarchy, drill.level]);

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

  const spiderLabels = useMemo(() => itemsForLevel.map((i) => i.label), [itemsForLevel]);
  const spiderValues = useMemo(() => itemsForLevel.map((i) => i.score), [itemsForLevel]);

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
      <DashboardShell title={t("app.scoring.title", "en")}>
        <PageLoading />
      </DashboardShell>
    );
  }

  if (error || !hierarchy) {
    return (
      <DashboardShell title={t("app.scoring.title", "en")}>
        <TarotCard icon="⚠️" title={t("app.analysis.scoring_not_found", "en")}>
          <p className="text-sm text-muted-foreground">{error || t("app.analysis.scoring_not_found", "en")}</p>
          <Link href={`/stocks/${symbol}`} className="mt-3 inline-block text-sm text-secondary hover:underline">
            ← {t("app.stocks.detail.back_to_list", "en")}
          </Link>
        </TarotCard>
      </DashboardShell>
    );
  }

  return (
    <DashboardShell title={t("app.scoring.title", "en")}>
      <div className="flex flex-col gap-4">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Link href={`/stocks/${symbol}`} className="hover:text-foreground">
            {symbol}
          </Link>
          <span>/</span>
          <span className="text-foreground">{t("app.scoring.title", "en")}</span>
        </div>

        <TarotCard icon="💎" title={t("app.scoring.overall_score", "en")}>
          <div className="flex items-center gap-4">
            <div
              className={cn(
                "text-4xl font-black rounded-full h-24 w-24 flex items-center justify-center border-8 shadow-inner",
                hierarchy.overallScore >= 70 ? "text-green-600 border-green-600/20" : hierarchy.overallScore >= 40 ? "text-yellow-500 border-yellow-500/20" : "text-red-600 border-red-600/20"
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
                ? "bg-red-600/10 font-semibold text-red-600"
                : "text-muted-foreground hover:bg-black/5"
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
          <TarotCard title={LEVEL_LABELS[drill.level]}>
            {itemsForLevel.length > 0 ? (
              <SpiderChart labels={spiderLabels} values={spiderValues} height={320} />
            ) : (
              <div className="flex min-h-[240px] items-center justify-center text-muted-foreground">
                {t("app.analysis.no_data", "en")}
              </div>
            )}
          </TarotCard>

          <TarotCard title={`${LEVEL_LABELS[drill.level]} - Trend`}>
            <div className="mb-3 flex flex-wrap gap-2">
              {itemsForLevel.map((item) => (
                <button
                  key={item.key}
                  type="button"
                  onClick={() => setTrendFilter(item.key)}
                  className={cn(
                    "rounded-full px-3 py-1 text-xs transition",
                    trendFilter === item.key
                      ? "bg-red-600/10 font-semibold text-red-600"
                      : "text-muted-foreground hover:bg-black/5"
                  )}
                >
                  {item.label}
                </button>
              ))}
            </div>
            {history && history.length > 0 ? (
              <ScoreTrendChart
                series={[
                  {
                    key: trendFilter,
                    label: itemsForLevel.find((i) => i.key === trendFilter)?.label || trendFilter,
                    color: "#2563EB",
                    data: history.map((pt) => ({
                      time: pt.date,
                      value: num(pt[trendFilter] !== undefined ? pt[trendFilter] : pt.overall),
                    })),
                  },
                ]}
                height={320}
              />
            ) : (
              <div className="flex min-h-[240px] items-center justify-center text-muted-foreground">
                {t("app.stocks.detail.no_history", "en")}
              </div>
            )}
          </TarotCard>
        </div>

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
    </DashboardShell>
  );
}
