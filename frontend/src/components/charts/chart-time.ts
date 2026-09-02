import type { TickMarkFormatter, UTCTimestamp } from "lightweight-charts";

export type ChartTimeValue = string | number;

const ISO_DATE_PATTERN = /^\d{4}-\d{2}-\d{2}([T ]\d{2}:\d{2}(:\d{2}(\.\d+)?)?(Z|[+-]\d{2}:?\d{2})?)?$/;

export function isDateString(value: unknown): value is string {
  return typeof value === "string" && ISO_DATE_PATTERN.test(value) && !Number.isNaN(Date.parse(value));
}

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
  if (isDateString(time)) {
    return Math.floor(Date.parse(time) / 1000) as UTCTimestamp;
  }
  if (typeof time === "string") {
    ordinalLabels.set(index, time);
  }
  return index as UTCTimestamp;
}

export function normalizeChartData(
  points: { time: ChartTimeValue; value: number }[],
): { data: NormalizedChartPoint[]; ordinalLabels: Map<number, string> } {
  const ordinalLabels = new Map<number, string>();
  const data = points.map((p, i) => ({
    time: toTimestamp(p.time, i, ordinalLabels),
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

export function createDateTickMarkFormatter(): TickMarkFormatter {
  return (time, tickMarkType) => {
    if (typeof time === "number") {
      const date = new Date(time * 1000);
      switch (tickMarkType) {
        case 0:
          return String(date.getFullYear());
        case 1:
          return date.toLocaleString("en-US", { month: "short" });
        case 2:
          return String(date.getDate());
        default:
          return date.toLocaleString("en-US", { month: "short", day: "numeric" });
      }
    }
    return null;
  };
}
