"use client";

import { cn } from "@/lib/cn";
import { num } from "@/lib/utils";
import { TarotCard } from "@/components/ui/TarotCard";
import { SpiderChart } from "@/components/charts/SpiderChart";
import { ScoreTrendChart } from "@/components/charts/ScoreTrendChart";
import { ColumnChart } from "@/components/charts/ColumnChart";
import { CoefficientChart } from "@/components/charts/CoefficientChart";
import { LEVEL_LABELS, PALETTE, type Level } from "./useScoringData";
import type { HierarchyScores, ScoreHistoryPoint, CoefficientItem, DimensionScore } from "@/lib/api/scoring";

interface ExpertLevelViewProps {
  hierarchy: HierarchyScores;
  history: ScoreHistoryPoint[] | null;
  coefficients: CoefficientItem[] | null;
  trendWindowLabel: string;
  scoringTabLabel: string;
  onDrillDown: (item: { key: string; label: string }) => void;
}

function getScoreForLevel(pt: ScoreHistoryPoint, lvl: Level, key: string): number {
  let raw: number | string | undefined;
  switch (lvl) {
    case 1: raw = pt.dimension_scores?.[key]; break;
    case 2: raw = pt.sub_dimension_scores?.[key]; break;
    case 3: raw = pt.aspect_scores?.[key]; break;
    case 4: raw = pt.sub_aspect_scores?.[key]; break;
  }
  return typeof raw === "number" ? raw : pt.overall;
}

function getLevelItems(hierarchy: HierarchyScores, lvl: Level): DimensionScore[] | undefined {
  switch (lvl) {
    case 1: return hierarchy.level1;
    case 2: return hierarchy.level2;
    case 3: return hierarchy.level3;
    case 4: return hierarchy.level4;
  }
}

function getLevelWeights(coefficients: CoefficientItem[] | null, lvl: Level): CoefficientItem[] | undefined {
  const targetLevel = lvl === 4 ? 4 : lvl;
  return coefficients?.filter((c) => c.level === targetLevel);
}

export function ExpertLevelView({
  hierarchy,
  history,
  coefficients,
  trendWindowLabel,
  scoringTabLabel,
  onDrillDown,
}: ExpertLevelViewProps) {
  return (
    <>
      {([1, 2, 3, 4] as Level[]).map((lvl) => {
        const levelItems = getLevelItems(hierarchy, lvl);
        if (!levelItems || levelItems.length === 0) return null;

        const levelSpider = levelItems.map((i) => ({ label: i.label, value: i.score }));

        const levelTrend = history && history.length > 0
          ? levelItems.map((item, i) => ({
              key: item.key,
              label: item.label,
              color: PALETTE[i % PALETTE.length],
              data: history.map((pt) => ({
                time: pt.date,
                value: num(getScoreForLevel(pt, lvl, item.key)),
              })),
            }))
          : [];

        const levelChange = history && history.length >= 2
          ? levelItems.map((item, i) => ({
              key: item.key,
              label: item.label,
              color: PALETTE[i % PALETTE.length],
              data: history.slice(1).map((pt, j) => ({
                time: pt.date,
                value: num(getScoreForLevel(pt, lvl, item.key)) - num(getScoreForLevel(history[j], lvl, item.key)),
              })),
            }))
          : [];

        const levelWeights = getLevelWeights(coefficients, lvl);

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
                      if (it) onDrillDown(it);
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
  );
}
