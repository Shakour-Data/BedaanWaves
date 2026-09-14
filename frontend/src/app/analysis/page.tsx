"use client";

import { NewDashboardShell } from "@/components/layout/NewDashboardShell";
import { AssetTable } from "@/components/shared/AssetTable";
import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api";
import {
  fetchFundamental,
  fetchTechnical,
  fetchSentiment,
  fetchScoring,
} from "@/lib/api/stocks";
import type { AssetRow } from "@/lib/dashboard-data";
import { isNasdaqEquityLike } from "@/lib/dashboard-data";
import { cn } from "@/lib/cn";
import { t } from "@/lib/i18n";
import { StatCard, ChangeBadge } from "@/components/shared/StatCard";
import { SpiderChart } from "@/components/charts/SpiderChart";
import { ScoreTrendChart } from "@/components/charts/ScoreTrendChart";
import {
  fetchScoreTrend,
  fetchGeneralDashboard,
  type GeneralDashboardResponse,
} from "@/lib/api/dashboard";
import {
  useLiveData,
  LiveConnectionIndicator,
  type LiveStreamKey,
} from "@/hooks/useLiveData";
import { useDateStore, useSnapshotLoading, useSnapshotError } from "@/store/useDateStore";
import {
  useSnapshot,
  useSnapshotId,
  useSnapshotTimestamp,
} from "@/store/useDateStore";
import { ScoreTripleBadge } from "@/components/scoring/ScoreTripleBadge";
import { AsOfStamp } from "@/components/scoring/AsOfStamp";
import { QK } from "@/lib/query-keys";

interface Performer {
  symbol: string;
  name?: string;
  current_price?: number;
  change_percent?: number;
}

interface SymbolItem {
  symbol: string;
  name: string;
}

interface MarketPulsePayload {
  stats?: Array<{ label: string; value: string; change_pct?: number }>;
  top_movers?: Array<{
    symbol: string;
    name?: string;
    price?: number;
    change_pct?: number;
  }>;
  latest_date?: string;
  overall_trend?: { value: number; direction: "up" | "down" | "flat" };
}

interface ScoresPayload {
  dimensions?: Record<string, number>;
  overall_score?: number;
  grade?: string;
  per_symbol?: Record<
    string,
    { overall_score?: number; dimensions?: Record<string, number>; grade?: string }
  >;
  deltas?: Array<{
    symbol: string;
    overall_score_delta?: number;
    dimensions?: Record<string, number>;
  }>;
}

type Tab = "general" | "technical" | "fundamental" | "scoring" | "sentiment";

