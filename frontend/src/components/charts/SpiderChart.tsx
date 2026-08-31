"use client";

import { useEffect, useMemo, useRef } from "react";
import { useAppStore } from "@/store/useAppStore";

interface SpiderChartProps {
  data: { label: string; value: number }[];
  size?: number;
  color?: string;
  onLabelClick?: (label: string) => void;
}

const LIGHT = {
  grid: "#E2E8F0",
  axis: "#94A3B8",
  text: "#475569",
  bg: "#FFFFFF" };

const DARK = {
  grid: "#334155",
  axis: "#64748B",
  text: "#CBD5E1",
  bg: "#1E293B" };

const DIMENSION_COLORS = [
  "#2563EB",
  "#10B981",
  "#F59E0B",
  "#EF4444",
  "#8B5CF6",
  "#06B6D4",
  "#EC4899",
  "#84CC16" ];

export function SpiderChart({ data, size = 360, color = "#2563EB", onLabelClick }: SpiderChartProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const { theme } = useAppStore();
  const colors = theme === "dark" ? DARK : LIGHT;

  const levels = 5;
  const max = 100;

  const angleStep = useMemo(() => data.length > 0 ? (2 * Math.PI) / data.length : 0, [data.length]);

  const getLabelAtPosition = (clientX: number, clientY: number): string | null => {
    const canvas = canvasRef.current;
    if (!canvas || data.length === 0) return null;

    const rect = canvas.getBoundingClientRect();
    const x = clientX - rect.left;
    const y = clientY - rect.top;
    const center = size / 2;
    const radius = Math.min(size, size) * 0.38;
    const labelRadius = radius + 22;

    const dx = x - center;
    const dy = y - center;
    const dist = Math.sqrt(dx * dx + dy * dy);

    if (dist < labelRadius - 15 || dist > labelRadius + 30) return null;

    let angle = Math.atan2(dy, dx) + Math.PI / 2;
    if (angle < 0) angle += 2 * Math.PI;

    for (let i = 0; i < data.length; i++) {
      const labelAngle = i * angleStep;
      let diff = angle - labelAngle;
      while (diff > Math.PI) diff -= 2 * Math.PI;
      while (diff < -Math.PI) diff += 2 * Math.PI;

      if (Math.abs(diff) < angleStep / 2) {
        return data[i].label;
      }
    }

    return null;
  };

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || data.length === 0) return;

    const dpr = window.devicePixelRatio || 1;
    const width = size;
    const height = size;

    canvas.width = width * dpr;
    canvas.height = height * dpr;
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, width, height);

    const center = width / 2;
    const radius = Math.min(width, height) * 0.38;

    ctx.strokeStyle = colors.grid;
    ctx.lineWidth = 0.5;

    for (let level = 1; level <= levels; level++) {
      const levelRadius = radius * (level / levels);
      ctx.beginPath();
      for (let i = 0; i < data.length; i++) {
        const angle = i * angleStep - Math.PI / 2;
        const x = center + levelRadius * Math.cos(angle);
        const y = center + levelRadius * Math.sin(angle);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.closePath();
      ctx.stroke();
    }

    ctx.strokeStyle = colors.axis;
    ctx.lineWidth = 0.5;
    for (let i = 0; i < data.length; i++) {
      const angle = i * angleStep - Math.PI / 2;
      const x = center + radius * Math.cos(angle);
      const y = center + radius * Math.sin(angle);
      ctx.beginPath();
      ctx.moveTo(center, center);
      ctx.lineTo(x, y);
      ctx.stroke();
    }

    ctx.beginPath();
    for (let i = 0; i < data.length; i++) {
      const value = Math.min(data[i].value, max);
      const r = radius * (value / max);
      const angle = i * angleStep - Math.PI / 2;
      const x = center + r * Math.cos(angle);
      const y = center + r * Math.sin(angle);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.closePath();
    ctx.fillStyle = color ? `${color}26` : "#2563EB26";
    ctx.fill();
    ctx.strokeStyle = color || "#2563EB";
    ctx.lineWidth = 2;
    ctx.stroke();

    for (let i = 0; i < data.length; i++) {
      const value = Math.min(data[i].value, max);
      const r = radius * (value / max);
      const angle = i * angleStep - Math.PI / 2;
      const x = center + r * Math.cos(angle);
      const y = center + r * Math.sin(angle);

      ctx.beginPath();
      ctx.arc(x, y, 4, 0, 2 * Math.PI);
      ctx.fillStyle = color || "#2563EB";
      ctx.fill();
    }

    ctx.fillStyle = colors.text;
    ctx.font = "12px inherit";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";

    for (let i = 0; i < data.length; i++) {
      const angle = i * angleStep - Math.PI / 2;
      const labelRadius = radius + 22;
      const x = center + labelRadius * Math.cos(angle);
      const y = center + labelRadius * Math.sin(angle);

      ctx.fillText(data[i].label, x, y);
    }
  }, [data, size, color, colors, angleStep]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !onLabelClick) return;

    const handleClick = (event: MouseEvent) => {
      const label = getLabelAtPosition(event.clientX, event.clientY);
      if (label) {
        onLabelClick(label);
      }
    };

    canvas.addEventListener("click", handleClick);
    return () => canvas.removeEventListener("click", handleClick);
  }, [onLabelClick, data]);

  return (
    <div className="relative inline-flex items-center justify-center">
      <canvas ref={canvasRef} className="block" style={{ cursor: onLabelClick ? "pointer" : "default" }} />
    </div>
  );
}

export { DIMENSION_COLORS };
