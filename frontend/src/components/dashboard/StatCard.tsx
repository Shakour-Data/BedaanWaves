import { cn } from "@/lib/cn";
import type { MarketStat } from "@/lib/dashboard-data";

export function ChangeBadge({ value }: { value: number }) {
  const up = value >= 0;
  return (
    <span
      className={cn(
        "rounded-full px-2 py-0.5 text-xs font-semibold",
        up ? "bg-success/15 text-success" : "bg-primary/15 text-primary",
      )}
    >
      {up ? "▲" : "▼"} {Math.abs(value).toFixed(2)}٪
    </span>
  );
}

export function StatCard({ stat }: { stat: MarketStat }) {
  return (
    <article className="tarot-card flex flex-col gap-1">
      <span className="text-sm text-muted-foreground">{stat.label}</span>
      <span className="text-xl font-bold">{stat.value}</span>
      {stat.changePct !== undefined ? <ChangeBadge value={stat.changePct} /> : null}
    </article>
  );
}
