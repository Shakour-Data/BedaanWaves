"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { cn } from "@/lib/cn";

interface DashboardTabNavProps {
  tabs: Array<{ id: string; label: string; href: string }>;
}

export function DashboardTabNav({ tabs }: DashboardTabNavProps) {
  const searchParams = useSearchParams();
  const active = searchParams.get("tab") || "overview";
  return (
    <nav
      role="tablist"
      aria-label="Dashboard views"
      className="inline-flex items-center gap-1 rounded-lg bg-[var(--color-surface)]/60 p-1 text-sm font-medium ring-1 ring-[var(--color-border)]"
    >
      {tabs.map((tab) => {
        const selected = active === tab.id;
        return (
          <Link
            key={tab.id}
            href={tab.href}
            role="tab"
            aria-selected={selected}
            className={cn(
              "inline-flex items-center justify-center rounded-md px-3.5 py-2 whitespace-nowrap outline-none",
              selected
                ? "bg-[var(--color-primary)] text-white shadow-sm"
                : "text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface)]",
            )}
          >
            {tab.label}
          </Link>
        );
      })}
    </nav>
  );
}
