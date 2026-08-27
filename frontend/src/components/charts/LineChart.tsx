"use client";

import { useEffect, useMemo, useRef } from "react";
import {
  createChart,
  LineSeries,
  ColorType,
  CrosshairMode,
  type IChartApi,
  type UTCTimestamp,
  type LineData } from "lightweight-charts";
import { useAppStore } from "@/store/useAppStore";

interface LineChartProps {
  data: { time: string | UTCTimestamp; value: number }[];
  height?: number;
  color?: string;
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

export function LineChart({ data, height = 320, color = "#2563EB" }: LineChartProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const { theme } = useAppStore();
  const colors = theme === "dark" ? DARK : LIGHT;

  const chartData = useMemo(
    () =>
      data.map((d) => ({
        time: d.time as LineData["time"],
        value: d.value })),
    [data]
  );

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

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
      timeScale: { borderColor: colors.border },
      crosshair: { mode: CrosshairMode.Normal },
      localization: {
        locale: "fa-IR",
        priceFormatter: (p: number) => p.toLocaleString("fa-IR", { maximumFractionDigits: 2 }) },
      autoSize: false });
    chartRef.current = chart;

    const series = chart.addSeries(LineSeries, {
      color,
      lineWidth: 2 });
    series.setData(chartData);

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
  }, [chartData, colors, height, color]);

  return <div ref={containerRef} className="w-full" style={{ height }} />;
}
