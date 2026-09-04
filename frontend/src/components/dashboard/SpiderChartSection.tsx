"use client";

import { SpiderChart } from "@/components/charts/SpiderChart";
import { ChartSection, ChartEmpty, ChartLoading } from "./ChartSection";

interface SpiderChartSectionProps {
  title: string;
  subtitle?: string;
  data: { label: string; value: number }[];
  size?: number;
  color?: string;
  onLabelClick?: (label: string) => void;
  loading?: boolean;
  emptyMessage?: string;
}

export function SpiderChartSection({
  title,
  subtitle,
  data,
  size = 280,
  color = "#2563EB",
  onLabelClick,
  loading = false,
  emptyMessage = "No data available",
}: SpiderChartSectionProps) {
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
      <div className="flex justify-center">
        <SpiderChart data={data} size={size} color={color} onLabelClick={onLabelClick} />
      </div>
    </ChartSection>
  );
}
