"use client";

import { cn } from "@/lib/cn";
import type { NewsItem } from "@/lib/dashboard-data";

interface NewsListProps {
  items: NewsItem[];
  className?: string;
}

export function NewsList({ items, className }: NewsListProps) {
  if (items.length === 0) {
    return <ul className={cn("space-y-0", className)} />;
  }

  return (
    <ul className={cn("space-y-0", className)}>
      {items.map((item, index) => (
        <li key={index} className="border-b border-[var(--color-border)] px-4 py-3 last:border-b-0 hover:bg-[var(--color-background)]">
          <p className="font-medium text-[var(--color-text-primary)] text-sm">{item.title}</p>
          <div className="flex items-center gap-2 mt-1 text-xs text-[var(--color-text-secondary)]">
            <span>{item.source}</span>
            <span>•</span>
            <span>{item.time}</span>
          </div>
        </li>
      ))}
    </ul>
  );
}
