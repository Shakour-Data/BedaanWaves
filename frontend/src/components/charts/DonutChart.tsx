"use client";

import { useMemo } from "react";

interface DonutChartProps {
  data: { label: string; value: number; color?: string }[];
  size?: number;
  thickness?: number;
}

const DEFAULT_COLORS = [
  "#2563EB",
  "#10B981",
  "#F59E0B",
  "#EF4444",
  "#8B5CF6",
  "#EC4899",
  "#06B6D4",
  "#F97316",
];

export function DonutChart({ data, size = 240, thickness = 40 }: DonutChartProps) {
  const total = data.reduce((sum, d) => sum + d.value, 0);
  const radius = (size - thickness) / 2;
  const circumference = 2 * Math.PI * radius;

  const offsets = useMemo(() => {
    const result: number[] = [];
    let currentOffset = 0;
    for (const d of data) {
      result.push(currentOffset);
      const fraction = d.value / total;
      currentOffset += fraction * circumference;
    }
    return result;
  }, [data, total, circumference]);

  const segments = useMemo(() => {
    return data.map((d, i) => ({
      ...d,
      fraction: d.value / total,
      segmentLength: (d.value / total) * circumference,
      offset: offsets[i] ?? 0,
      color: d.color || DEFAULT_COLORS[i % DEFAULT_COLORS.length],
    }));
  }, [data, total, circumference, offsets]);

  if (total <= 0 || data.length === 0) {
    return (
      <div
        className="flex items-center justify-center text-muted-foreground"
        style={{ width: size, height: size }}
      >
        No data
      </div>
    );
  }

  const center = size / 2;

  return (
    <div className="relative inline-flex flex-col items-center gap-4">
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        className="transform -rotate-90"
      >
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke="var(--color-border)"
          strokeWidth={thickness}
        />
        {segments.map((seg, i) => (
          <circle
            key={i}
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            stroke={seg.color}
            strokeWidth={thickness}
            strokeDasharray={`${seg.segmentLength} ${circumference - seg.segmentLength}`}
            strokeDashoffset={-seg.offset}
            strokeLinecap="butt"
          />
        ))}
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-bold text-[var(--color-text-primary)]">
          {total >= 1 ? `${(total * 100).toFixed(0)}%` : total.toFixed(2)}
        </span>
        <span className="text-xs text-[var(--color-text-muted)]">Total</span>
      </div>
      <div className="flex flex-wrap justify-center gap-3">
        {segments.map((seg, i) => (
          <div key={i} className="flex items-center gap-2">
            <span
              className="inline-block h-2.5 w-2.5 rounded-full"
              style={{ backgroundColor: seg.color }}
            />
            <span className="text-xs text-[var(--color-text-secondary)]">
              {seg.label} {((seg.value / total) * 100).toFixed(1)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
