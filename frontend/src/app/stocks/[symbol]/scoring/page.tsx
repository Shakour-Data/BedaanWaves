"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { cn } from "@/lib/cn";
import { TarotCard } from "@/components/ui/TarotCard";
import { PageLoading } from "@/components/ui/PageLoading";
import { SpiderChart } from "@/components/charts/SpiderChart";
import { ColumnChart } from "@/components/charts/ColumnChart";
import { ScoreTrendChart } from "@/components/charts/ScoreTrendChart";
import { CoefficientChart } from "@/components/charts/CoefficientChart";
import { AsOfStamp } from "@/components/scoring/AsOfStamp";
import { t } from "@/lib/i18n";
import {
  useScoringData,
  LEVEL_LABELS,
  PALETTE,
  DAILY_WINDOW_OPTIONS,
  INTRADAY_WINDOW_OPTIONS,
  type Level,
  type ScoringTab,
  type ViewMode,
} from "./useScoringData";
import { SnapshotReplaySlider } from "./SnapshotReplaySlider";
import { ThreeFrameScoreReference } from "./ThreeFrameScoreReference";
import { ExpertLevelView } from "./ExpertLevelView";

export default function StockScoringPage() {
  const params = useParams<{ symbol: string }>();
  const symbol = decodeURIComponent(
    Array.isArray(params.symbol) ? params.symbol[0] : params.symbol ?? ""
  );

  const d = useScoringData(symbol);

  if (d.loading || d.snapshotLoading) {
    return <PageLoading />;
  }

  if (d.error || !d.hierarchy) {
    return (
      <TarotCard icon="[!]" title={t("app.analysis.scoring_not_found")}>
        <p className="text-sm text-muted-foreground">{d.error || t("app.analysis.scoring_not_found")}</p>
        <Link href={`/stocks/${symbol}`} className="mt-3 inline-block text-sm text-secondary hover:underline">
          ← {t("app.stocks.detail.back_to_list")}
        </Link>
      </TarotCard>
    );
  }

  const showSimpleL1Only = d.viewMode === "SIMPLE";

  return (
    <div className="flex flex-col gap-4">
      {/* Breadcrumb header */}
      <div className="flex items-center justify-between gap-2 text-sm text-muted-foreground">
        <div className="flex items-center gap-2">
          <Link href={`/stocks/${symbol}`} className="hover:text-foreground">
            {symbol}
          </Link>
          <span>/</span>
          <span className="text-foreground">{t("app.scoring.title")}</span>
        </div>
        <AsOfStamp
          timestamp={d.snapshotTimestamp ?? d.hierarchy.timestamp ?? null}
          snapshotId={d.snapshotId ?? null}
          variant="compact"
        />
      </div>

      {/* Tab + window controls */}
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
              aria-selected={d.scoringTab === tab}
              aria-controls={`scoring-panel-${tab}`}
              id={`scoring-tab-${tab}`}
              onClick={() => d.setScoringTab(tab)}
              className={cn(
                "rounded-md px-4 py-1.5 text-sm font-semibold transition",
                d.scoringTab === tab
                  ? "bg-[var(--color-background)] text-[var(--color-primary)] shadow-sm border border-[var(--color-border)]"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              {tab === "HISTORICAL" ? "◷ HISTORICAL" : "⚡ INTRADAY"}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          {d.scoringTab === "HISTORICAL" ? (
            <div className="flex items-center gap-1 rounded-lg bg-[var(--color-neutral)] p-1" role="group" aria-label="Historical window">
              {DAILY_WINDOW_OPTIONS.map((w) => (
                <button
                  key={w}
                  type="button"
                  onClick={() => d.setWindowDaily(w)}
                  className={cn(
                    "rounded-md px-3 py-1 text-xs font-semibold transition",
                    d.windowDaily === w
                      ? "bg-[var(--color-background)] text-[var(--color-primary)] border border-[var(--color-border)] shadow-sm"
                      : "text-muted-foreground hover:text-foreground"
                  )}
                  aria-pressed={d.windowDaily === w}
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
                  onClick={() => d.setWindowIntraday(w)}
                  className={cn(
                    "rounded-md px-3 py-1 text-xs font-semibold transition",
                    d.windowIntraday === w
                      ? "bg-[var(--color-background)] text-[var(--color-primary)] border border-[var(--color-border)] shadow-sm"
                      : "text-muted-foreground hover:text-foreground"
                  )}
                  aria-pressed={d.windowIntraday === w}
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
                onClick={() => d.setViewMode(m)}
                className={cn(
                  "rounded-md px-3 py-1 text-xs font-semibold transition",
                  d.viewMode === m
                    ? "bg-[var(--color-background)] text-[var(--color-primary)] border border-[var(--color-border)] shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                )}
                aria-pressed={d.viewMode === m}
              >
                {m}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Snapshot replay slider */}
      <SnapshotReplaySlider
        entries={d.mergedSnapshotIndex}
        sliderIndex={d.sliderIndex}
        onSliderChange={d.setSliderIndex}
      />

      {/* Three-frame score reference */}
      <ThreeFrameScoreReference
        snapshot={d.snapshot}
        hierarchy={d.hierarchy}
        scoringTab={d.scoringTab}
      />

      {/* Overall score badge */}
      <TarotCard icon="[AN]" title={`${symbol} · ${d.overallScoreText}`}>
        <div className="flex items-center gap-4 flex-wrap">
          <div
            className={cn(
              "text-4xl font-black rounded-full h-24 w-24 flex items-center justify-center border-8 shadow-inner",
              d.hierarchy.overallScore >= 70 ? "text-success border-success/20" : d.hierarchy.overallScore >= 40 ? "text-warning border-warning/20" : "text-error border-error/20"
            )}
            aria-label={`Overall score ${d.hierarchy.overallScore}`}
          >
            {d.hierarchy.overallScore}
          </div>
          <div>
            <div className="text-lg font-bold">{d.hierarchy.grade?.replace("_", " ")}</div>
            <div className="text-xs text-muted-foreground">
              {t("app.scoring.system_title")}
            </div>
          </div>
        </div>
      </TarotCard>

      {/* Drill-down breadcrumb */}
      <div className="flex items-center gap-2 text-sm">
        <button
          type="button"
          onClick={() => d.handleBreadcrumb(1)}
          className={cn(
            "rounded-full px-3 py-1 transition",
            d.drill.level === 1
              ? "bg-primary/10 font-semibold text-primary"
              : "text-muted-foreground hover:bg-neutral"
          )}
        >
          {LEVEL_LABELS[1]}
        </button>
        {d.drill.level >= 2 && d.drill.selectedLabel && (
          <>
            <span className="text-muted-foreground">/</span>
            <button
              type="button"
              onClick={() => d.handleBreadcrumb(2)}
              className={cn(
                "rounded-full px-3 py-1 transition",
                d.drill.level === 2
                  ? "bg-primary/10 font-semibold text-primary"
                  : "text-muted-foreground hover:bg-neutral"
              )}
            >
              {d.drill.selectedLabel}
            </button>
          </>
        )}
        {d.drill.level >= 3 && d.drill.selectedLabel && (
          <>
            <span className="text-muted-foreground">/</span>
            <button
              type="button"
              onClick={() => d.handleBreadcrumb(3)}
              className={cn(
                "rounded-full px-3 py-1 transition",
                d.drill.level === 3
                  ? "bg-primary/10 font-semibold text-primary"
                  : "text-muted-foreground hover:bg-neutral"
              )}
            >
              {d.drill.selectedLabel}
            </button>
          </>
        )}
        {d.drill.level >= 4 && d.drill.selectedLabel && (
          <>
            <span className="text-muted-foreground">/</span>
            <span className="text-foreground">{d.drill.selectedLabel}</span>
          </>
        )}
      </div>

      {/* Main chart panel */}
      <div
        id={`scoring-panel-${d.scoringTab}`}
        role="tabpanel"
        aria-labelledby={`scoring-tab-${d.scoringTab}`}
        className="grid grid-cols-1 gap-4"
      >
        {d.viewMode === "EXPERT" ? (
          <ExpertLevelView
            hierarchy={d.hierarchy}
            history={d.history}
            coefficients={d.coefficients}
            trendWindowLabel={d.trendWindowLabel}
            scoringTabLabel={d.scoringTab}
            onDrillDown={d.handleDrillDown}
          />
        ) : (
          <>
            <TarotCard title={`${LEVEL_LABELS[d.drill.level]} — Spider Chart`}>
              {d.spiderData.length > 0 ? (
                <div className="flex justify-center">
                  <SpiderChart
                    data={d.spiderData}
                    size={360}
                    color={PALETTE[0]}
                    onLabelClick={d.drill.level < 4 ? (label) => {
                      const item = d.itemsForLevel.find((i) => i.label === label);
                      if (item) d.handleDrillDown(item);
                    } : undefined}
                  />
                </div>
              ) : (
                <div className="flex min-h-[240px] items-center justify-center text-muted-foreground">
                  No data available
                </div>
              )}
            </TarotCard>

            {d.l1TrendSeries.length > 0 && d.drill.level === 1 && (
              <TarotCard title={`${LEVEL_LABELS[1]} — Score Trend (${d.trendWindowLabel})`}>
                <ScoreTrendChart showLegend series={d.l1TrendSeries} height={280} />
              </TarotCard>
            )}

            {d.l1ChangeData.length > 0 && d.drill.level === 1 && (
              <TarotCard title={`${LEVEL_LABELS[1]} — Score Changes (${d.scoringTab === "HISTORICAL" ? "Daily" : "Periodic"} Delta)`}>
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {d.l1ChangeData.map((series) => (
                    <div key={series.key} className="rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] p-3">
                      <div className="mb-1 flex items-center gap-2">
                        <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: series.color }} />
                        <span className="text-xs font-medium text-[var(--color-text-secondary)]">{series.label}</span>
                      </div>
                      <ColumnChart data={series.data} height={140} valueFormatter={(v) => (v >= 0 ? "+" : "") + v.toFixed(2)} />
                    </div>
                  ))}
                </div>
              </TarotCard>
            )}

            {d.perStockTrendSeries.length > 0 && d.drill.level > 1 && (
              <TarotCard title={`${LEVEL_LABELS[d.drill.level]} — Score Trend (${d.trendWindowLabel})`}>
                <ScoreTrendChart showLegend series={d.perStockTrendSeries} height={280} />
              </TarotCard>
            )}

            {d.perStockChangeFlat.length > 0 && d.drill.level > 1 && (
              <TarotCard title={`${LEVEL_LABELS[d.drill.level]} — Score Changes (${d.scoringTab === "HISTORICAL" ? "Daily" : "Periodic"} Delta)`}>
                <ColumnChart data={d.perStockChangeFlat} height={220} valueFormatter={(v) => (v >= 0 ? "+" : "") + v.toFixed(2)} />
              </TarotCard>
            )}

            {d.trendSeriesForLevel.length > 0 && d.drill.level > 1 && d.perStockTrendSeries.length === 0 && (
              <TarotCard title={`${LEVEL_LABELS[d.drill.level]} — Score Trend (${d.trendWindowLabel}) — Market`}>
                <ScoreTrendChart showLegend series={d.trendSeriesForLevel} height={280} />
              </TarotCard>
            )}

            {d.changeSeriesForLevel.length > 0 && d.drill.level > 1 && d.perStockChangeSeries.length === 0 && (
              <TarotCard title={`${LEVEL_LABELS[d.drill.level]} — Score Changes (${d.scoringTab === "HISTORICAL" ? "Daily" : "Periodic"} Delta) — Market`}>
                <ColumnChart data={d.changeSeriesForLevel} height={220} valueFormatter={(v) => (v >= 0 ? "+" : "") + v.toFixed(2)} />
              </TarotCard>
            )}

            {d.currentCoefficients.length > 0 && (
              <TarotCard title={`${LEVEL_LABELS[d.drill.level]} — Coefficients (Weights)`}>
                <CoefficientChart
                  data={d.currentCoefficients.map((c) => ({ key: c.key, label: c.label, weight: c.weight }))}
                  height={280}
                />
              </TarotCard>
            )}

            {d.coeffSeriesForLevel.length > 0 && (
              <TarotCard title={`${LEVEL_LABELS[d.drill.level]} — Coefficient Trend (${d.trendWindowLabel})`}>
                <ScoreTrendChart showLegend series={d.coeffSeriesForLevel} height={260} />
              </TarotCard>
            )}

            {d.coeffChangeSeries.length > 0 && (
              <TarotCard title={`${LEVEL_LABELS[d.drill.level]} — Coefficient Changes (${d.scoringTab === "HISTORICAL" ? "Daily" : "Periodic"} Delta)`}>
                <ColumnChart data={d.coeffChangeSeries} height={200} valueFormatter={(v) => (v >= 0 ? "+" : "") + v.toFixed(4)} />
              </TarotCard>
            )}
          </>
        )}
      </div>

      {/* Drill-down item cards */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {d.itemsForLevel.map((item) => (
          <TarotCard
            key={item.key}
            className="cursor-pointer transition hover:border-[var(--color-primary)]/30"
            onClick={() => d.handleDrillDown(item)}
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
