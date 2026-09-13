"use client";

import { cn } from "@/lib/cn";
import { Button } from "@/components/ui/Button";

const REGIONS = [
  { key: "all", label: "All Regions" },
  { key: "US", label: "United States" },
  { key: "EU", label: "Europe" },
  { key: "UK", label: "United Kingdom" },
  { key: "ASIA", label: "Asia Pacific" },
  { key: "MENA", label: "Middle East & Africa" },
  { key: "LATAM", label: "Latin America" },
  { key: "GLOBAL", label: "Global" },
];

interface NewsRegionFilterProps {
  selected: string | null;
  onChange: (region: string | null) => void;
}

export function NewsRegionFilter({ selected, onChange }: NewsRegionFilterProps) {
  return (
    <div className="space-y-1">
      {REGIONS.map((region) => (
        <Button
          key={region.key}
          variant="ghost"
          size="sm"
          className={cn(
            "w-full justify-start px-3 py-2 text-sm font-medium transition-all",
            selected === region.key
              ? "bg-[var(--color-primary)] text-white shadow-md"
              : "text-[var(--color-text-secondary)] hover:bg-[var(--color-muted)] hover:text-[var(--color-text-primary)]"
          )}
          onClick={() => onChange(region.key === "all" ? null : region.key)}
        >
          {region.label}
        </Button>
      ))}
    </div>
  );
}
