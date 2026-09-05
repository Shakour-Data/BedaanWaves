import { cn } from "@/lib/cn";

export interface MarketStat {
  label: string;
  value: string;
  changePct?: number;
}

interface StatCardProps {
  stat: MarketStat;
  className?: string;
}

export function StatCard({ stat, className }: StatCardProps) {
  const changePct = stat.changePct ?? 0;
  const isPositive = changePct >= 0;
  const changeColor = isPositive ? "text-[var(--color-success)]" : "text-[var(--color-error)]";

  return (
    <div className={cn("rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm", className)}>
      <p className="text-sm font-medium text-[var(--color-text-secondary)]">{stat.label}</p>
      <p className="mt-2 text-2xl font-bold text-[var(--color-text-primary)] tabular-nums">{stat.value}</p>
      {stat.changePct !== undefined && (
        <p className={cn("mt-1 text-sm font-medium", changeColor)}>
          {isPositive ? "+" : ""}{changePct.toFixed(2)}%
        </p>
      )}
    </div>
  );
}

interface ChangeBadgeProps {
  value: number;
  className?: string;
}

export function ChangeBadge({ value, className }: ChangeBadgeProps) {
  const isPositive = value >= 0;
  const colorClass = isPositive
    ? "bg-success/10 text-success"
    : "bg-error/10 text-error";

  return (
    <span className={cn("inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium", colorClass, className)}>
      <span>{isPositive ? "+" : ""}{value.toFixed(2)}%</span>
    </span>
  );
}
