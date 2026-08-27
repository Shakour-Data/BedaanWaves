import { cn } from "@/lib/cn";
import type { MarketStat } from "@/lib/dashboard-data";
import { semanticColors } from "@/styles/design-tokens";
import { ArrowUpIcon, ArrowDownIcon } from "@/components/icons/Icons";

export function ChangeBadge({ value }: { value: number }) {
  const up = value >= 0;
  const color = up ? semanticColors.success : semanticColors.error;
  return (
    <span
      className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold"
      style={{
        backgroundColor: `${color}26`,
        color,
      }}
    >
      {up ? <ArrowUpIcon className="h-3 w-3" /> : <ArrowDownIcon className="h-3 w-3" />}
      {Math.abs(value).toFixed(2)}٪
    </span>
  );
}

export function StatCard({ stat }: { stat: MarketStat }) {
  return (
    <article
      className={cn(
        "rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 shadow-sm"
      )}
    >
      <span className="text-sm text-muted-foreground">{stat.label}</span>
      <span className="mt-1 block text-xl font-bold text-foreground">{stat.value}</span>
      {stat.changePct !== undefined ? <ChangeBadge value={stat.changePct} /> : null}
    </article>
  );
}
