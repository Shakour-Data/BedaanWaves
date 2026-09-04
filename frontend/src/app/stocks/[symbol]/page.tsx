"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { cn } from "@/lib/cn";
import { TarotCard } from "@/components/ui/TarotCard";
import { ChangeBadge } from "@/components/dashboard/StatCard";
import { StatBox } from "@/components/dashboard/StatBox";
import { CandlestickChart } from "@/components/charts/CandlestickChart";
import { StockDetailSkeleton } from "@/components/ux/SkeletonLoaders";
import { useUXStore } from "@/store/useUXStore";
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
  type Market,
} from "@/lib/api/stocks";

import { t } from "@/lib/i18n";

type Tab = "overview" | "risk" | "history";

export default function StockDetailPage() {
  const params = useParams<{ symbol: string }>();
  const symbol = decodeURIComponent(
    Array.isArray(params.symbol) ? params.symbol[0] : params.symbol ?? "",
  );

  const [activeTab, setActiveTab] = useState<Tab>("overview");
  const [asset, setAsset] = useState<Asset | null>(null);
  const [candles, setCandles] = useState<Candle[] | null>(null);
  const [latest, setLatest] = useState<LatestPrice | null>(null);
  const [scoring, setScoring] = useState<Record<string, unknown> | null>(null);
  const [fundamental, setFundamental] = useState<Record<string, unknown> | null>(null);
  const [risk, setRisk] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [range, setRange] = useState<string>("90");
  const addToast = useUXStore((state) => state.addToast);

  useEffect(() => {
    if (!symbol) return;
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const requests: Promise<unknown>[] = [
          fetchPriceHistory({ symbol, timeframe: "1d", limit: 500 }),
          fetchAsset(symbol),
          fetchLatestPrice(symbol),
          fetchScoring(symbol),
        ];

        if (activeTab === "risk") requests.push(fetchRisk(symbol), fetchFundamental(symbol));

        const results = await Promise.all(requests);
        if (cancelled) return;
        setCandles(results[0] as Candle[]);
        setAsset(results[1] as Asset | null);
        setLatest(results[2] as LatestPrice | null);
        setScoring(results[3] as Record<string, unknown>);
        if (activeTab === "risk") { setRisk(results[4] as Record<string, unknown>); setFundamental(results[5] as Record<string, unknown>); }
      } catch (e: unknown) {
        if (!cancelled) {
          const message = e instanceof Error ? e.message : t("app.stocks.detail.error_title", "en");
          setError(message);
          addToast({ type: "error", message });
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();

    return () => { cancelled = true; };
  }, [symbol, activeTab, addToast]);

  const MARKET_LABEL: Record<Market, string> = {
    NASDAQ: t("app.stocks.markets.nasdaq", "en") };

  const RANGES = useMemo(() => [
    { key: "30", label: t("app.stocks.detail.ranges.1m", "en"), days: 30 },
    { key: "90", label: t("app.stocks.detail.ranges.3m", "en"), days: 90 },
    { key: "all", label: t("app.stocks.detail.ranges.all", "en"), days: null },
  ], []);

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
    const avgVol = visibleCandles.reduce((s, c) => s + c.volume, 0) / (visibleCandles.length || 1);
    return { price: last.close, change, changePct, rangeHigh: highs.length ? Math.max(...highs) : last.high, rangeLow: lows.length ? Math.min(...lows) : last.low, lastVolume: last.volume, avgVol };
  }, [candles, visibleCandles]);

  const price = latest?.price ?? derived?.price ?? 0;
  const changePct = latest?.change_pct ?? derived?.changePct ?? 0;
  const currency = t("app.stocks.detail.currency_usd", "en");
  const noData = !candles || candles.length === 0;

  const tabs: { key: Tab; label: string }[] = [
    { key: "overview", label: "Overview" },
    { key: "risk", label: "Risk" },
    { key: "history", label: "Historical Data" },
  ];

  function fmt(n: number, digits = 0): string {
    return n.toLocaleString("en-US", { maximumFractionDigits: digits });
  }

  if (loading) {
    return (
      <StockDetailSkeleton />
    );
  }

  if (error) {
    return (
      <TarotCard icon="⚠️" title={t("app.stocks.detail.error_title", "en")}>
        <p className="text-sm text-muted-foreground">{t("app.stocks.detail.error_desc", "en").replace("{symbol}", symbol)}</p>
        <p className="mt-2 text-xs text-error">{error}</p>
        <Link href="/stocks" className="mt-3 inline-block text-sm text-secondary hover:underline">← {t("app.stocks.detail.back_to_list", "en")}</Link>
      </TarotCard>
    );
  }

  return (
      <div className="flex flex-col gap-4 animate-in fade-in duration-300">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Link href="/stocks" className="hover:text-foreground">{t("app.nav.stocks", "en")}</Link>
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
                    {MARKET_LABEL[asset.market]}
                  </span>
                ) : null}
              </div>
              {asset ? <span className="text-muted-foreground">{asset.name}</span> : null}
              {asset?.sector ? (
                <span className="text-xs text-muted-foreground">
                  {t("app.stocks.sector", "en")}: {asset.sector}
                </span>
              ) : null}
            </div>
            <div className="flex flex-col items-end gap-1">
              <span className="text-2xl font-bold">{fmt(price, 2)}</span>
              <div className="flex items-center gap-2">
                <ChangeBadge value={changePct} />
                <span className="text-xs text-muted-foreground">{currency}</span>
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
          <div className="space-y-4 animate-in fade-in duration-200">
            {derived ? (
              <section className="grid grid-cols-2 gap-3 md:grid-cols-4">
                <StatBox label={t("app.stocks.detail.last_price", "en")} value={fmt(price, 2)} hint={currency} />
                <StatBox label={`${t("app.stocks.detail.high", "en")} (${RANGES.find((r) => r.key === range)?.label})`} value={fmt(derived.rangeHigh, 2)} />
                <StatBox label={`${t("app.stocks.detail.low", "en")} (${RANGES.find((r) => r.key === range)?.label})`} value={fmt(derived.rangeLow, 2)} />
                <StatBox label={t("app.stocks.detail.volume", "en")} value={fmt(derived.lastVolume)} hint={`${t("app.stocks.detail.avg_volume", "en")}: ${fmt(derived.avgVol)}`} />
              </section>
            ) : null}

            {scoring ? (
              <TarotCard icon="💎" title={t("app.stocks.detail.analysis_6d", "en")}>
                <div className="flex flex-col md:flex-row items-center gap-8 py-4">
                  <div className="flex flex-col items-center justify-center">
                    <div className={cn(
                      "text-5xl font-black rounded-full h-32 w-32 flex items-center justify-center border-8 shadow-inner",
                      typeof scoring.overall_score === "number" && scoring.overall_score >= 70 ? "text-green-600 border-green-600/20" : typeof scoring.overall_score === "number" && scoring.overall_score >= 40 ? "text-yellow-500 border-yellow-500/20" : "text-red-600 border-red-600/20"
                    )}>
                      {scoring.overall_score as number}
                    </div>
                    <div className="mt-4 text-lg font-bold">{t("app.stocks.detail.overall_score", "en")} {(scoring.grade as string)?.replace("_", " ")}</div>
                  </div>
                  <div className="flex-1 grid grid-cols-2 md:grid-cols-3 gap-4 w-full">
                    {Object.entries(scoring.dimension_scores || {}).map(([dim, score]: [string, unknown]) => (
                      <div key={dim} className="p-3 rounded-xl bg-neutral/40 border border-border/40">
                        <div className="text-xs text-muted-foreground uppercase">{t(`app.scoring.dimensions.${dim.toLowerCase()}`, "en")}</div>
                        <div className="flex items-center justify-between mt-1">
                          <span className="font-bold text-lg">{score as number}</span>
                          <div className="h-1.5 flex-1 mx-2 bg-border rounded-full overflow-hidden">
                            <div className={cn("h-full rounded-full", (score as number) >= 70 ? "bg-green-600" : (score as number) >= 40 ? "bg-yellow-500" : "bg-red-600")} style={{ width: `${score as number}%` }} />
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="mt-4 pt-4 border-t border-border/40 flex flex-wrap gap-2">
                  <Link href={`/stocks/${symbol}/scoring`} className="inline-flex items-center gap-2 rounded-lg bg-error/10 px-4 py-2 text-sm font-semibold text-error transition hover:bg-error/20">
                    {t("app.scoring.title", "en")} →
                  </Link>
                  <Link href={`/stocks/${symbol}/charts`} className="inline-flex items-center gap-2 rounded-lg bg-primary/10 px-4 py-2 text-sm font-semibold text-primary transition hover:bg-primary/20">
                    Charts →
                  </Link>
                </div>
              </TarotCard>
            ) : null}
          </div>
        )}

        {activeTab === "risk" && (
          <div className="space-y-4 animate-in fade-in duration-200">
            {risk && Object.keys(risk).length > 0 ? (
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <TarotCard title="Risk Metrics">
                  <div className="space-y-3">
                    {Object.entries(risk).map(([key, value]) => (
                      <div key={key} className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground capitalize">{key.replace(/_/g, " ")}</span>
                        <span className="font-semibold">{typeof value === "number" ? fmt(value, 2) : String(value)}</span>
                      </div>
                    ))}
                  </div>
                </TarotCard>
                {fundamental && Object.keys(fundamental).length > 0 && (
                  <TarotCard title="Fundamentals">
                    <div className="space-y-3">
                      {Object.entries(fundamental).map(([key, value]) => (
                        <div key={key} className="flex items-center justify-between">
                          <span className="text-sm text-muted-foreground capitalize">{key.replace(/_/g, " ")}</span>
                          <span className="font-semibold">{typeof value === "number" ? fmt(value, 2) : String(value)}</span>
                        </div>
                      ))}
                    </div>
                  </TarotCard>
                )}
              </div>
            ) : (
              <div className="rounded-xl border border-dashed border-[var(--color-border)] bg-[var(--color-surface)]/30 py-12 text-center">
                <p className="text-sm text-[var(--color-text-secondary)]">Risk analysis data is not yet available for this stock.</p>
              </div>
            )}
          </div>
        )}

        {activeTab === "history" && (
          <div className="space-y-4 animate-in fade-in duration-200">
            <TarotCard>
              <div className="mb-3 flex items-center justify-between">
                <h3 className="text-lg font-semibold">{t("app.stocks.detail.chart_title", "en")}</h3>
                <div className="flex gap-1">
                  {RANGES.map((r) => (
                    <button key={r.key} type="button" onClick={() => setRange(r.key)} className={cn("rounded-full px-3 py-1 text-sm transition duration-fast ease-flow", range === r.key ? "bg-primary/10 font-semibold text-primary" : "text-muted-foreground hover:bg-neutral")}>
                      {r.label}
                    </button>
                  ))}
                </div>
              </div>
              {noData ? (
                <div className="flex min-h-[240px] items-center justify-center text-muted-foreground">{t("app.stocks.detail.no_history", "en")}</div>
              ) : (
                <CandlestickChart candles={visibleCandles} timeframe="1d" height={420} />
              )}
            </TarotCard>
          </div>
        )}
      </div>
  );
}