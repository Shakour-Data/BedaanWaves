"use client";

import { cn } from "@/lib/cn";

type HierarchyLevel = "dimension" | "sub_dimension" | "aspect" | "sub_aspect";

interface DimensionChartSelectorProps {
  level: HierarchyLevel;
  onLevelChange: (level: HierarchyLevel) => void;
  selectedKey: string;
  onKeyChange: (key: string) => void;
  availableKeys: string[];
  className?: string;
}

const LEVEL_LABELS: Record<HierarchyLevel, string> = {
  dimension: "Dimension",
  sub_dimension: "Sub-Dimension",
  aspect: "Aspect",
  sub_aspect: "Sub-Aspect",
};

export function DimensionChartSelector({
  level,
  onLevelChange,
  selectedKey,
  onKeyChange,
  availableKeys,
  className,
}: DimensionChartSelectorProps) {
  return (
    <div className={cn("flex flex-wrap items-center gap-2", className)}>
      <div className="flex rounded-lg bg-[var(--color-background)]/50 p-0.5">
        {(Object.keys(LEVEL_LABELS) as HierarchyLevel[]).map((lvl) => (
          <button
            key={lvl}
            type="button"
            onClick={() => onLevelChange(lvl)}
            className={cn(
              "px-2.5 py-1.5 text-xs font-semibold rounded-md transition-all",
              level === lvl
                ? "bg-[var(--color-primary)] text-white shadow-sm"
                : "text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]"
            )}
          >
            {LEVEL_LABELS[lvl]}
          </button>
        ))}
      </div>
      <select
        value={selectedKey}
        onChange={(e) => onKeyChange(e.target.value)}
        className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-1.5 text-xs font-medium text-[var(--color-text-primary)] focus:border-[var(--color-primary)] focus:outline-none"
      >
        {availableKeys.map((key) => (
          <option key={key} value={key}>
            {key.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
          </option>
        ))}
      </select>
    </div>
  );
}
