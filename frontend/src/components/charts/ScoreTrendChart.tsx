"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  createChart,
  LineSeries,
  ColorType,
  CrosshairMode,
  type IChartApi,
  type ISeriesApi,
  type UTCTimestamp,
} from "lightweight-charts";
import { useAppStore } from "@/store/useAppStore";
import { normalizeChartData, createOrdinalTickMarkFormatter, createDateTickMarkFormatter } from "@/components/charts/chart-time";
import { cn } from "@/lib/cn";

interface SeriesDef {
  key: string;
  label: string;
  color: string;
  data: { time: string | UTCTimestamp; value: number }[];
}

interface ScoreTrendChartProps {
  series: SeriesDef[];
  height?: number;
  showLegend?: boolean;
  defaultHiddenKeys?: string[];
}

const PALETTE = [
  "#2563EB",
  "#10b981",
  "#f59e0b",
  "#ef4444",
  "#8b5cf6",
  "#ec4899",
  "#06b6d4",
  "#f97316",
];

const LIGHT = {
  background: "#ffffff",
  text: "#5c5c5c",
  grid: "#eeeeee",
  border: "#e0e0e0",
};

const DARK = {
  background: "#1e1e1e",
  text: "#a8a8a8",
  grid: "#2a2a2a",
  border: "#333333",
};

export function ScoreTrendChart({
  series,
  height = 360,
  showLegend = false,
  defaultHiddenKeys = [],
}: ScoreTrendChartProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRefs = useRef<ISeriesApi<"Line">[]>([]);
  const { theme } = useAppStore();
  const colors = theme === "dark" ? DARK : LIGHT;

  const [hidden, setHidden] = useState<Set<string>>(() => new Set(defaultHiddenKeys));

  const visibleSeries = useMemo(
    () =>
      series.map((s, i) => ({
        ...s,
        color: s.color || PALETTE[i % PALETTE.length],
      })),
    [series]
  );

  const chartSeries = useMemo(() => {
    const ordinalLabels = new Map<number, string>();
    const series = visibleSeries.map((s) => {
      const { data, ordinalLabels: labels } = normalizeChartData(s.data);
      for (const [k, v] of labels) ordinalLabels.set(k, v);
      return { ...s, data };
    });
    return { series, ordinalLabels };
  }, [visibleSeries]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const hasOrdinal = chartSeries.ordinalLabels.size > 0;
    const timeScaleFormatter = hasOrdinal
      ? createOrdinalTickMarkFormatter(chartSeries.ordinalLabels)
      : createDateTickMarkFormatter();

    const chart = createChart(container, {
      height,
      layout: {
        background: { type: ColorType.Solid, color: colors.background },
        textColor: colors.text,
        fontFamily: "inherit",
      },
      grid: {
        vertLines: { color: colors.grid },
        horzLines: { color: colors.grid },
      },
      rightPriceScale: {
        borderColor: colors.border,
        autoScale: true,
      },
      timeScale: {
        borderColor: colors.border,
        tickMarkFormatter: timeScaleFormatter,
      },
      crosshair: { mode: CrosshairMode.Normal },
      localization: {
        locale: "en-US",
        priceFormatter: (p: number) => p.toLocaleString("en-US", { maximumFractionDigits: 2 }),
      },
      autoSize: false,
    });
    chartRef.current = chart;

    seriesRefs.current = [];
    for (const s of chartSeries.series) {
      const line = chart.addSeries(LineSeries, {
        color: s.color,
        lineWidth: 2,
        priceScaleId: "right",
        visible: !hidden.has(s.key),
      });
      line.setData(s.data);
      seriesRefs.current.push(line);
    }

    chart.timeScale().fitContent();

    const resize = () => chart.applyOptions({ width: container.clientWidth });
    resize();
    const observer = new ResizeObserver(resize);
    observer.observe(container);

    return () => {
      observer.disconnect();
      chart.remove();
      chartRef.current = null;
      seriesRefs.current = [];
    };
    // ``hidden`` is intentionally omitted: we do NOT want to recreate the
    // lightweight-charts instance every time a dimension is toggled. The
    // separate effect below flips the per-series ``visible`` flag in place.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chartSeries, colors, height]);

  useEffect(() => {
    seriesRefs.current.forEach((line, i) => {
      const key = chartSeries.series[i]?.key;
      if (!key) return;
      line.applyOptions({ visible: !hidden.has(key) });
    });
  }, [hidden, chartSeries]);

  const toggle = (key: string) => {
    setHidden((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  return (
    <div className="w-full">
      {showLegend && (
        <div className="mb-2 flex flex-wrap gap-2">
          {chartSeries.series.map((s) => {
            const isHidden = hidden.has(s.key);
            return (
              <button
                key={s.key}
                type="button"
                onClick={() => toggle(s.key)}
                aria-pressed={!isHidden}
                className={cn(
                  "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium transition-opacity",
                  isHidden
                    ? "border-[var(--color-border)] bg-[var(--color-background)] opacity-50"
                    : "border-transparent bg-[var(--color-background)]"
                )}
              >
                <span
                  className="inline-block h-2.5 w-2.5 rounded-full"
                  style={{ backgroundColor: s.color }}
                />
                <span>{s.label}</span>
              </button>
            );
          })}
        </div>
      )}
      <div ref={containerRef} className="w-full" style={{ height }} />
    </div>
  );
}
