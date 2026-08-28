"use client";

import { useEffect, useMemo, useRef } from "react";
import { useAppStore } from "@/store/useAppStore";

interface CoefficientChartProps {
  data: { name: string; coefficient: number; color?: string }[];
  height?: number;
}

const LIGHT = {
  background: "#ffffff",
  text: "#475569",
  grid: "#E2E8F0",
  barBg: "#F1F5F9" };

const DARK = {
  background: "#1E293B",
  text: "#CBD5E1",
  grid: "#334155",
  barBg: "#334155" };

export function CoefficientChart({ data, height = 320 }: CoefficientChartProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const { theme } = useAppStore();
  const colors = theme === "dark" ? DARK : LIGHT;

  const maxValue = useMemo(() => Math.max(...data.map((d) => Math.abs(d.coefficient)), 1), [data]);

  useEffect(() => {
    const container = containerRef.current;
    const canvas = canvasRef.current;
    if (!container || !canvas) return;

    const resize = () => {
      const dpr = window.devicePixelRatio || 1;
      const width = container.clientWidth;
      const canvasHeight = height;

      canvas.width = width * dpr;
      canvas.height = canvasHeight * dpr;
      canvas.style.width = `${width}px`;
      canvas.style.height = `${canvasHeight}px`;

      const ctx = canvas.getContext("2d");
      if (!ctx) return;

      ctx.scale(dpr, dpr);
      ctx.clearRect(0, 0, width, canvasHeight);

      const padding = { top: 30, right: 40, bottom: 60, left: 50 };
      const chartWidth = width - padding.left - padding.right;
      const chartHeight = canvasHeight - padding.top - padding.bottom;

      if (data.length === 0 || chartWidth <= 0 || chartHeight <= 0) return;

      const barGap = 16;
      const barWidth = Math.max(20, (chartWidth - barGap * (data.length + 1)) / data.length);

      ctx.strokeStyle = colors.grid;
      ctx.lineWidth = 0.5;

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
        const val = (maxValue * i) / 4;
        ctx.fillText(val.toFixed(2), padding.left - 8, y);
      }

      ctx.strokeStyle = colors.grid;
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(padding.left, padding.top);
      ctx.lineTo(padding.left, padding.top + chartHeight);
      ctx.lineTo(padding.left + chartWidth, padding.top + chartHeight);
      ctx.stroke();

      const totalBarWidth = data.length * barWidth + (data.length - 1) * barGap;
      const startX = padding.left + (chartWidth - totalBarWidth) / 2;

      data.forEach((item, i) => {
        const barHeight = (Math.abs(item.coefficient) / maxValue) * chartHeight;
        const x = startX + i * (barWidth + barGap);
        const y = padding.top + chartHeight - barHeight;
        const barColor = item.color || "#2563EB";

        ctx.fillStyle = colors.barBg;
        ctx.fillRect(x, padding.top, barWidth, chartHeight);

        ctx.fillStyle = barColor;
        ctx.fillRect(x, y, barWidth, barHeight);

        ctx.fillStyle = colors.text;
        ctx.font = "bold 11px inherit";
        ctx.textAlign = "center";
        ctx.textBaseline = "bottom";
        ctx.fillText(item.coefficient.toFixed(2), x + barWidth / 2, y - 6);

        ctx.textBaseline = "top";
        ctx.font = "11px inherit";

        const words = item.name.split(" ");
        if (words.length > 2) {
          const mid = Math.ceil(words.length / 2);
          ctx.fillText(words.slice(0, mid).join(" "), x + barWidth / 2, padding.top + chartHeight + 6);
          ctx.fillText(words.slice(mid).join(" "), x + barWidth / 2, padding.top + chartHeight + 20);
        } else {
          ctx.fillText(item.name, x + barWidth / 2, padding.top + chartHeight + 8);
        }
      });
    };

    resize();
    const observer = new ResizeObserver(resize);
    observer.observe(container);

    return () => {
      observer.disconnect();
    };
  }, [data, maxValue, colors, height]);

  return <div ref={containerRef} className="w-full"><canvas ref={canvasRef} className="block" /></div>;
}
