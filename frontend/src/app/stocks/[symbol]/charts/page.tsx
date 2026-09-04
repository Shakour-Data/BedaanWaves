"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { TarotCard } from "@/components/ui/TarotCard";
import { PageLoading } from "@/components/ui/PageLoading";
import { CandlestickChart } from "@/components/charts/CandlestickChart";
import { ScoreTrendChart } from "@/components/charts/ScoreTrendChart";
import { ColumnChart } from "@/components/charts/ColumnChart";
import {
  fetchPriceHistory,
  type Candle,
} from "@/lib/api/stocks";
import {
  fetchScoreHistory,
  type ScoreHistoryPoint,
} from "@/lib/api/scoring";

import { t } from "@/lib/i18n";
import { num } from "@/lib/utils";

const SCORE_DIMENSIONS: { key: string; label: string; color: string }[] = [
  { key: "overall", label: "Overall", color: "#005A9C" },
  { key: "fundamental", label: "Fundamental", color: "#2563EB" },
  { key: "technical", label: "Technical", color: "#10b981" },
  { key: "sentiment", label: "Sentiment", color: "#f59e0b" },
  { key: "risk", label: "Risk", color: "#ef4444" },
  { key: "macro", label: "Macro", color: "#8b5cf6" },
  { key: "ai", label: "AI", color: "#ec4899" },
];

export default function StockChartsPage() {
  const params = useParams<{ symbol: string }>();
  const symbol = decodeURIComponent(
    Array.isArray(params.symbol) ? params.symbol[0] : params.symbol ?? "",
  );

  const [candles, setCandles] = useState<Candle[] | null>(null);
  const [history, setHistory] = useState<ScoreHistoryPoint[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!symbol) return;
    let active = true;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [c, h] = await Promise.all([
          fetchPriceHistory({ symbol, timeframe: "1d", limit: 500 }),
          fetchScoreHistory(symbol, 30),
        ]);
        if (!active) return;
        setCandles(c);
        setHistory(h);
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

  const scoreSeries = useMemo(() => {
    if (!history) return [];
    return SCORE_DIMENSIONS.map((dim) => ({
      key: dim.key,
      label: dim.label,
      color: dim.color,
      data: history.map((pt) => {
        const raw = dim.key === "overall" ? pt.overall : pt[dim.key];
        return {
          time: pt.date,
          value: dim.key === "overall" ? num(raw) : (raw === undefined ? 0 : num(raw)),
        };
      }),
    }));
  }, [history]);

  const scoreDeltas = useMemo(() => {
    if (!history || history.length < 2) return [];
    return history.slice(1).map((pt, i) => ({
      date: pt.date,
      value: num(pt.overall) - num(history[i].overall),
    }));
  }, [history]);

  if (loading) {
    return <PageLoading />;
  }

  if (error) {
    return (
      <TarotCard icon="⚠️" title={t("app.analysis.scoring_not_found", "en")}>
        <p className="text-sm text-muted-foreground">{error}</p>
        <Link href={`/stocks/${symbol}`} className="mt-3 inline-block text-sm text-secondary hover:underline">
          ← {t("app.stocks.detail.back_to_list", "en")}
        </Link>
      </TarotCard>
    );
  }

  const noPrice = !candles || candles.length === 0;
  const noScores = !history || history.length === 0;

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Link href={`/stocks/${symbol}`} className="hover:text-foreground">
          {symbol}
        </Link>
        <span>/</span>
        <span className="text-foreground">Charts</span>
      </div>

      <TarotCard title="Price History">
        {noPrice ? (
          <div className="flex min-h-[240px] items-center justify-center text-muted-foreground">
            {t("app.stocks.detail.no_history", "en")}
          </div>
        ) : (
          <CandlestickChart candles={candles!} timeframe="1d" height={420} />
        )}
      </TarotCard>

      <TarotCard title="6D Score History (30-Day)">
        {noScores ? (
          <div className="flex min-h-[240px] items-center justify-center text-muted-foreground">
            {t("app.analysis.no_data", "en")}
          </div>
        ) : (
          <ScoreTrendChart series={scoreSeries} height={360} showLegend />
        )}
      </TarotCard>

      <TarotCard title="Overall Score Changes (Daily Delta)">
        <p className="mb-2 text-xs text-muted-foreground">
          Day-over-day change in overall score across the 30-day window — green/red bars indicate up/down
        </p>
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
            {t("app.analysis.no_data", "en")}
          </div>
        )}
      </TarotCard>
    </div>
  );
}
