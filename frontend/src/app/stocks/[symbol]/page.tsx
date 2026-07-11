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
import { TarotCard } from "@/components/ui/TarotCard";
import { ChangeBadge } from "@/components/dashboard/StatCard";
import { CandlestickChart } from "@/components/charts/CandlestickChart";
import {
  fetchAsset,
  fetchPriceHistory,
  fetchLatestPrice,
  type Asset,
  type Candle,
  type LatestPrice,
  type Market,
} from "@/lib/api/stocks";

const MARKET_LABEL: Record<Market, string> = {
  TSE: "بورس",
  OTC: "فرابورس",
  BINANCE: "کریپتو (Binance)",
  KRAKEN: "کریپتو (Kraken)",
  COINBASE: "کریپتو (Coinbase)",
  NYSE: "NYSE",
  NASDAQ: "NASDAQ",
};

const RANGES: { key: string; label: string; days: number | null }[] = [
  { key: "30", label: "۱ ماه", days: 30 },
  { key: "90", label: "۳ ماه", days: 90 },
  { key: "all", label: "همه", days: null },
];

function fmt(n: number, digits = 0): string {
  return n.toLocaleString("fa-IR", { maximumFractionDigits: digits });
}

function StatBox({ label, value, hint }: { label: string; value: React.ReactNode; hint?: string }) {
  return (
    <div className="flex flex-col gap-1 rounded-xl bg-neutral/60 px-3 py-2">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className="text-lg font-bold">{value}</span>
      {hint ? <span className="text-xs text-muted-foreground">{hint}</span> : null}
    </div>
  );
}

export default function StockDetailPage() {
  const params = useParams<{ symbol: string }>();
  const symbol = decodeURIComponent(
    Array.isArray(params.symbol) ? params.symbol[0] : params.symbol ?? "",
  );

  const [asset, setAsset] = useState<Asset | null>(null);
  const [candles, setCandles] = useState<Candle[] | null>(null);
  const [latest, setLatest] = useState<LatestPrice | null>(null);
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
        const [history, a, l] = await Promise.all([
          fetchPriceHistory({ symbol, timeframe: "1d", limit: 500 }),
          fetchAsset(symbol),
          fetchLatestPrice(symbol),
        ]);
        if (!active) return;
        setCandles(history);
        setAsset(a);
        setLatest(l);
      } catch (e: unknown) {
        if (active) setError(e instanceof Error ? e.message : "خطا در دریافت داده‌ی نماد");
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
  const currency = asset?.currency === "USD" ? "دلار" : "ریال";

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center text-muted-foreground">
        در حال بارگذاری نماد {symbol}…
      </div>
    );
  }

  if (error) {
    return (
      <TarotCard icon="⚠️" title="خطا در دریافت داده">
        <p className="text-sm text-muted-foreground">
          دریافت داده‌ی نماد «{symbol}» ممکن نشد. مطمئن شوید سرویس بک‌اند در حال اجراست و نماد وجود
          دارد.
        </p>
        <p className="mt-2 text-xs text-primary">{error}</p>
        <Link href="/stocks" className="mt-3 inline-block text-sm text-secondary hover:underline">
          ← بازگشت به فهرست سهام
        </Link>
      </TarotCard>
    );
  }

  const noData = !candles || candles.length === 0;

  return (
    <div className="flex flex-col gap-3">
      {/* سرتیتر نماد */}
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Link href="/stocks" className="hover:text-foreground">
          سهام
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
              <span className="text-xs text-muted-foreground">صنعت: {asset.sector}</span>
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
          <StatBox label="آخرین قیمت" value={fmt(price, 2)} hint={currency} />
          <StatBox
            label={`بیشترین (${RANGES.find((r) => r.key === range)?.label})`}
            value={fmt(derived.rangeHigh, 2)}
          />
          <StatBox
            label={`کمترین (${RANGES.find((r) => r.key === range)?.label})`}
            value={fmt(derived.rangeLow, 2)}
          />
          <StatBox
            label="حجم آخرین معامله"
            value={fmt(derived.lastVolume)}
            hint={`میانگین: ${fmt(derived.avgVol)}`}
          />
        </section>
      ) : null}

      {/* نمودار */}
      <TarotCard>
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-lg font-semibold">نمودار قیمت (روزانه)</h3>
          <div className="flex gap-1">
            {RANGES.map((r) => (
              <button
                key={r.key}
                type="button"
                onClick={() => setRange(r.key)}
                className={
                  "rounded-full px-3 py-1 text-sm transition duration-fast ease-flow " +
                  (range === r.key
                    ? "bg-secondary/10 font-semibold text-secondary"
                    : "text-muted-foreground hover:bg-black/5")
                }
              >
                {r.label}
              </button>
            ))}
          </div>
        </div>

        {noData ? (
          <div className="flex min-h-[240px] items-center justify-center text-muted-foreground">
            داده‌ی تاریخی برای این نماد موجود نیست.
          </div>
        ) : (
          <CandlestickChart candles={visibleCandles} timeframe="1d" height={420} />
        )}
      </TarotCard>
    </div>
  );
}
