"use client";

import { cn } from "@/lib/cn";
import { Button } from "@/components/ui/Button";

const CATEGORIES = [
  { key: "all", label: "All News", icon: "📰" },
  { key: "POLITICAL", label: "Political", icon: "🏛️" },
  { key: "ECONOMIC", label: "Economic", icon: "📊" },
  { key: "INTERNATIONAL", label: "International", icon: "🌍" },
  { key: "STOCK_MARKET", label: "Stock Market", icon: "📈" },
  { key: "INDUSTRY", label: "Industries", icon: "🏭" },
  { key: "COMPANY", label: "Companies", icon: "🏢" },
];

interface NewsCategoryFilterProps {
  selected: string | null;
  onChange: (category: string | null) => void;
}

export function NewsCategoryFilter({ selected, onChange }: NewsCategoryFilterProps) {
  return (
    <div className="space-y-1">
      {CATEGORIES.map((cat) => (
        <Button
          key={cat.key}
          variant="ghost"
          size="sm"
          className={cn(
            "w-full justify-start gap-2 px-3 py-2 text-sm font-medium transition-all",
            selected === cat.key
              ? "bg-[var(--color-primary)] text-white shadow-md"
              : "text-[var(--color-text-secondary)] hover:bg-[var(--color-muted)] hover:text-[var(--color-text-primary)]"
          )}
          onClick={() => onChange(cat.key === "all" ? null : cat.key)}
        >
          <span>{cat.icon}</span>
          <span>{cat.label}</span>
        </Button>
      ))}
      <div className="my-2 border-t border-[var(--color-border)]" />
      <Button
        variant="ghost"
        size="sm"
        className={cn(
          "w-full justify-start gap-2 px-3 py-2 text-sm font-medium transition-all",
          selected === "market-moving"
            ? "bg-red-600 text-white shadow-md"
            : "text-red-600 hover:bg-red-50"
        )}
        onClick={() => onChange(selected === "market-moving" ? null : "market-moving")}
      >
        <span>⚡</span>
        <span>Market Moving</span>
      </Button>
    </div>
  );
}
