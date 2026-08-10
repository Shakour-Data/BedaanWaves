import { cn } from "@/lib/cn";
import type { MarketStat } from "@/lib/dashboard-data";
import { semanticColors, fontSizes } from "@/styles/design-tokens";

export function ChangeBadge({ value }: { value: number }) {
  const up = value >= 0;
  return (
    <span
      className={cn(
        "rounded-full px-2 py-0.5 text-xs font-semibold",
        up
          ? `bg-[${semanticColors.success}]/15 text-[${semanticColors.success}]`
          : `bg-[${semanticColors.error}]/15 text-[${semanticColors.error}]`,
      )}
    >
      {up ? "▲" : "▼"} {Math.abs(value).toFixed(2)}٪
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
