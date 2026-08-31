import type { TickMarkFormatter, UTCTimestamp } from "lightweight-charts";

export type ChartTimeValue = string | number;

export interface NormalizedChartPoint {
  time: UTCTimestamp;
  value: number;
}

export function toTimestamp(
  time: ChartTimeValue,
  index: number,
  ordinalLabels: Map<number, string>,
): UTCTimestamp {
  if (typeof time === "number" && Number.isFinite(time)) {
    return time as UTCTimestamp;
  }
  if (typeof time === "string") {
    const parsed = Date.parse(time);
    if (!Number.isNaN(parsed)) {
      return Math.floor(parsed / 1000) as UTCTimestamp;
    }
    ordinalLabels.set(index, time);
  }
  return index as UTCTimestamp;
}

export function normalizeChartData(
  points: { time: ChartTimeValue; value: number }[],
  baseIndex = 0,
): { data: NormalizedChartPoint[]; ordinalLabels: Map<number, string> } {
  const ordinalLabels = new Map<number, string>();
  const data = points.map((p, i) => ({
    time: toTimestamp(p.time, baseIndex + i, ordinalLabels),
    value: p.value,
  }));
  return { data, ordinalLabels };
}

export function createOrdinalTickMarkFormatter(
  ordinalLabels: Map<number, string>,
): TickMarkFormatter {
  return (time) => {
    if (typeof time === "number") {
      const label = ordinalLabels.get(time);
      if (label) return label;
    }
    return "";
  };
}
