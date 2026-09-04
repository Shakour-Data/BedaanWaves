"use client";

import { useMemo } from "react";
import { ScoreTrendChart } from "@/components/charts/ScoreTrendChart";
import { ColumnChart } from "@/components/charts/ColumnChart";
import { ChartSection, ChartEmpty, ChartLoading } from "./ChartSection";

interface SeriesDef {
  key: string;
  label: string;
  color: string;
  data: { time: string; value: number }[];
}

interface CoefficientTrendSectionProps {
  title: string;
  subtitle?: string;
  series: SeriesDef[];
  height?: number;
  showLegend?: boolean;
  type?: "line" | "column";
  valueFormatter?: (value: number) => string;
  loading?: boolean;
  emptyMessage?: string;
}

const DIMENSION_COLORS = [
  "#2563EB",
  "#10B981",
  "#F59E0B",
  "#EF4444",
  "#8B5CF6",
  "#EC4899",
  "#06B6D4",
  "#F97316",
];

export function CoefficientTrendSection({
  title,
  subtitle,
  series,
  height = 240,
  showLegend = false,
  type = "line",
  valueFormatter,
  loading = false,
  emptyMessage = "No coefficient data available",
}: CoefficientTrendSectionProps) {
  const coloredSeries = useMemo(
    () =>
      series.map((s, i) => ({
        ...s,
        color: s.color || DIMENSION_COLORS[i % DIMENSION_COLORS.length],
      })),
    [series]
  );

  if (loading) {
    return (
      <ChartSection title={title} subtitle={subtitle}>
        <ChartLoading />
      </ChartSection>
    );
  }

  if (coloredSeries.length === 0 || coloredSeries.every((s) => s.data.length === 0)) {
    return (
      <ChartSection title={title} subtitle={subtitle}>
        <ChartEmpty message={emptyMessage} />
      </ChartSection>
    );
  }

  const hasMultipleSeries = coloredSeries.length > 1;

  if (type === "column") {
    const firstSeries = coloredSeries[0];
    return (
      <ChartSection title={title} subtitle={subtitle}>
        <ColumnChart
          data={firstSeries.data.map((d) => ({
            time: d.time,
            value: d.value,
            color: d.value >= 0 ? "#10b981" : "#ef4444",
          }))}
          height={height}
          valueFormatter={valueFormatter}
        />
      </ChartSection>
    );
  }

  return (
    <ChartSection title={title} subtitle={subtitle}>
      <ScoreTrendChart
        showLegend={showLegend && hasMultipleSeries}
        series={coloredSeries}
        height={height}
      />
    </ChartSection>
  );
}
