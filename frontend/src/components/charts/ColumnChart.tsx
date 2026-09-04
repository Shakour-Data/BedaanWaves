"use client";

import { useEffect, useMemo, useRef } from "react";
import {
  createChart,
  HistogramSeries,
  ColorType,
  CrosshairMode,
  type IChartApi,
  type UTCTimestamp,
} from "lightweight-charts";
import { useAppStore } from "@/store/useAppStore";
import { toTimestamp, createDateTickMarkFormatter, createOrdinalTickMarkFormatter } from "@/components/charts/chart-time";
import { priceFormatter } from "@/lib/utils";

interface ColumnChartProps {
  data: { time: string | number; value: number; color?: string }[];
  height?: number;
  valueFormatter?: (value: number) => string;
  yAxisLabel?: string;
}

const LIGHT = {
  background: "#ffffff",
  text: "#5c5c5c",
  grid: "#eeeeee",
  border: "#e0e0e0",
}

const DARK = {
  background: "#1e1e1e",
  text: "#a8a8a8",
  grid: "#2a2a2a",
  border: "#333333",
}

const DEFAULT_GREEN = "#10b981";
const DEFAULT_RED = "#ef4444";

export function ColumnChart({ data, height = 240, valueFormatter, yAxisLabel = "Value" }: ColumnChartProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const { theme } = useAppStore();
  const colors = theme === "dark" ? DARK : LIGHT;

  const chartData = useMemo(() => {
    const ordinalLabels = new Map<number, string>();
    const normalized = data.map((d, i) => ({
      time: toTimestamp(d.time, i, ordinalLabels),
      value: d.value,
      color: d.color,
    }));
    return { data: normalized, ordinalLabels };
  }, [data]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const hasOrdinal = chartData.ordinalLabels.size > 0;
    const timeScaleFormatter = hasOrdinal
      ? createOrdinalTickMarkFormatter(chartData.ordinalLabels)
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
      },
      timeScale: {
        borderColor: colors.border,
        tickMarkFormatter: timeScaleFormatter,
      },
      crosshair: { mode: CrosshairMode.Normal },
      localization: {
        locale: "en-US",
        priceFormatter: valueFormatter || priceFormatter,
      },
      autoSize: false,
    });
    chartRef.current = chart;

    const series = chart.addSeries(HistogramSeries, {
      priceFormat: { type: "price", precision: 4, minMove: 0.0001 },
      priceScaleId: "right",
    });

    const histogramData = chartData.data.map((d) => ({
      time: d.time,
      value: d.value,
      color: d.color || (d.value >= 0 ? DEFAULT_GREEN : DEFAULT_RED),
    }));
    series.setData(histogramData);

    chart.timeScale().fitContent();

    const resize = () => chart.applyOptions({ width: container.clientWidth });
    resize();
    const observer = new ResizeObserver(resize);
    observer.observe(container);

    return () => {
      observer.disconnect();
      chart.remove();
      chartRef.current = null;
    };
  }, [chartData, colors, height, valueFormatter, yAxisLabel]);

  return <div ref={containerRef} className="w-full" style={{ height }} />;
}
