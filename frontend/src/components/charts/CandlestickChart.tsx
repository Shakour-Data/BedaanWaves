"use client";

/**
 * CandlestickChart.tsx
 * ---------------------------------------------------------------------------
 * نمودار کندل‌استیک OHLCV + هیستوگرام حجم، مبتنی بر lightweight-charts (v5).
 * - رنگ‌ها با تمِ روشن/تاریک (useAppStore) هماهنگ می‌شوند.
 * - نمودار با تغییر اندازه‌ی ظرف و تمِ برنامه، به‌روزرسانی می‌شود.
 * - حجم به‌صورت overlay در یک‌پنجم پایینِ نمودار رسم می‌شود.
 */

import { useEffect, useMemo, useRef } from "react";
import {
  createChart,
  CandlestickSeries,
  HistogramSeries,
  ColorType,
  CrosshairMode,
  type IChartApi,
  type UTCTimestamp,
  type CandlestickData,
  type HistogramData,
} from "lightweight-charts";
import { useAppStore } from "@/store/useAppStore";
import type { Candle, Timeframe } from "@/lib/api/stocks";

interface CandlestickChartProps {
  candles: Candle[];
  timeframe?: Timeframe;
  height?: number;
}

const INTRADAY: Timeframe[] = ["1m", "5m", "15m", "1h", "4h"];

/** زمانِ کندل را به قالبِ مناسبِ lightweight-charts تبدیل می‌کند. */
function toChartTime(timestamp: string, timeframe: Timeframe): UTCTimestamp | string {
  if (INTRADAY.includes(timeframe)) {
    return Math.floor(new Date(timestamp).getTime() / 1000) as UTCTimestamp;
  }
  // تایم‌فریم روزانه و بالاتر: قالب «YYYY-MM-DD» تا روزِ نمایش‌داده‌شده جابه‌جا نشود.
  return timestamp.slice(0, 10);
}

interface ThemeColors {
  background: string;
  text: string;
  grid: string;
  border: string;
  up: string;
  down: string;
  volUp: string;
  volDown: string;
}

const LIGHT: ThemeColors = {
  background: "#ffffff",
  text: "#5c5c5c",
  grid: "#eeeeee",
  border: "#e0e0e0",
  up: "#2e7d32",
  down: "#c62828",
  volUp: "rgba(46, 125, 50, 0.35)",
  volDown: "rgba(198, 40, 40, 0.35)",
};

const DARK: ThemeColors = {
  background: "#1e1e1e",
  text: "#a8a8a8",
  grid: "#2a2a2a",
  border: "#333333",
  up: "#4caf50",
  down: "#ef5350",
  volUp: "rgba(76, 175, 80, 0.35)",
  volDown: "rgba(239, 83, 80, 0.35)",
};

export function CandlestickChart({ candles, timeframe = "1d", height = 420 }: CandlestickChartProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const { theme } = useAppStore();
  const colors = theme === "dark" ? DARK : LIGHT;

  const { candleData, volumeData } = useMemo(() => {
    const cd: CandlestickData[] = [];
    const vd: HistogramData[] = [];
    for (const c of candles) {
      const time = toChartTime(c.timestamp, timeframe) as CandlestickData["time"];
      cd.push({ time, open: c.open, high: c.high, low: c.low, close: c.close });
      vd.push({
        time,
        value: c.volume,
        color: c.close >= c.open ? colors.volUp : colors.volDown,
      });
    }
    return { candleData: cd, volumeData: vd };
  }, [candles, timeframe, colors.volUp, colors.volDown]);

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
      rightPriceScale: { borderColor: colors.border },
      timeScale: { borderColor: colors.border, timeVisible: INTRADAY.includes(timeframe) },
      crosshair: { mode: CrosshairMode.Normal },
      localization: {
        locale: "fa-IR",
        priceFormatter: (p: number) => p.toLocaleString("fa-IR", { maximumFractionDigits: 2 }),
      },
      autoSize: false,
    });
    chartRef.current = chart;

    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: colors.up,
      downColor: colors.down,
      borderUpColor: colors.up,
      borderDownColor: colors.down,
      wickUpColor: colors.up,
      wickDownColor: colors.down,
    });
    candleSeries.setData(candleData);

    const volumeSeries = chart.addSeries(HistogramSeries, {
      priceFormat: { type: "volume" },
      priceScaleId: "volume",
    });
    volumeSeries.priceScale().applyOptions({
      scaleMargins: { top: 0.8, bottom: 0 },
    });
    volumeSeries.setData(volumeData);

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
    // بازسازی نمودار با تغییر داده یا تم (رنگ‌ها).
  }, [candleData, volumeData, colors, height, timeframe]);

  return <div ref={containerRef} className="w-full" style={{ height }} />;
}
