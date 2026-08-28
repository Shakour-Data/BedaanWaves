"use client";

import { useEffect, useMemo, useRef } from "react";
import { useAppStore } from "@/store/useAppStore";
import { cn } from "@/lib/cn";

export interface ScoreTrendChartProps {
  data: { date: string; scores: Record<string, number> }[];
  selectedDimensions: string[];
  height?: number;
}

const LIGHT = {
  background: "#ffffff",
  text: "#475569",
  grid: "#E2E8F0",
  border: "#CBD5E1" };

const DARK = {
  background: "#1E293B",
  text: "#CBD5E1",
  grid: "#334155",
  border: "#475569" };

const DIMENSION_COLORS: Record<string, string> = {
  fundamental: "#2563EB",
  technical: "#10B981",
  sentiment: "#F59E0B",
  risk: "#EF4444",
  macro: "#8B5CF6",
  ai: "#06B6D4" };

const DEFAULT_COLORS = [
  "#2563EB",
  "#10B981",
  "#F59E0B",
  "#EF4444",
  "#8B5CF6",
  "#06B6D4",
  "#EC4899",
  "#84CC16",
  "#F97316",
  "#14B8A6" ];

export function ScoreTrendChart({ data, selectedDimensions, height = 360 }: ScoreTrendChartProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const { theme } = useAppStore();
  const colors = theme === "dark" ? DARK : LIGHT;

  const dimensions = useMemo(() => {
    if (data.length === 0) return [];
    const first = data[0].scores;
    return Object.keys(first).filter((d) => selectedDimensions.includes(d));
  }, [data, selectedDimensions]);

  const dates = useMemo(() => data.map((d) => d.date), [data]);

  const colorMap = useMemo(() => {
    const map: Record<string, string> = {};
    dimensions.forEach((dim, i) => {
      map[dim] = DIMENSION_COLORS[dim] || DEFAULT_COLORS[i % DEFAULT_COLORS.length];
    });
    return map;
  }, [dimensions]);

  useEffect(() => {
    const container = containerRef.current;
    const canvas = canvasRef.current;
    if (!container || !canvas) return;

    const resize = () => {
      const dpr = window.devicePixelRatio || 1;
      const width = container.clientWidth;
      const canvasHeight = height - 48;

      canvas.width = width * dpr;
      canvas.height = canvasHeight * dpr;
      canvas.style.width = `${width}px`;
      canvas.style.height = `${canvasHeight}px`;

      const ctx = canvas.getContext("2d");
      if (!ctx) return;

      ctx.scale(dpr, dpr);
      ctx.clearRect(0, 0, width, canvasHeight);

      const padding = { top: 20, right: 20, bottom: 30, left: 40 };
      const chartWidth = width - padding.left - padding.right;
      const chartHeight = canvasHeight - padding.top - padding.bottom;

      ctx.strokeStyle = colors.grid;
      ctx.lineWidth = 0.5;
      ctx.setLineDash([4, 4]);

      for (let i = 0; i <= 4; i++) {
        const y = padding.top + chartHeight * (1 - i / 4);
        ctx.beginPath();
        ctx.moveTo(padding.left, y);
        ctx.lineTo(padding.left + chartWidth, y);
        ctx.stroke();

        ctx.fillStyle = colors.text;
        ctx.font = "11px inherit";
        ctx.textAlign = "right";
        ctx.textBaseline = "middle";
        ctx.fillText(String(i * 25), padding.left - 8, y);
      }
      ctx.setLineDash([]);

      ctx.strokeStyle = colors.border;
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(padding.left, padding.top);
      ctx.lineTo(padding.left, padding.top + chartHeight);
      ctx.lineTo(padding.left + chartWidth, padding.top + chartHeight);
      ctx.stroke();

      const xStep = dates.length > 1 ? chartWidth / (dates.length - 1) : 0;

      dimensions.forEach((dim) => {
        const color = colorMap[dim];
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.beginPath();

        data.forEach((d, i) => {
          const x = padding.left + i * xStep;
          const y = padding.top + chartHeight * (1 - d.scores[dim] / 100);
          if (i === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        });
        ctx.stroke();

        data.forEach((d, i) => {
          const x = padding.left + i * xStep;
          const y = padding.top + chartHeight * (1 - d.scores[dim] / 100);
          ctx.beginPath();
          ctx.arc(x, y, 3, 0, 2 * Math.PI);
          ctx.fillStyle = color;
          ctx.fill();
        });
      });

      ctx.fillStyle = colors.text;
      ctx.font = "11px inherit";
      ctx.textAlign = "center";
      ctx.textBaseline = "top";

      const maxLabels = Math.min(dates.length, 6);
      const labelStep = dates.length > 1 ? Math.floor(dates.length / maxLabels) : 1;

      dates.forEach((date, i) => {
        if (i % labelStep === 0 || i === dates.length - 1) {
          const x = padding.left + i * xStep;
          ctx.fillText(date.slice(5), x, padding.top + chartHeight + 8);
        }
      });
    };

    resize();
    const observer = new ResizeObserver(resize);
    observer.observe(container);

    return () => {
      observer.disconnect();
    };
  }, [data, dimensions, dates, colorMap, colors, height]);

  return (
    <div className="w-full">
      <div className="mb-3 flex flex-wrap gap-3">
        {dimensions.map((dim) => (
          <label
            key={dim}
            className={cn(
              "flex items-center gap-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-1.5 text-xs font-medium capitalize transition-colors",
              "cursor-pointer select-none"
            )}
          >
            <input
              type="checkbox"
              checked
              readOnly
              className="h-3.5 w-3.5 rounded border-[var(--color-border)] accent-[var(--color-primary)]"
            />
            <span
              className="h-2 w-2 rounded-full"
              style={{ backgroundColor: colorMap[dim] }}
            />
            {dim}
          </label>
        ))}
      </div>
      <div ref={containerRef} className="relative w-full">
        <canvas ref={canvasRef} className="block w-full" style={{ height: height - 48 }} />
      </div>
    </div>
  );
}
