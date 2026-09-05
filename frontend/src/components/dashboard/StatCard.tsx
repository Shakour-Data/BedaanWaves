import { cn } from "@/lib/cn";
import type { MarketStat } from "@/lib/dashboard-data";
import { Badge } from "@/components/ui/Badge";

export function ChangeBadge({ value }: { value: number }) {
  const up = value >= 0;
  return (
    <Badge variant={up ? "success" : "error"} size="sm">
      <span className="flex items-center gap-1 font-mono tabular-nums">
        {up ? "\u25B2" : "\u25BC"}
        {Math.abs(value).toFixed(2)}%
      </span>
    </Badge>
  );
}

export function StatCard({ stat }: { stat: MarketStat }) {
  return (
    <div
      className={cn(
        "rounded-xl border border-border bg-surface p-6 shadow-sm transition-all duration-200 hover:shadow-md hover:-translate-y-0.5"
      )}
    >
      <span className="text-sm font-medium text-muted-foreground">{stat.label}</span>
      <span className="mt-2 block text-2xl font-bold text-foreground tabular-nums">{stat.value}</span>
      <div className="mt-3">
        {stat.changePct !== undefined ? <ChangeBadge value={stat.changePct} /> : null}
      </div>
    </div>
  );
}
