"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  createChart,
  LineSeries,
  ColorType,
  CrosshairMode,
  type IChartApi,
  type UTCTimestamp,
  type LineData,
} from "lightweight-charts";
import { useAppStore } from "@/store/useAppStore";

interface SeriesDef {
  key: string;
  label: string;
  color: string;
  data: { time: string | UTCTimestamp; value: number }[];
}

interface ScoreTrendChartProps {
  series: SeriesDef[];
  height?: number;
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

export function ScoreTrendChart({ series, height = 360 }: ScoreTrendChartProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRefs = useRef<unknown[]>([]);
  const { theme } = useAppStore();
  const colors = theme === "dark" ? DARK : LIGHT;

  const visibleSeries = useMemo(
    () =>
      series.map((s, i) => ({
        ...s,
        color: s.color || PALETTE[i % PALETTE.length],
      })),
    [series]
  );

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

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
      timeScale: { borderColor: colors.border },
      crosshair: { mode: CrosshairMode.Normal },
      localization: {
        locale: "fa-IR",
        priceFormatter: (p: number) => p.toLocaleString("fa-IR", { maximumFractionDigits: 2 }),
      },
      autoSize: false,
    });
    chartRef.current = chart;

    seriesRefs.current = [];
    for (const s of visibleSeries) {
      const line = chart.addSeries(LineSeries, {
        color: s.color,
        lineWidth: 2,
        priceScaleId: "right",
      });
      line.setData(
        s.data.map((d) => ({
          time: d.time as LineData["time"],
          value: d.value,
        }))
      );
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
  }, [visibleSeries, colors, height]);

  return (
    <div className="w-full">
      <div ref={containerRef} className="w-full" style={{ height }} />
    </div>
  );
}
