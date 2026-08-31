import type { UTCTimestamp } from "lightweight-charts";

export function toTimestamp(
  time: string | UTCTimestamp,
  index: number,
  ordinalLabels: Map<number, string>
): UTCTimestamp {
  if (typeof time === "number") {
    return time;
  }

  const trimmed = time.trim();

  const numeric = Number(trimmed);
  if (!Number.isNaN(numeric) && String(numeric) === trimmed) {
    return numeric as UTCTimestamp;
  }

  const date = new Date(trimmed);
  if (!Number.isNaN(date.getTime())) {
    return Math.floor(date.getTime() / 1000) as UTCTimestamp;
  }

  ordinalLabels.set(index, trimmed);
  return index as UTCTimestamp;
}
