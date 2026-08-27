import { cn } from "@/lib/cn";
import type { MarketStat } from "@/lib/dashboard-data";
import { ArrowUpIcon, ArrowDownIcon } from "@/components/icons/Icons";

export function ChangeBadge({ value }: { value: number }) {
  const up = value >= 0;
  return (
    <span
      className={cn(
        "rounded-full px-2 py-0.5 text-xs font-semibold",
        up ? "bg-success/15 text-success" : "bg-error/15 text-error"
      )}
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
        "rounded-xl border border-border bg-surface p-4 shadow-sm transition duration-fast ease-flow hover:shadow-md"
      )}
    >
      <span className="text-sm text-muted-foreground">{stat.label}</span>
      <span className="mt-1 block text-xl font-bold text-foreground">{stat.value}</span>
      <div className="mt-2">
        {stat.changePct !== undefined ? <ChangeBadge value={stat.changePct} /> : null}
      </div>
    </article>
  );
}
