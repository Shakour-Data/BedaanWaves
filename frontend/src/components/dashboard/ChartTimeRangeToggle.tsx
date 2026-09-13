"use client";

import { useState } from "react";
import { cn } from "@/lib/cn";

type TimeRange = "6h" | "24h" | "7d" | "30d" | "90d" | "1y";

interface ChartTimeRangeToggleProps {
  value: TimeRange;
  onChange: (value: TimeRange) => void;
  className?: string;
}

const INTRADAY_RANGES: TimeRange[] = ["6h", "24h", "7d"];
const HISTORICAL_RANGES: TimeRange[] = ["30d", "90d", "1y"];

export function ChartTimeRangeToggle({
  value,
  onChange,
  className,
}: ChartTimeRangeToggleProps) {
  const [mode, setMode] = useState<"intraday" | "historical">(
    INTRADAY_RANGES.includes(value) ? "intraday" : "historical"
  );

  const handleModeChange = (newMode: "intraday" | "historical") => {
    setMode(newMode);
    const ranges = newMode === "intraday" ? INTRADAY_RANGES : HISTORICAL_RANGES;
    onChange(ranges[0]);
  };

  return (
    <div className={cn("flex items-center gap-1 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-1", className)}>
      <div className="flex rounded-lg bg-[var(--color-background)]/50 p-0.5">
        <button
          type="button"
          onClick={() => handleModeChange("intraday")}
          className={cn(
            "px-3 py-1.5 text-xs font-semibold rounded-md transition-all",
            mode === "intraday"
              ? "bg-[var(--color-primary)] text-white shadow-sm"
              : "text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]"
          )}
        >
          Intraday
        </button>
        <button
          type="button"
          onClick={() => handleModeChange("historical")}
          className={cn(
            "px-3 py-1.5 text-xs font-semibold rounded-md transition-all",
            mode === "historical"
              ? "bg-[var(--color-primary)] text-white shadow-sm"
              : "text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]"
          )}
        >
          Historical
        </button>
      </div>
      <div className="h-4 w-px bg-[var(--color-border)]" />
      <div className="flex gap-1">
        {(mode === "intraday" ? INTRADAY_RANGES : HISTORICAL_RANGES).map((range) => (
          <button
            key={range}
            type="button"
            onClick={() => onChange(range)}
            className={cn(
              "px-2.5 py-1.5 text-xs font-medium rounded-md transition-all",
              value === range
                ? "bg-[var(--color-primary-soft)] text-[var(--color-primary)]"
                : "text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]"
            )}
          >
            {range}
          </button>
        ))}
      </div>
    </div>
  );
}
