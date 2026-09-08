"use client";

import { useState } from "react";
import { cn } from "@/lib/cn";

export type Level = "overall" | "dimension" | "sub_dimension" | "aspect" | "sub_aspect";

interface LevelSelectorProps {
  level: Level;
  dimension?: string;
  onLevelChange: (level: Level) => void;
  onDimensionChange?: (dimension: string) => void;
  className?: string;
}

const LEVELS: { id: Level; label: string }[] = [
  { id: "overall", label: "Overall" },
  { id: "dimension", label: "Dimensions" },
  { id: "sub_dimension", label: "Sub-Dimensions" },
  { id: "aspect", label: "Aspects" },
  { id: "sub_aspect", label: "Sub-Aspects" },
];

const CANONICAL_DIMENSIONS = [
  { id: "fundamental", label: "Fundamental", color: "#10B981" },
  { id: "technical", label: "Technical", color: "#2563EB" },
  { id: "sentiment", label: "Sentiment", color: "#F59E0B" },
  { id: "risk", label: "Risk", color: "#EF4444" },
  { id: "macro", label: "Macro", color: "#8B5CF6" },
  { id: "ai", label: "AI", color: "#EC4899" },
];

export function LevelSelector({
  level,
  dimension,
  onLevelChange,
  onDimensionChange,
  className,
}: LevelSelectorProps) {
  const [activeDimension, setActiveDimension] = useState<string>(dimension || CANONICAL_DIMENSIONS[0].id);

  const handleDimensionClick = (dim: string) => {
    setActiveDimension(dim);
    if (onDimensionChange) {
      onDimensionChange(dim);
    }
  };

  return (
    <div className={cn("space-y-4", className)}>
      <div className="flex flex-wrap items-center gap-2">
        {LEVELS.map((lvl) => (
          <button
            key={lvl.id}
            type="button"
            onClick={() => onLevelChange(lvl.id)}
            className={cn(
              "rounded-lg px-4 py-2.5 text-sm font-medium transition-all min-h-[44px]",
              level === lvl.id
                ? "bg-[var(--color-primary)] text-white shadow-sm"
                : "bg-[var(--color-background)] text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-border)] active:bg-[var(--color-border)]/80"
            )}
          >
            {lvl.label}
          </button>
        ))}
      </div>

      {level !== "overall" && (
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-medium text-[var(--color-text-secondary)] uppercase tracking-wider">
            Select Dimension:
          </span>
          {CANONICAL_DIMENSIONS.map((dim) => (
            <button
              key={dim.id}
              type="button"
              onClick={() => handleDimensionClick(dim.id)}
              className={cn(
                "flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-all border min-h-[44px]",
                activeDimension === dim.id
                  ? "border-[var(--color-primary)] bg-[var(--color-primary)]/10 text-[var(--color-primary)]"
                  : "border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] active:bg-muted"
              )}
            >
              <span
                className="inline-block h-2.5 w-2.5 rounded-full"
                style={{ backgroundColor: dim.color }}
              />
              {dim.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