export default function AnalysisPage() {
  const [activeTab, setActiveTab] = useState<Tab>("general");
  const [topMovers, setTopMovers] = useState<AssetRow[]>([]);
  const [marketStats, setMarketStats] = useState<Array<{ label: string; value: string; changePct?: number }>>([]);
  const [overallScore, setOverallScore] = useState<number | null>(null);
  const [overallGrade, setOverallGrade] = useState<string | null>(null);
  const [dimensionScores, setDimensionScores] = useState<Record<string, number> | null>(null);
  const [scoreTrend, setScoreTrend] = useState<Array<{ time: string; value: number }>>([]);
  const [analysisData, setAnalysisData] = useState<{
    fundamental?: Record<string, unknown>;
    technical?: unknown;
    sentiment?: {
      label?: string;
      confidence?: number;
      news_count?: number;
    };
    scoring?: {
      overall_score?: number | string;
      grade?: string;
      dimensions?: Record<string, unknown>;
    };
    symbol?: string;
  } | null>(null);

  // Snapshot Zustand integration
  const setLiveLatestFromStream = useDateStore((s) => s.setLiveLatestFromStream);
  const snapshot = useSnapshot();
  const snapshotId = useSnapshotId();
  const snapshotTs = useSnapshotTimestamp();
  const snapLoading = useSnapshotLoading();
  const snapError = useSnapshotError();

  const analysisTabs = useMemo(() => [
    { id: "general" as Tab, label: "GENERAL", icon: "≡" },
    { id: "technical" as Tab, label: t("app.analysis.tabs.technical"), icon: "T" },
    { id: "fundamental" as Tab, label: t("app.analysis.tabs.fundamental"), icon: "F" },
    { id: "scoring" as Tab, label: t("app.analysis.tabs.scoring"), icon: "S" },
    { id: "sentiment" as Tab, label: t("app.analysis.tabs.sentiment"), icon: "N" },
  ], []);

  // ── React Query: REST data fetching ──────────────────────────────
  const performersQ = useQuery<{ data: Performer[] }>({
    queryKey: QK.analysisTopPerformers(10, "1d", "NASDAQ"),
    queryFn: () => apiClient.get<{ data: Performer[] }>(
      "/analysis/top-performers?limit=10&timeframe=1d&market=NASDAQ",
      { timeout: 60000 },
    ).then((r: { data: { data: Performer[] } }) => r.data),
  });

  const symbolsQ = useQuery<{ data: SymbolItem[] }>({
    queryKey: QK.symbols({ market: "NASDAQ", limit: 50 }),
    queryFn: () => apiClient.get<{ data: SymbolItem[] }>(
      "/market/symbols?market=NASDAQ&limit=50",
      { timeout: 60000 },
    ).then((r: { data: { data: SymbolItem[] } }) => r.data),
  });

  const generalQ = useQuery<GeneralDashboardResponse | null>({
    queryKey: QK.dashboardGeneral({ latest: true }),
    queryFn: () => fetchGeneralDashboard({ latest: true }).catch(() => null),
  });

  const trendQ = useQuery<unknown>({
    queryKey: QK.scoreTrend(30, "NASDAQ", { latest: "true" }),
    queryFn: () => fetchScoreTrend(30, "NASDAQ", { latest: true }).catch(() => null),
  });

  const topMoverSymbol = performersQ.data?.data?.[0]?.symbol;

  const topMoverAnalysisQ = useQuery({
    queryKey: ["analysisTopMover", topMoverSymbol],
    queryFn: async () => {
      if (!topMoverSymbol) return null;
      const [fundamental, technical, sentiment, scoring] = await Promise.all([
        fetchFundamental(topMoverSymbol).catch(() => undefined),
        fetchTechnical(topMoverSymbol).catch(() => undefined),
        fetchSentiment(topMoverSymbol).catch(() => undefined),
        fetchScoring(topMoverSymbol).catch(() => undefined),
      ]);
      return {
        fundamental: fundamental ?? undefined,
        technical: technical ?? undefined,
        sentiment: sentiment ?? undefined,
        scoring: scoring ?? undefined,
        symbol: topMoverSymbol,
      };
    },
    enabled: !!topMoverSymbol,
  });

  const coreLoading = performersQ.isLoading || symbolsQ.isLoading || generalQ.isLoading || trendQ.isLoading;
  const hasAnyData = topMovers.length > 0 || marketStats.length > 0 || !!snapshot;
  const loading = coreLoading && !hasAnyData;

  // ── Sync: snapshot data → local state ────────────────────────────
  useEffect(() => {
    if (!snapshot) return;

    const currentDims = snapshot.scores?.current?.dimension ?? {};
    if (Object.keys(currentDims).length > 0) {
      setDimensionScores(currentDims);
    }
    if (typeof snapshot.scores?.current?.overall === "number") {
      setOverallScore(snapshot.scores.current.overall);
    }
    if (Array.isArray(snapshot.trends?.daily) && snapshot.trends.daily.length > 0) {
      setScoreTrend(
        snapshot.trends.daily.map((p) => ({
          time: p.date,
          value: typeof p.overall === "number" ? p.overall : NaN,
        })).filter((p) => Number.isFinite(p.value)),
      );
    }

    const snapshotSymbolCount = snapshot.scores?.current?.symbol_map
      ? Object.keys(snapshot.scores.current.symbol_map).length
      : null;

    const topFromSnap = (() => {
      if (!snapshot.scores?.current?.symbol_map) return null;
      const entries = Object.entries(snapshot.scores.current.symbol_map);
      entries.sort((a, b) => (b[1].overall ?? -Infinity) - (a[1].overall ?? -Infinity));
      return entries.length ? entries[0] : null;
    })();
    const bottomFromSnap = (() => {
      if (!snapshot.scores?.current?.symbol_map) return null;
      const entries = Object.entries(snapshot.scores.current.symbol_map);
      entries.sort((a, b) => (a[1].overall ?? Infinity) - (b[1].overall ?? Infinity));
      return entries.length ? entries[0] : null;
    })();

    const statsFromSnap: typeof marketStats = [];
    statsFromSnap.push({
      label: "Active Symbols",
      value: (snapshotSymbolCount ?? generalQ.data?.summary?.total_symbols ?? 0).toLocaleString("en-US"),
      changePct: 0,
    });
    if (topFromSnap) {
      const [sym, d] = topFromSnap;
      statsFromSnap.push({
        label: "Top Scorer",
        value: `${sym} ${typeof d.overall === "number" ? d.overall.toFixed(1) : "0"}`,
        changePct: 0,
      });
    } else if (generalQ.data?.top_performers?.[0]) {
      const top = generalQ.data.top_performers[0];
      statsFromSnap.push({
        label: "Top Scorer",
        value: `${top.symbol} ${typeof top.overall_score === "number" ? top.overall_score.toFixed(1) : "0"}`,
        changePct: 0,
      });
    }
    if (bottomFromSnap) {
      const [sym, d] = bottomFromSnap;
      statsFromSnap.push({
        label: "Lowest Scorer",
        value: `${sym} ${typeof d.overall === "number" ? d.overall.toFixed(1) : "0"}`,
        changePct: 0,
      });
    } else if (generalQ.data?.bottom_performers?.[0]) {
      const bottom = generalQ.data.bottom_performers[0];
      statsFromSnap.push({
        label: "Lowest Scorer",
        value: `${bottom.symbol} ${typeof bottom.overall_score === "number" ? bottom.overall_score.toFixed(1) : "0"}`,
        changePct: 0,
      });
    }
    if (statsFromSnap.length > 0) setMarketStats(statsFromSnap);
    if (snapshot.timestamp) setLiveLatestFromStream(snapshot.timestamp);
  }, [snapshot, generalQ.data, setLiveLatestFromStream]);

  // ── Sync: legacy fallback (when no snapshot) ─────────────────────
  useEffect(() => {
    if (snapshot) return;
    const generalRes = generalQ.data;
    const trendRes = trendQ.data as { status?: string; series?: Array<{ date: string; avg_score: number }> } | null;

    if (generalRes?.status === "success") {
      const top = generalRes.top_performers?.[0];
      const bottom = generalRes.bottom_performers?.[0];
      const totalSymbols = generalRes.summary?.total_symbols ?? 0;
      setMarketStats([
        { label: "Active Symbols", value: totalSymbols.toLocaleString("en-US"), changePct: 0 },
        {
          label: "Top Scorer",
          value: top ? `${top.symbol} ${typeof top.overall_score === "number" ? top.overall_score.toFixed(1) : "0"}` : "—",
          changePct: 0,
        },
        {
          label: "Lowest Scorer",
          value: bottom ? `${bottom.symbol} ${typeof bottom.overall_score === "number" ? bottom.overall_score.toFixed(1) : "0"}` : "—",
          changePct: 0,
        },
      ]);

      const dims: Record<string, number> = {};
      if (generalRes.dimensions) {
        Object.entries(generalRes.dimensions).forEach(([k, v]) => {
          const val = v as { avg_score?: number } | null;
          if (val && typeof val.avg_score === "number") dims[k] = val.avg_score;
        });
      }
      if (Object.keys(dims).length > 0) setDimensionScores(dims);
      if (generalRes.latest_date) setLiveLatestFromStream(generalRes.latest_date);
    }

    if (trendRes?.status === "success" && trendRes.series) {
      setScoreTrend(trendRes.series.map((p) => ({ time: p.date, value: p.avg_score })));
    }
  }, [snapshot, generalQ.data, trendQ.data, setLiveLatestFromStream]);

  // ── Sync: top movers from performers query ───────────────────────
  useEffect(() => {
    const performers = performersQ.data?.data;
    const symbols = symbolsQ.data?.data;
    if (!performers || !symbols) return;

    const symbolMap = new Map(symbols.map((s) => [s.symbol, s.name]));
    const movers: AssetRow[] = performers
      .filter((p) => isNasdaqEquityLike({ symbol: p.symbol }))
      .map((p) => ({
        symbol: p.symbol,
        name: symbolMap.get(p.symbol) || p.name || "",
        market: "NASDAQ" as const,
        price: p.current_price ?? 0,
        changePct: p.change_percent ?? 0,
      }));
    setTopMovers(movers.slice(0, 10));
  }, [performersQ.data, symbolsQ.data]);

  // ── Sync: top mover analysis ─────────────────────────────────────
  useEffect(() => {
    if (topMoverAnalysisQ.data) {
      setAnalysisData(topMoverAnalysisQ.data);
    }
  }, [topMoverAnalysisQ.data]);

  const liveMarket = useLiveData<MarketPulsePayload>("market" as LiveStreamKey, {
    onData: (data) => {
      if (data?.latest_date) {
        setLiveLatestFromStream(data.latest_date);
      }
      if (data?.stats && data.stats.length > 0) {
        setMarketStats(data.stats.map((s) => ({
          label: s.label,
          value: s.value,
          changePct: s.change_pct,
        })));
      }
      if (data?.top_movers && data.top_movers.length > 0) {
        const movers: AssetRow[] = data.top_movers
          .filter((m) => isNasdaqEquityLike({ symbol: m.symbol }))
          .map((m) => ({
            symbol: m.symbol,
            name: m.name ?? "",
            market: "NASDAQ" as const,
            price: m.price ?? 0,
            changePct: m.change_pct ?? 0,
          }));
        if (movers.length > 0) {
          setTopMovers((prev) => {
            if (prev.length === 0) return movers;
            const bySymbol = new Map(prev.map((p) => [p.symbol, p]));
            movers.forEach((m) => bySymbol.set(m.symbol, { ...bySymbol.get(m.symbol), ...m }));
            return Array.from(bySymbol.values()).slice(0, 10);
          });
        }
      }
    },
  });

  const liveScores = useLiveData<ScoresPayload>("scores" as LiveStreamKey, {
    onData: (data) => {
      if (typeof data?.overall_score === "number") {
        setOverallScore(data.overall_score);
      }
      if (data?.grade) {
        setOverallGrade(data.grade);
      }
      if (data?.dimensions) {
        setDimensionScores((prev) => ({ ...prev, ...data.dimensions }));
      }
    },
  });

  const lastMarketEventTs =
    liveMarket.data === liveMarket.latest
      ? null
      : null;
  const lastScoresEventTs =
    liveScores.data === liveScores.latest ? null : null;

  if (loading) {
    return (
      <NewDashboardShell title={t("app.analysis.title")}>
        <div className="flex min-h-[40vh] items-center justify-center text-muted-foreground">
          {t("app.analysis.loading")}
        </div>
      </NewDashboardShell>
    );
  }

  return (
    <NewDashboardShell title={t("app.analysis.title")}>
      <div className="flex flex-col gap-6 animate-in fade-in duration-500">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="flex-1">
            <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">
              {t("app.analysis.title")}
            </h1>
            <div className="mt-2">
              <AsOfStamp
                timestamp={snapshotTs ?? null}
                snapshotId={snapshotId ?? null}
                loading={snapLoading}
                error={snapError ?? null}
                variant="emphasis"
              />
            </div>
            {overallScore !== null && activeTab !== "general" && (
              <div className="mt-2 flex items-center gap-3">
                <span className="text-sm text-[var(--color-text-secondary)]">
                  Overall Market Score
                </span>
                <span
                  className={cn(
                    "rounded-full px-3 py-1 text-lg font-bold",
                    overallScore >= 70
                      ? "bg-success/15 text-success"
                      : overallScore >= 40
                        ? "bg-warning/15 text-warning"
                        : "bg-error/15 text-error",
                  )}
                >
                  {overallScore.toFixed(0)}
                  {overallGrade ? ` · ${overallGrade.replace(/_/g, " ")}` : ""}
                </span>
              </div>
            )}
          </div>
          <div className="flex flex-wrap gap-2">
            <LiveConnectionIndicator
              health={liveMarket.connectionHealth}
              dataAgeMs={liveMarket.lastDataAgeMs}
              lastEventTs={lastMarketEventTs}
              label="Market"
            />
            <LiveConnectionIndicator
              health={liveScores.connectionHealth}
              dataAgeMs={liveScores.lastDataAgeMs}
              lastEventTs={lastScoresEventTs}
              label="Scores"
            />
          </div>
        </div>

        {activeTab === "general" && snapshot && (
          <section className="flex flex-col gap-4 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-base font-semibold text-[var(--color-text-primary)]">
                  THREE-FRAME SCORE REFERENCE
                </h2>
                <p className="mt-0.5 text-xs text-[var(--color-text-secondary)]">
                  PREV DAY (00:00 UTC) · PREV HOUR · CURRENT LIVE · source snapshot #{snapshotId?.slice(0, 8) ?? "—"}
                </p>
              </div>
              {overallScore !== null && (
                <span
                  className={cn(
                    "rounded-full px-3 py-1 text-lg font-bold",
                    overallScore >= 70
                      ? "bg-[var(--color-success)]/15 text-[var(--color-success)]"
                      : overallScore >= 40
                        ? "bg-[var(--color-warning)]/15 text-[var(--color-warning)]"
                        : "bg-[var(--color-error)]/15 text-[var(--color-error)]",
                  )}
                >
                  {overallScore.toFixed(0)}
                  {overallGrade ? ` · ${overallGrade.replace(/_/g, " ")}` : ""}
                </span>
              )}
            </div>
            <ScoreTripleBadge
              scores={snapshot.scores}
              deltas={snapshot.deltas}
              showDailyDelta
              size="md"
            />
          </section>
        )}

        {activeTab === "general" && !snapshot && (
          <section className="rounded-2xl border border-dashed border-[var(--color-border)] p-6 text-center shadow-sm">
            <p className="text-sm font-semibold text-[var(--color-text-secondary)]">
              Unified snapshot not loaded yet
            </p>
            <p className="mt-1 text-xs text-[var(--color-text-secondary)]/80">
              Legacy fallback feeds power the dashboard below. Reload once the
              scheduler has produced the first hourly snapshot.
            </p>
          </section>
        )}

        {marketStats.length > 0 ? (
          <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {marketStats.map((stat, i) => (
              <StatCard key={i} stat={stat} />
            ))}
          </section>
        ) : null}

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          {dimensionScores && Object.keys(dimensionScores).length > 0 ? (
            <section className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm lg:col-span-1">
              <div className="mb-3 flex items-center justify-between">
                <h3 className="font-semibold text-[var(--color-text-primary)]">
                  Score Spider
                </h3>
                <LiveConnectionIndicator
                  health={liveScores.connectionHealth}
                  dataAgeMs={liveScores.lastDataAgeMs}
                  lastEventTs={lastScoresEventTs}
                />
              </div>
              <SpiderChart
                data={Object.entries(dimensionScores).map(([name, score]) => ({
                  label: name.charAt(0).toUpperCase() + name.slice(1),
                  value: score,
                }))}
                size={320}
              />
            </section>
          ) : null}

          {scoreTrend.length > 0 ? (
            <section className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm lg:col-span-2">
              <div className="mb-3 flex items-center justify-between">
                <h3 className="font-semibold text-[var(--color-text-primary)]">
                  30-Day Market Score Trend
                </h3>
                <span className="text-xs text-[var(--color-text-secondary)]">
                  Historical REST · chart kept from initial load
                </span>
              </div>
              <ScoreTrendChart series={[{ key: 'score', label: 'Market Score', color: '#2563EB', data: scoreTrend }]} height={320} />
            </section>
          ) : null}
        </div>

        <div className="flex gap-2 overflow-x-auto pb-2">
          {analysisTabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                "inline-flex items-center gap-2 rounded-xl border px-4 py-2.5 text-sm font-semibold transition-all whitespace-nowrap",
                activeTab === tab.id
                  ? "border-[var(--color-primary)] bg-[var(--color-primary)] text-white shadow-lg shadow-[var(--color-primary)]/20"
                  : "border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text-secondary)] hover:border-[var(--color-primary)]/30 hover:text-[var(--color-text-primary)]"
              )}
            >
              <span>{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>

        <section className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
          <div className="mb-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--color-primary-soft)] text-[var(--color-primary)]">
                <span className="text-lg font-mono text-sm font-bold tracking-tight">[MO]</span>
              </div>
              <div>
                <h3 className="font-semibold text-[var(--color-text-primary)]">
                  {t("app.analysis.top_movers")}
                </h3>
                <p className="text-xs text-[var(--color-text-muted)]">
                  Top performing stocks · live patches applied
                </p>
              </div>
            </div>
            <LiveConnectionIndicator
              health={liveMarket.connectionHealth}
              dataAgeMs={liveMarket.lastDataAgeMs}
              lastEventTs={lastMarketEventTs}
            />
          </div>
          {topMovers.length > 0 ? (
            <AssetTable rows={topMovers} />
          ) : (
            <p className="text-[var(--color-text-muted)] py-8 text-center text-sm">
              {t("app.analysis.no_data")}
            </p>
          )}
        </section>

        {activeTab === "technical" && (
          <section className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
            <div className="flex items-center gap-3 mb-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--color-primary-soft)] text-[var(--color-primary)]">
                <span className="text-lg font-mono text-sm font-bold tracking-tight">[TR]</span>
              </div>
              <div>
                <h3 className="font-semibold text-[var(--color-text-primary)]">
                  {t("app.analysis.technical_charts")}
                </h3>
                <p className="text-xs text-[var(--color-text-muted)]">
                  Technical indicators for top movers
                </p>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {topMovers.slice(0, 3).map((mover, i) => (
                <div
                  key={i}
                  className="group rounded-xl border border-[var(--color-border)] bg-[var(--color-background)]/50 p-5 transition-all hover:border-[var(--color-primary)]/30 hover:shadow-md"
                >
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <div className="font-bold text-lg text-[var(--color-text-primary)]">
                        {mover.symbol}
                      </div>
                      <div className="text-xs text-[var(--color-text-muted)]">
                        {mover.name}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-bold tabular-nums text-[var(--color-text-primary)]">
                        ${mover.price > 0 ? mover.price.toFixed(2) : "—"}
                      </div>
                      <div
                        className={cn(
                          "text-sm font-semibold",
                          mover.changePct >= 0
                            ? "text-[var(--color-success)]"
                            : "text-[var(--color-error)]"
                        )}
                      >
                        {mover.changePct >= 0 ? "+" : ""}
                        {mover.changePct.toFixed(2)}%
                      </div>
                    </div>
                  </div>
                  <div className="h-16 rounded-lg bg-[var(--color-border)]/30 flex items-end gap-1 p-2">
                    {Array.from({ length: 12 }).map((_, j) => (
                      <div
                        key={j}
                        className="flex-1 rounded bg-[var(--color-primary)]/60 hover:bg-[var(--color-primary)] transition-colors"
                        style={{
                          height: `${30 + ((i * 7 + j * 11) % 70)}%`,
                        }}
                      />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {activeTab === "fundamental" && (
          <section className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
            <div className="flex items-center gap-3 mb-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--color-primary-soft)] text-[var(--color-primary)]">
                <span className="text-lg font-mono text-sm font-bold tracking-tight">[FU]</span>
              </div>
              <div>
                <h3 className="font-semibold text-[var(--color-text-primary)]">
                  {t("app.analysis.fundamental_indicators").replace(
                    "{symbol}",
                    analysisData?.symbol || ""
                  )}
                </h3>
                <p className="text-xs text-[var(--color-text-muted)]">
                  Key fundamental metrics
                </p>
              </div>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {Object.entries(analysisData?.fundamental || {})
                .slice(0, 8)
                .map(([key, value]: [string, unknown], i) => (
                  <div
                    key={i}
                    className="rounded-xl border border-[var(--color-border)] bg-[var(--color-background)]/50 p-4 text-center"
                  >
                    <div className="text-xs text-[var(--color-text-muted)] uppercase tracking-wider">
                      {key.replace(/_/g, " ")}
                    </div>
                    <div className="text-sm font-bold mt-1 text-[var(--color-text-primary)]">
                      {typeof value === "number"
                        ? value.toLocaleString("en-US")
                        : typeof value === "string"
                        ? value
                        : "—"}
                    </div>
                  </div>
                ))}
              {(!analysisData?.fundamental ||
                Object.keys(analysisData.fundamental).length === 0) && (
                <div className="col-span-full py-8 text-center text-[var(--color-text-muted)] text-sm">
                  {t("app.analysis.fundamental_not_found")}
                </div>
              )}
            </div>
          </section>
        )}

        {activeTab === "scoring" && (
          <section className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--color-primary-soft)] text-[var(--color-primary)]">
                  <span className="text-lg font-mono text-sm font-bold tracking-tight">[SC]</span>
                </div>
                <div>
                  <h3 className="font-semibold text-[var(--color-text-primary)]">
                    {`${t("app.nav.scoring")} (${analysisData?.symbol || ""})`}
                  </h3>
                  <p className="text-xs text-[var(--color-text-muted)]">
                    AI-powered stock scoring
                  </p>
                </div>
              </div>
              <LiveConnectionIndicator
                health={liveScores.connectionHealth}
                dataAgeMs={liveScores.lastDataAgeMs}
                lastEventTs={lastScoresEventTs}
              />
            </div>
            {analysisData?.scoring ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between rounded-xl border border-[var(--color-border)] bg-[var(--color-background)]/50 p-5">
                  <div>
                    <div className="text-xs text-[var(--color-text-muted)]">
                      {t("app.analysis.overall_score")}
                    </div>
                    <div className="text-3xl font-bold bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-accent)] bg-clip-text text-transparent">
                      {typeof analysisData.scoring.overall_score === "number"
                        ? analysisData.scoring.overall_score.toLocaleString("en-US")
                        : String(analysisData.scoring.overall_score ?? "—")}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs text-[var(--color-text-muted)]">
                      {t("app.analysis.grade")}
                    </div>
                    <div className="text-2xl font-bold text-[var(--color-text-primary)]">
                      {analysisData.scoring.grade}
                    </div>
                  </div>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {Object.entries(analysisData.scoring.dimensions || {}).map(
                    ([dim, score]: [string, unknown], i) => {
                      const numericScore = typeof score === "number" ? score : Number(score) || 0;
                      return (
                        <div
                          key={i}
                          className="rounded-xl border border-[var(--color-border)] bg-[var(--color-background)]/30 p-3"
                        >
                          <div className="text-xs text-[var(--color-text-muted)] capitalize">
                            {t(`app.scoring.dimensions.${dim.toLowerCase()}`)}
                          </div>
                          <div className="flex items-center justify-between mt-1">
                            <span className="font-bold text-lg text-[var(--color-text-primary)]">
                              {numericScore.toLocaleString("en-US")}
                            </span>
                            <div className="h-1.5 flex-1 mx-2 bg-border rounded-full overflow-hidden">
                              <div
                                className={cn(
                                  "h-full rounded-full",
                                  numericScore >= 70
                                    ? "bg-green-600"
                                    : numericScore >= 40
                                    ? "bg-yellow-500"
                                    : "bg-red-600"
                                )}
                                style={{ width: `${Math.max(0, Math.min(100, numericScore))}%` }}
                              />
                            </div>
                          </div>
                        </div>
                      );
                    }
                  )}
                </div>
              </div>
            ) : (
              <p className="text-[var(--color-text-muted)] py-8 text-center text-sm">
                {t("app.analysis.scoring_not_found")}
              </p>
            )}
          </section>
        )}

        {activeTab === "sentiment" && (
          <section className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
            <div className="flex items-center gap-3 mb-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--color-primary-soft)] text-[var(--color-primary)]">
                <span className="text-lg font-mono text-sm font-bold tracking-tight">[SE]</span>
              </div>
              <div>
                <h3 className="font-semibold text-[var(--color-text-primary)]">
                  {t("app.analysis.sentiment_title").replace(
                    "{symbol}",
                    analysisData?.symbol || ""
                  )}
                </h3>
                <p className="text-xs text-[var(--color-text-muted)]">
                  Market sentiment analysis
                </p>
              </div>
            </div>
            {analysisData?.sentiment ? (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {[
                  {
                    label: t("app.analysis.sentiment_labels.overall"),
                    value: t(
                      `app.analysis.sentiment_values.${String(
                        analysisData.sentiment.label || "neutral"
                      ).toLowerCase()}`
                    ),
                    score: analysisData.sentiment.confidence ?? null,
                    color:
                      analysisData.sentiment.label === "positive"
                        ? "text-[var(--color-success)]"
                        : analysisData.sentiment.label === "negative"
                        ? "text-[var(--color-error)]"
                        : "text-[var(--color-text-muted)]",
                  },
                  {
                    label: t("app.analysis.sentiment_labels.news_count"),
                    value: t("app.analysis.sentiment_values.news_items").replace(
                      "{count}",
                      String(analysisData.sentiment.news_count ?? 0)
                    ),
                    score: null,
                    color: "text-[var(--color-text-primary)]",
                  },
                  {
                    label: t("app.analysis.sentiment_labels.confidence"),
                    value: `${Math.round((analysisData.sentiment.confidence ?? 0) * 100)}%`,
                    score: null,
                    color: "text-[var(--color-primary)]",
                  },
                ].map((sentiment, i) => (
                  <div
                    key={i}
                    className="rounded-xl border border-[var(--color-border)] bg-[var(--color-background)]/50 p-6 text-center"
                  >
                    <div className="text-xs text-[var(--color-text-muted)]">
                      {sentiment.label}
                    </div>
                    <div className={`text-lg font-bold mt-2 ${sentiment.color}`}>
                      {sentiment.value}
                    </div>
                    {typeof sentiment.score === "number" && (
                      <ChangeBadge value={sentiment.score * 100} className="mt-2" />
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-[var(--color-text-muted)] py-8 text-center text-sm">
                {t("app.analysis.sentiment_not_found")}
              </p>
            )}
          </section>
        )}
      </div>
    </NewDashboardShell>
  );
}
