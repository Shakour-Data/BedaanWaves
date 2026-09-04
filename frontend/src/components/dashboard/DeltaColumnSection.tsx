"use client";

import { ColumnChart } from "@/components/charts/ColumnChart";
import { ChartSection, ChartEmpty, ChartLoading } from "./ChartSection";

interface DeltaColumnSectionProps {
  title: string;
  subtitle?: string;
  data: { time: string; value: number }[];
  height?: number;
  valueFormatter?: (value: number) => string;
  loading?: boolean;
  emptyMessage?: string;
}

export function DeltaColumnSection({
  title,
  subtitle,
  data,
  height = 220,
  valueFormatter,
  loading = false,
  emptyMessage = "No change data available",
}: DeltaColumnSectionProps) {
  if (loading) {
    return (
      <ChartSection title={title} subtitle={subtitle}>
        <ChartLoading />
      </ChartSection>
    );
  }

  if (!data || data.length === 0) {
    return (
      <ChartSection title={title} subtitle={subtitle}>
        <ChartEmpty message={emptyMessage} />
      </ChartSection>
    );
  }

  return (
    <ChartSection title={title} subtitle={subtitle}>
      <ColumnChart
        data={data.map((d) => ({
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
