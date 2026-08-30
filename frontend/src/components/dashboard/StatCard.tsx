import { cn } from "@/lib/cn";
import type { MarketStat } from "@/lib/dashboard-data";
import { ArrowUpIcon, ArrowDownIcon } from "@/components/icons/Icons";
import { Badge } from "@/components/ui/Badge";

export function ChangeBadge({ value }: { value: number }) {
  const up = value >= 0;
  return (
    <Badge variant={up ? "success" : "error"} size="sm">
      <span className="flex items-center gap-1">
        {up ? <ArrowUpIcon className="h-3 w-3" /> : <ArrowDownIcon className="h-3 w-3" />}
        {Math.abs(value).toFixed(2)}%
      </span>
    </Badge>
  );
}

export function StatCard({ stat }: { stat: MarketStat }) {
  return (
    <div
      className={cn(
        "rounded-xl border border-border bg-surface p-4 shadow-sm transition-all duration-200 hover:shadow-md"
      )}
    >
      <span className="text-sm text-muted-foreground">{stat.label}</span>
      <span className="mt-1 block text-xl font-bold text-foreground">{stat.value}</span>
      <div className="mt-2">
        {stat.changePct !== undefined ? <ChangeBadge value={stat.changePct} /> : null}
      </div>
    </div>
  );
}
