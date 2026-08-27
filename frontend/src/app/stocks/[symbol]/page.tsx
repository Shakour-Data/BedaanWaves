"use client";

/**
 * صفحه‌ی جزئیات سهم: `/stocks/[symbol]`
 * - نمودار کندل‌استیک OHLCV + حجم (از `GET /market/price-history`).
 * - آمار لحظه‌ای (از `GET /market/latest-prices`).
 * - انتخاب بازه‌ی زمانی نمایش (۳۰ / ۹۰ / همه) به‌صورت سمتِ کلاینت.
 */

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { cn } from "@/lib/cn";
import { TarotCard } from "@/components/ui/TarotCard";
import { ChangeBadge } from "@/components/dashboard/StatCard";
import { CandlestickChart } from "@/components/charts/CandlestickChart";
import {
  fetchAsset,
  fetchPriceHistory,
  fetchLatestPrice,
  fetchScoring,
  type Asset,
  type Candle,
  type LatestPrice,
  type Market,
} from "@/lib/api/stocks";

import { t } from "@/lib/i18n";
import { useAuthStore } from "@/store/useAuthStore";

export default function StockDetailPage() {
  const { currentLang } = useAuthStore();
  const params = useParams<{ symbol: string }>();
  const symbol = decodeURIComponent(
    Array.isArray(params.symbol) ? params.symbol[0] : params.symbol ?? "",
  );

  const MARKET_LABEL: Record<Market, string> = {
    TSE: t("app.stocks.markets.tse", currentLang),
    OTC: t("app.stocks.markets.otc", currentLang),
    BINANCE: t("app.stocks.markets.binance", currentLang),
    KRAKEN: t("app.stocks.markets.kraken", currentLang),
    COINBASE: t("app.stocks.markets.coinbase", currentLang),
    NYSE: t("app.stocks.markets.nyse", currentLang),
    NASDAQ: t("app.stocks.markets.nasdaq", currentLang),
  };

  const RANGES: { key: string; label: string; days: number | null }[] = [
    { key: "30", label: t("app.stocks.detail.ranges.1m", currentLang), days: 30 },
    { key: "90", label: t("app.stocks.detail.ranges.3m", currentLang), days: 90 },
    { key: "all", label: t("app.stocks.detail.ranges.all", currentLang), days: null },
  ];

  function fmt(n: number, digits = 0): string {
    return currentLang === "fa" 
      ? n.toLocaleString("fa-IR", { maximumFractionDigits: digits })
      : n.toLocaleString("en-US", { maximumFractionDigits: digits });
  }

  const [asset, setAsset] = useState<Asset | null>(null);
  const [candles, setCandles] = useState<Candle[] | null>(null);
  const [latest, setLatest] = useState<LatestPrice | null>(null);
  const [scoring, setScoring] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [range, setRange] = useState<string>("90");

  useEffect(() => {
    if (!symbol) return;
    let active = true;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [history, a, l, s] = await Promise.all([
          fetchPriceHistory({ symbol, timeframe: "1d", limit: 500 }),
          fetchAsset(symbol),
          fetchLatestPrice(symbol),
          fetchScoring(symbol),
        ]);
        if (!active) return;
        setCandles(history);
        setAsset(a);
        setLatest(l);
        setScoring(s);
      } catch (e: unknown) {
        if (active) setError(e instanceof Error ? e.message : t("app.stocks.detail.error_title", currentLang));
      } finally {
        if (active) setLoading(false);
      }
    }

    load();

    return () => {
      active = false;
    };
  }, [symbol]);

  const visibleCandles = useMemo(() => {
    if (!candles) return [];
    const cfg = RANGES.find((r) => r.key === range);
    if (!cfg || cfg.days === null) return candles;
    return candles.slice(-cfg.days);
  }, [candles, range]);

  // آمارِ مشتق‌شده از کندل‌ها (پشتیبانِ latest-prices).
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
      visibleCandles.reduce((s, c) => s + c.volume, 0) / (visibleCandles.length || 1);
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

  const price = latest?.price ?? derived?.price ?? 0;
  const changePct = latest?.change_pct ?? derived?.changePct ?? 0;
  const currency = asset?.currency === "USD" 
    ? t("app.stocks.detail.currency_usd", currentLang) 
    : t("app.stocks.detail.currency_irr", currentLang);

  if (loading) {
    return (
      <DashboardShell title={t("app.stocks.title", currentLang)}>
        <div className="flex min-h-[40vh] items-center justify-center text-muted-foreground">
          {t("app.stocks.detail.loading", currentLang).replace("{symbol}", symbol)}
        </div>
      </DashboardShell>
    );
  }

  if (error) {
    return (
      <DashboardShell title={t("app.stocks.title", currentLang)}>
        <TarotCard icon="⚠️" title={t("app.stocks.detail.error_title", currentLang)}>
          <p className="text-sm text-muted-foreground">
            {t("app.stocks.detail.error_desc", currentLang).replace("{symbol}", symbol)}
          </p>
          <p className="mt-2 text-xs text-red-600">{error}</p>
          <Link href="/stocks" className="mt-3 inline-block text-sm text-secondary hover:underline">
            ← {t("app.stocks.detail.back_to_list", currentLang)}
          </Link>
        </TarotCard>
      </DashboardShell>
    );
  }

  const noData = !candles || candles.length === 0;

  return (
    <DashboardShell title={t("app.stocks.title", currentLang)}>
      <div className="flex flex-col gap-3">
        {/* سرتیتر نماد */}
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Link href="/stocks" className="hover:text-foreground">
            {t("app.nav.stocks", currentLang)}
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
                    {MARKET_LABEL[asset.market]}
                  </span>
                ) : null}
              </div>
              {asset ? <span className="text-muted-foreground">{asset.name}</span> : null}
              {asset?.sector ? (
                <span className="text-xs text-muted-foreground">
                  {t("app.stocks.sector", currentLang)}: {asset.sector}
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

        {/* آمار لحظه‌ای */}
        {derived ? (
          <section className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <StatBox label={t("app.stocks.detail.last_price", currentLang)} value={fmt(price, 2)} hint={currency} />
            <StatBox
              label={`${t("app.stocks.detail.high", currentLang)} (${RANGES.find((r) => r.key === range)?.label})`}
              value={fmt(derived.rangeHigh, 2)}
            />
            <StatBox
              label={`${t("app.stocks.detail.low", currentLang)} (${RANGES.find((r) => r.key === range)?.label})`}
              value={fmt(derived.rangeLow, 2)}
            />
            <StatBox
              label={t("app.stocks.detail.volume", currentLang)}
              value={fmt(derived.lastVolume)}
              hint={`${t("app.stocks.detail.avg_volume", currentLang)}: ${fmt(derived.avgVol)}`}
            />
          </section>
        ) : null}

        {/* تحلیل ۶ بعدی */}
        {scoring ? (
          <TarotCard icon="💎" title={t("app.stocks.detail.analysis_6d", currentLang)}>
            <div className="flex flex-col md:flex-row items-center gap-8 py-4">
              <div className="flex flex-col items-center justify-center">
                <div className={cn(
                  "text-5xl font-black rounded-full h-32 w-32 flex items-center justify-center border-8 shadow-inner",
                  scoring.overall_score >= 70 ? "text-green-600 border-green-600/20" : 
                  scoring.overall_score >= 40 ? "text-yellow-500 border-yellow-500/20" : "text-red-600 border-red-600/20"
                )}>
                  {scoring.overall_score}
                </div>
                <div className="mt-4 text-lg font-bold">
                  {t("app.stocks.detail.overall_score", currentLang)} {scoring.grade?.replace("_", " ")}
                </div>
              </div>
              
              <div className="flex-1 grid grid-cols-2 md:grid-cols-3 gap-4 w-full">
                {Object.entries(scoring.dimension_scores || {}).map(([dim, score]: [string, any]) => (
                  <div key={dim} className="p-3 rounded-xl bg-neutral/40 border border-border/40">
                    <div className="text-xs text-muted-foreground uppercase">
                      {t(`app.scoring.dimensions.${dim.toLowerCase()}`, currentLang)}
                    </div>
                    <div className="flex items-center justify-between mt-1">
                      <span className="font-bold text-lg">{score}</span>
                      <div className="h-1.5 flex-1 mx-2 bg-border rounded-full overflow-hidden">
                        <div 
                          className={cn(
                            "h-full rounded-full",
                            score >= 70 ? "bg-green-600" : score >= 40 ? "bg-yellow-500" : "bg-red-600"
                          )}
                          style={{ width: `${score}%` }}
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
            {scoring.signals && scoring.signals.length > 0 && (
              <div className="mt-4 flex flex-wrap gap-2 pt-4 border-t border-border/40">
                {scoring.signals.map((sig: string, i: number) => (
                  <span key={i} className="px-3 py-1 rounded-full bg-red-600/10 text-red-600 text-xs font-semibold">
                    {sig.replace("_", " ")}
                  </span>
                ))}
              </div>
            )}
          </TarotCard>
        ) : null}

        {/* نمودار */}
        <TarotCard icon="📊">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-lg font-semibold">{t("app.stocks.detail.chart_title", currentLang)}</h3>
            <div className="flex gap-1">
              {RANGES.map((r) => (
                <button
                  key={r.key}
                  type="button"
                  onClick={() => setRange(r.key)}
                  className={cn(
                    "rounded-full px-3 py-1 text-sm transition duration-fast ease-flow",
                    range === r.key
                      ? "bg-red-600/10 font-semibold text-red-600"
                      : "text-muted-foreground hover:bg-black/5"
                  )}
                >
                  {r.label}
                </button>
              ))}
            </div>
          </div>

          {noData ? (
            <div className="flex min-h-[240px] items-center justify-center text-muted-foreground">
              {t("app.stocks.detail.no_history", currentLang)}
            </div>
          ) : (
            <CandlestickChart candles={visibleCandles} timeframe="1d" height={420} />
          )}
        </TarotCard>
      </div>
    </DashboardShell>
  );
}

