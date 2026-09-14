"use client";

import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useParams } from "next/navigation";
import { cn } from "@/lib/cn";
import { TarotCard } from "@/components/ui/TarotCard";
import { ChangeBadge } from "@/components/shared/StatCard";
import { StockDetailSkeleton } from "@/components/ux/SkeletonLoaders";
import {
  fetchAsset,
  fetchPriceHistory,
  fetchLatestPrice,
  fetchScoring,
  fetchFundamental,
  fetchRisk,
  type Asset,
  type Candle,
  type LatestPrice,
  type ScoringResponse,
  type FundamentalResponse,
  type RiskResponse,
} from "@/lib/api/stocks";
import { t } from "@/lib/i18n";
import {
  useLiveData,
  LiveConnectionIndicator,
  type LiveStreamKey,
} from "@/hooks/useLiveData";
import { QK } from "@/lib/query-keys";
import { OverviewTab } from "./OverviewTab";
import { RiskTab } from "./RiskTab";
import { HistoryTab } from "./HistoryTab";
import type {
  QuotePayload,
  IntradayBar,
  IntradayPayload,
  ScoreDelta,
  ScoringData,
  RiskData,
  FundamentalData,
} from "./types";

type Tab = "overview" | "risk" | "history";

export default function StockDetailPage() {
  const params = useParams<{ symbol: string }>();
  const symbol = decodeURIComponent(
    Array.isArray(params.symbol) ? params.symbol[0] : params.symbol ?? ""
  );

  const [activeTab, setActiveTab] = useState<Tab>("overview");
  const [asset, setAsset] = useState<Asset | null>(null);
  const [candles, setCandles] = useState<Candle[] | null>(null);
  const [intradayBars, setIntradayBars] = useState<IntradayBar[]>([]);
  const [latest, setLatest] = useState<LatestPrice | null>(null);
  const [scoring, setScoring] = useState<ScoringData | null>(null);
  const [fundamental, setFundamental] = useState<FundamentalData | null>(null);
  const [risk, setRisk] = useState<RiskData | null>(null);
  const [range, setRange] = useState<string>("90");

  const candlesQ = useQuery<Candle[]>({
    queryKey: QK.priceHistory(symbol, "1d", 500),
    queryFn: () => fetchPriceHistory({ symbol, timeframe: "1d", limit: 500 }),
    enabled: !!symbol,
  });

  const assetQ = useQuery<Asset | null>({
    queryKey: QK.symbols({ symbol }),
    queryFn: () => fetchAsset(symbol),
    enabled: !!symbol,
  });

  const latestQ = useQuery<LatestPrice | null>({
    queryKey: QK.latestPrices([symbol]),
    queryFn: () => fetchLatestPrice(symbol),
    enabled: !!symbol,
  });

  const scoringQ = useQuery<ScoringResponse | null>({
    queryKey: QK.scoring(symbol),
    queryFn: () => fetchScoring(symbol),
    enabled: !!symbol,
  });

  const riskQ = useQuery<RiskResponse | null>({
    queryKey: QK.risk(symbol),
    queryFn: () => fetchRisk(symbol),
    enabled: !!symbol && activeTab === "risk",
  });

  const fundamentalQ = useQuery<FundamentalResponse | null>({
    queryKey: QK.fundamental(symbol),
    queryFn: () => fetchFundamental(symbol),
    enabled: !!symbol && activeTab === "risk",
  });

  const coreLoading = candlesQ.isLoading || assetQ.isLoading || latestQ.isLoading || scoringQ.isLoading;
  const hasData = candles !== null || asset !== null;
  const loading = coreLoading && !hasData;

  const coreError = candlesQ.error || assetQ.error || latestQ.error || scoringQ.error;
  const error = coreError && !hasData
    ? (coreError instanceof Error ? coreError.message : t("app.stocks.detail.error_title"))
    : null;

  useEffect(() => { if (candlesQ.data) setCandles(candlesQ.data); }, [candlesQ.data]);
  useEffect(() => { if (assetQ.data !== undefined) setAsset(assetQ.data); }, [assetQ.data]);
  useEffect(() => { if (latestQ.data !== undefined) setLatest(latestQ.data); }, [latestQ.data]);
  useEffect(() => { if (scoringQ.data) setScoring(scoringQ.data as unknown as ScoringData); }, [scoringQ.data]);
  useEffect(() => { if (riskQ.data) setRisk(riskQ.data as unknown as RiskData); }, [riskQ.data]);
  useEffect(() => { if (fundamentalQ.data) setFundamental(fundamentalQ.data as unknown as FundamentalData); }, [fundamentalQ.data]);

  const intradayKey = `intraday:${symbol}:5m` as LiveStreamKey;
  const quoteKey = `quote:${symbol}` as LiveStreamKey;

  const liveQuote = useLiveData<QuotePayload>(quoteKey, {
    onData: (data) => {
      if (!data) return;
      setLatest((prev) => {
        const next: LatestPrice = {
          symbol: data.symbol ?? symbol,
          price: data.price ?? prev?.price ?? 0,
          change: data.change ?? prev?.change ?? 0,
          change_pct: data.change_pct ?? prev?.change_pct ?? 0,
          volume: data.volume ?? prev?.volume ?? 0,
          timestamp: data.freshness_ts ?? new Date().toISOString(),
        };
        return next;
      });
    },
  });

  const liveIntraday = useLiveData<IntradayPayload>(intradayKey, {
    onData: (data) => {
      if (data?.bar) {
        setIntradayBars((prev) => {
          const next = [...prev, data.bar!];
          const deduped = next.reduce<IntradayBar[]>((acc, b) => {
            if (acc.length === 0 || acc[acc.length - 1].time !== b.time) {
              acc.push(b);
            } else {
              acc[acc.length - 1] = b;
            }
            return acc;
          }, []);
          return deduped.slice(-60);
        });
      } else if (data?.bars && data.bars.length > 0) {
        setIntradayBars(data.bars.slice(-60));
      }
    },
  });

  const liveScores = useLiveData<{
    per_symbol?: Record<string, ScoreDelta>;
    deltas?: Array<ScoreDelta & { symbol: string }>;
  }>("scores" as LiveStreamKey, {
    onData: (data) => {
      const symUp = symbol?.toUpperCase();
      let mine: ScoreDelta | undefined;
      if (data?.per_symbol && symUp) {
        mine = Object.entries(data.per_symbol).find(
          ([k]) => k.toUpperCase() === symUp
        )?.[1];
      }
      if (!mine && data?.deltas && symUp) {
        mine = data.deltas.find((d) => d.symbol?.toUpperCase() === symUp);
      }
      if (mine) {
        setScoring((prev) => {
          const dimensions = { ...((prev?.dimension_scores as Record<string, number>) || {}) };
          if (mine?.dimensions) {
            Object.assign(dimensions, mine.dimensions);
          }
          return {
            ...(prev || {}),
            overall_score:
              typeof mine?.overall_score === "number"
                ? mine.overall_score
                : prev?.overall_score,
            grade: mine?.grade ?? prev?.grade,
            dimension_scores: dimensions,
          };
        });
      }
    },
  });

  const RANGES = useMemo(
    () => [
      { key: "30", label: t("app.stocks.detail.ranges.1m"), days: 30 },
      { key: "90", label: t("app.stocks.detail.ranges.3m"), days: 90 },
      { key: "all", label: t("app.stocks.detail.ranges.all"), days: null },
    ],
    []
  );

  const visibleCandles = useMemo(() => {
    if (!candles) return [];
    const cfg = RANGES.find((r) => r.key === range);
    if (!cfg || cfg.days === null) return candles;
    return candles.slice(-cfg.days);
  }, [candles, range, RANGES]);

  const derived = useMemo(() => {
    if (!candles || candles.length === 0) return null;
    const last = candles[candles.length - 1];
    const prev = candles.length >= 2 ? candles[candles.length - 2] : null;
    const change = prev ? last.close - prev.close : last.close - last.open;
    const base = prev ? prev.close : last.open;
    const changePct = base ? (change / base) * 100 : 0;
    const highs = visibleCandles.map((c) => c.high);
    const lows = visibleCandles.map((c) => c.low);
    const avgVol =
      visibleCandles.reduce((s, c) => s + c.volume, 0) /
      (visibleCandles.length || 1);
    return {
      price: last.close,
      change,
      changePct,
      rangeHigh: highs.length ? Math.max(...highs) : last.high,
      rangeLow: lows.length ? Math.min(...lows) : last.low,
      lastVolume: last.volume,
      avgVol,
    };
  }, [candles, visibleCandles]);

  const livePrice = latest?.price ?? derived?.price ?? 0;
  const liveChangePct = latest?.change_pct ?? derived?.changePct ?? 0;
  const currency = t("app.stocks.detail.currency_usd");

  const chartBarsForWindow: Candle[] = useMemo(() => {
    if (intradayBars.length > 0) {
      return intradayBars.map((b) => ({
        timestamp: b.time,
        timeframe: "5m",
        open: b.open,
        high: b.high,
        low: b.low,
        close: b.close,
        volume: b.volume ?? 0,
        turnover: null,
        transactions: null,
      }));
    }
    return visibleCandles.slice(-60);
  }, [intradayBars, visibleCandles]);

  const tabs: { key: Tab; label: string }[] = [
    { key: "overview", label: "Overview" },
    { key: "risk", label: "Risk" },
    { key: "history", label: "Historical Data" },
  ];

  if (loading) {
    return <StockDetailSkeleton />;
  }

  if (error) {
    return (
      <TarotCard icon="⚠️" title={t("app.stocks.detail.error_title")}>
        <p className="text-sm text-muted-foreground">
          {t("app.stocks.detail.error_desc").replace("{symbol}", symbol)}
        </p>
        <p className="mt-2 text-xs text-error">{error}</p>
        <Link
          href="/stocks"
          className="mt-3 inline-block text-sm text-secondary hover:underline"
        >
          ← {t("app.stocks.detail.back_to_list")}
        </Link>
      </TarotCard>
    );
  }

  return (
    <div className="flex flex-col gap-4 animate-in fade-in duration-300">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Link href="/stocks" className="hover:text-foreground">
          {t("app.nav.stocks")}
        </Link>
        <span>/</span>
        <span className="text-foreground">{symbol}</span>
      </div>

      <TarotCard>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="flex flex-col gap-1">
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold">{symbol}</h1>
              {asset ? (
                <span className="rounded-full bg-neutral/70 px-2 py-0.5 text-xs text-muted-foreground">
                  {t(`app.stocks.markets.${asset.market.toLowerCase()}`)}
                </span>
              ) : null}
            </div>
            {asset ? <span className="text-muted-foreground">{asset.name}</span> : null}
            {asset?.sector ? (
              <span className="text-xs text-muted-foreground">
                {t("app.stocks.sector")}: {asset.sector}
              </span>
            ) : null}
          </div>
          <div className="flex flex-col items-end gap-1">
            <span className="text-2xl font-bold tabular-nums">
              {livePrice.toLocaleString("en-US", { maximumFractionDigits: 2 })}
            </span>
            <div className="flex items-center gap-2">
              <ChangeBadge value={liveChangePct} />
              <span className="text-xs text-muted-foreground">{currency}</span>
              <LiveConnectionIndicator
                health={liveQuote.connectionHealth}
                dataAgeMs={liveQuote.lastDataAgeMs}
                lastEventTs={null}
              />
            </div>
          </div>
        </div>
      </TarotCard>

      <div className="flex items-center gap-1 border-b border-[var(--color-border)]">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            type="button"
            onClick={() => setActiveTab(tab.key)}
            className={cn(
              "relative rounded-t-lg px-4 py-2.5 text-sm font-medium transition-colors",
              activeTab === tab.key
                ? "text-[var(--color-primary)]"
                : "text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]"
            )}
            role="tab"
            aria-selected={activeTab === tab.key}
          >
            {tab.label}
            {activeTab === tab.key && (
              <span className="absolute inset-x-0 -bottom-px h-0.5 rounded-t-full bg-[var(--color-primary)]" />
            )}
          </button>
        ))}
      </div>

      {activeTab === "overview" && (
        <OverviewTab
          symbol={symbol}
          asset={asset}
          candles={candles}
          intradayBars={intradayBars}
          latest={latest}
          scoring={scoring}
          visibleCandles={visibleCandles}
          chartBarsForWindow={chartBarsForWindow}
          derived={derived}
          livePrice={livePrice}
          liveChangePct={liveChangePct}
          currency={currency}
          range={range}
          ranges={RANGES}
          liveQuoteHealth={liveQuote.connectionHealth}
          liveQuoteAgeMs={liveQuote.lastDataAgeMs}
          liveIntradayHealth={liveIntraday.connectionHealth}
          liveIntradayAgeMs={liveIntraday.lastDataAgeMs}
          liveScoresHealth={liveScores.connectionHealth}
          liveScoresAgeMs={liveScores.lastDataAgeMs}
        />
      )}

      {activeTab === "risk" && (
        <RiskTab risk={risk} fundamental={fundamental} />
      )}

      {activeTab === "history" && (
        <HistoryTab
          candles={candles}
          visibleCandles={visibleCandles}
          range={range}
          ranges={RANGES}
          onRangeChange={setRange}
        />
      )}
    </div>
  );
}
