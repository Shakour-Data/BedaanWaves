"use client";

import { cn } from "@/lib/cn";

interface ChartSectionProps {
  title: string;
  subtitle?: string;
  className?: string;
  children: React.ReactNode;
  action?: React.ReactNode;
}

export function ChartSection({ title, subtitle, className, children, action }: ChartSectionProps) {
  return (
    <div className={cn("rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm", className)}>
      <div className="mb-4 flex items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">{title}</h2>
          {subtitle && (
            <p className="mt-1 text-xs text-[var(--color-text-secondary)]">{subtitle}</p>
          )}
        </div>
        {action && <div className="shrink-0">{action}</div>}
      </div>
      {children}
    </div>
  );
}

export function ChartEmpty({ message = "No data available" }: { message?: string }) {
  return (
    <div className="flex min-h-[160px] items-center justify-center rounded-lg border border-dashed border-[var(--color-border)] bg-[var(--color-background)]">
      <p className="text-sm text-[var(--color-text-secondary)]">{message}</p>
    </div>
  );
}

export function ChartLoading() {
  return (
    <div className="flex items-center justify-center py-12">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-[var(--color-primary)] border-t-transparent" />
    </div>
  );
}
