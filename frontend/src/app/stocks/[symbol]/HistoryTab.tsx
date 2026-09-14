"use client";

import { cn } from "@/lib/cn";
import { TarotCard } from "@/components/ui/TarotCard";
import { CandlestickChart } from "@/components/charts/CandlestickChart";
import { t } from "@/lib/i18n";
import type { Candle } from "@/lib/api/stocks";

interface HistoryTabProps {
  candles: Candle[] | null;
  visibleCandles: Candle[];
  range: string;
  ranges: Array<{ key: string; label: string; days: number | null }>;
  onRangeChange: (range: string) => void;
}

export function HistoryTab({ candles, visibleCandles, range, ranges, onRangeChange }: HistoryTabProps) {
  const noData = !candles || candles.length === 0;

  return (
    <div className="space-y-4 animate-in fade-in duration-200">
      <TarotCard>
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-lg font-semibold">
            {t("app.stocks.detail.chart_title")}
          </h3>
          <div className="flex gap-1">
            {ranges.map((r) => (
              <button
                key={r.key}
                type="button"
                onClick={() => onRangeChange(r.key)}
                className={cn(
                  "rounded-full px-3 py-1 text-sm transition duration-fast ease-flow",
                  range === r.key
                    ? "bg-primary/10 font-semibold text-primary"
                    : "text-muted-foreground hover:bg-neutral"
                )}
              >
                {r.label}
              </button>
            ))}
          </div>
        </div>
        {noData ? (
          <div className="flex min-h-[240px] items-center justify-center text-muted-foreground">
            {t("app.stocks.detail.no_history")}
          </div>
        ) : (
          <CandlestickChart candles={visibleCandles} timeframe="1d" height={420} />
        )}
      </TarotCard>
    </div>
  );
}
