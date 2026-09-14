"use client";

import Link from "next/link";
import { cn } from "@/lib/cn";
import { TarotCard } from "@/components/ui/TarotCard";
import { StatBox } from "@/components/shared/StatBox";
import { CandlestickChart } from "@/components/charts/CandlestickChart";
import { LiveConnectionIndicator, type ConnectionHealth } from "@/hooks/useLiveData";
import { t } from "@/lib/i18n";
import type { Asset, Candle, LatestPrice, Market } from "@/lib/api/stocks";
import type { ScoringData, IntradayBar } from "./types";

interface OverviewTabProps {
  symbol: string;
  asset: Asset | null;
  candles: Candle[] | null;
  intradayBars: IntradayBar[];
  latest: LatestPrice | null;
  scoring: ScoringData | null;
  visibleCandles: Candle[];
  chartBarsForWindow: Candle[];
  derived: {
    price: number;
    change: number;
    changePct: number;
    rangeHigh: number;
    rangeLow: number;
    lastVolume: number;
    avgVol: number;
  } | null;
  livePrice: number;
  liveChangePct: number;
  currency: string;
  range: string;
  ranges: Array<{ key: string; label: string; days: number | null }>;
  liveQuoteHealth: ConnectionHealth;
  liveQuoteAgeMs: number | null;
  liveIntradayHealth: ConnectionHealth;
  liveIntradayAgeMs: number | null;
  liveScoresHealth: ConnectionHealth;
  liveScoresAgeMs: number | null;
}

const MARKET_LABEL: Record<Market, string> = {
  NASDAQ: t("app.stocks.markets.nasdaq"),
};

export function OverviewTab({
  symbol,
  asset,
  scoring,
  derived,
  livePrice,
  liveChangePct,
  currency,
  range,
  ranges,
  intradayBars,
  chartBarsForWindow,
  liveQuoteHealth,
  liveQuoteAgeMs,
  liveIntradayHealth,
  liveIntradayAgeMs,
  liveScoresHealth,
  liveScoresAgeMs,
}: OverviewTabProps) {
  return (
    <div className="space-y-4 animate-in fade-in duration-200">
      {derived ? (
        <section className="grid grid-cols-2 gap-3 md:grid-cols-4">
          <StatBox
            label={t("app.stocks.detail.last_price")}
            value={livePrice.toLocaleString("en-US", { maximumFractionDigits: 2 })}
            hint={currency}
          />
          <StatBox
            label={`${t("app.stocks.detail.high")} (${ranges.find((r) => r.key === range)?.label})`}
            value={derived.rangeHigh.toLocaleString("en-US", { maximumFractionDigits: 2 })}
          />
          <StatBox
            label={`${t("app.stocks.detail.low")} (${ranges.find((r) => r.key === range)?.label})`}
            value={derived.rangeLow.toLocaleString("en-US", { maximumFractionDigits: 2 })}
          />
          <StatBox
            label={t("app.stocks.detail.volume")}
            value={derived.lastVolume.toLocaleString("en-US", { maximumFractionDigits: 0 })}
            hint={`${t("app.stocks.detail.avg_volume")}: ${derived.avgVol.toLocaleString("en-US", { maximumFractionDigits: 0 })}`}
          />
        </section>
      ) : null}

      {intradayBars.length > 0 && (
        <TarotCard>
          <div className="mb-3 flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold">
                Intraday · 5m · Last {intradayBars.length} bars
              </h3>
              <p className="text-xs text-muted-foreground">
                Rolling window · live patches applied
              </p>
            </div>
            <LiveConnectionIndicator
              health={liveIntradayHealth}
              dataAgeMs={liveIntradayAgeMs}
              lastEventTs={null}
            />
          </div>
          <CandlestickChart candles={chartBarsForWindow} timeframe="5m" height={320} />
        </TarotCard>
      )}

      {scoring ? (
        <TarotCard icon="💎" title={t("app.stocks.detail.analysis_6d")}>
          <div className="mb-3 flex items-center justify-end">
            <LiveConnectionIndicator
              health={liveScoresHealth}
              dataAgeMs={liveScoresAgeMs}
              lastEventTs={null}
              label="Scores"
            />
          </div>
          <div className="flex flex-col md:flex-row items-center gap-8 py-4">
            <div className="flex flex-col items-center justify-center">
              <div
                className={cn(
                  "text-5xl font-black rounded-full h-32 w-32 flex items-center justify-center border-8 shadow-inner",
                  typeof scoring.overall_score === "number" && scoring.overall_score >= 70
                    ? "text-green-600 border-green-600/20"
                    : typeof scoring.overall_score === "number" && scoring.overall_score >= 40
                    ? "text-yellow-500 border-yellow-500/20"
                    : "text-red-600 border-red-600/20"
                )}
              >
                {scoring.overall_score ?? "—"}
              </div>
              <div className="mt-4 text-lg font-bold">
                {t("app.stocks.detail.overall_score")}{" "}
                {scoring.grade?.replace("_", " ")}
              </div>
            </div>
            <div className="flex-1 grid grid-cols-2 md:grid-cols-3 gap-4 w-full">
              {Object.entries(scoring.dimension_scores || {}).map(([dim, score]) => {
                const scoreNum = typeof score === "number" ? score : 0;
                return (
                  <div key={dim} className="p-3 rounded-xl bg-neutral/40 border border-border/40">
                    <div className="text-xs text-muted-foreground uppercase">
                      {t(`app.scoring.dimensions.${dim.toLowerCase()}`)}
                    </div>
                    <div className="flex items-center justify-between mt-1">
                      <span className="font-bold text-lg">{scoreNum}</span>
                      <div className="h-1.5 flex-1 mx-2 bg-border rounded-full overflow-hidden">
                        <div
                          className={cn(
                            "h-full rounded-full",
                            scoreNum >= 70 ? "bg-green-600" : scoreNum >= 40 ? "bg-yellow-500" : "bg-red-600"
                          )}
                          style={{ width: `${scoreNum}%` }}
                        />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
          <div className="mt-4 pt-4 border-t border-border/40 flex flex-wrap gap-2">
            <Link
              href={`/stocks/${symbol}/scoring`}
              className="inline-flex items-center gap-2 rounded-lg bg-error/10 px-4 py-2 text-sm font-semibold text-error transition hover:bg-error/20"
            >
              {t("app.scoring.title")} →
            </Link>
            <Link
              href={`/stocks/${symbol}/charts`}
              className="inline-flex items-center gap-2 rounded-lg bg-primary/10 px-4 py-2 text-sm font-semibold text-primary transition hover:bg-primary/20"
            >
              Charts →
            </Link>
          </div>
        </TarotCard>
      ) : null}
    </div>
  );
}
