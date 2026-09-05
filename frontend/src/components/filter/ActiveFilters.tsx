"use client";

import { X } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import type { AdvancedFilterResponse } from "@/types/filter";
import { LEVEL_LABELS, LEVEL_COLORS } from "@/types/filter";

interface ActiveFiltersProps {
  applied: AdvancedFilterResponse["applied_filters"];
  onClearAll: () => void;
}

export function ActiveFilters({ applied, onClearAll }: ActiveFiltersProps) {
  if (applied.length === 0) return null;

  return (
    <div className="flex flex-wrap items-center gap-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 shadow-sm">
      <span className="text-xs font-semibold uppercase tracking-wider text-[var(--color-text-secondary)]">
        Active Filters:
      </span>
      {applied.map((f, idx) => (
        <Badge
          key={idx}
          size="sm"
          variant="neutral"
          className="gap-1"
        >
          <span
            className="h-2 w-2 rounded-full"
            style={{ backgroundColor: LEVEL_COLORS[f.level as keyof typeof LEVEL_COLORS] }}
          />
          <span className="font-medium">{f.field}</span>
          <span className="text-[var(--color-text-secondary)]">{f.operator}</span>
          <span className="max-w-[120px] truncate text-[var(--color-text-secondary)]">
            {String(f.value)}
          </span>
        </Badge>
      ))}
      <Button size="sm" variant="ghost" onClick={onClearAll} className="ml-auto">
        <X className="h-4 w-4" /> Clear All
      </Button>
    </div>
  );
}
