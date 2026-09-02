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
import { toTimestamp, createOrdinalTickMarkFormatter } from "@/components/charts/chart-time";

interface BarChartProps {
  data: { time: string | UTCTimestamp; value: number; color?: string }[];
  height?: number;
}

const LIGHT = {
  background: "#ffffff",
  text: "#5c5c5c",
  grid: "#eeeeee",
  border: "#e0e0e0" };

const DARK = {
  background: "#1e1e1e",
  text: "#a8a8a8",
  grid: "#2a2a2a",
  border: "#333333" };

export function BarChart({ data, height = 320 }: BarChartProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const { theme } = useAppStore();
  const colors = theme === "dark" ? DARK : LIGHT;

  const chartSeries = useMemo(() => {
    const ordinalLabels = new Map<number, string>();
    const chartData = data.map((d, i) => ({
      time: toTimestamp(d.time, i, ordinalLabels),
      value: d.value,
      color: d.color,
    }));
    return { chartData, ordinalLabels };
  }, [data]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const hasOrdinal = chartSeries.ordinalLabels.size > 0;
    const timeScaleFormatter = hasOrdinal
      ? createOrdinalTickMarkFormatter(chartSeries.ordinalLabels)
      : undefined;

    const chart = createChart(container, {
      height,
      layout: {
        background: { type: ColorType.Solid, color: colors.background },
        textColor: colors.text,
        fontFamily: "inherit" },
      grid: {
        vertLines: { color: colors.grid },
        horzLines: { color: colors.grid } },
      rightPriceScale: { borderColor: colors.border },
      timeScale: {
        borderColor: colors.border,
        tickMarkFormatter: timeScaleFormatter,
      },
      crosshair: { mode: CrosshairMode.Normal },
      localization: {
        locale: "en-US",
        priceFormatter: (p: number) => p.toLocaleString("en-US", { maximumFractionDigits: 2 }) },
      autoSize: false });
    chartRef.current = chart;

    const series = chart.addSeries(HistogramSeries, {
      priceFormat: { type: "volume" } });
    series.setData(chartSeries.chartData);

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
  }, [chartSeries, colors, height]);

  return <div ref={containerRef} className="w-full" style={{ height }} />;
}
