"use client";

import { useEffect, useMemo, useRef } from "react";
import {
  createChart,
  AreaSeries,
  ColorType,
  CrosshairMode,
  type IChartApi,
  type UTCTimestamp,
  type AreaData } from "lightweight-charts";
import { useAppStore } from "@/store/useAppStore";

interface AreaChartProps {
  data: { time: string | UTCTimestamp; value: number }[];
  height?: number;
  lineColor?: string;
  fillColor?: string;
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

export function AreaChart({
  data,
  height = 320,
  lineColor = "#64748B",
  fillColor = "rgba(100,116,139,0.15)" }: AreaChartProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const { theme } = useAppStore();
  const colors = theme === "dark" ? DARK : LIGHT;

  const chartData = useMemo(
    () =>
      data.map((d) => ({
        time: d.time as AreaData["time"],
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
        locale: "en-US",
        priceFormatter: (p: number) => p.toLocaleString("en-US", { maximumFractionDigits: 2 }) },
      autoSize: false });
    chartRef.current = chart;

    const series = chart.addSeries(AreaSeries, {
      lineColor,
      topColor: fillColor,
      bottomColor: "rgba(100,116,139,0.0)" });
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
  }, [chartData, colors, height, lineColor, fillColor]);

  return <div ref={containerRef} className="w-full" style={{ height }} />;
}
