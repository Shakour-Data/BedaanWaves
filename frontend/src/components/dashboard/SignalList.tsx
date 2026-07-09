import { cn } from "@/lib/cn";
import type { SignalRow } from "@/lib/dashboard-data";

const TYPE_STYLE: Record<SignalRow["type"], string> = {
  BUY: "bg-success/15 text-success",
  SELL: "bg-primary/15 text-primary",
  HOLD: "bg-accent/30 text-accent-foreground",
};

const TYPE_LABEL: Record<SignalRow["type"], string> = {
  BUY: "خرید",
  SELL: "فروش",
  HOLD: "نگهداری",
};

export function SignalList({ signals }: { signals: SignalRow[] }) {
  return (
    <ul className="flex flex-col gap-2">
      {signals.map((s) => (
        <li key={`${s.symbol}-${s.model}`} className="flex items-center gap-3">
          <span className="w-16 font-semibold">{s.symbol}</span>
          <span className={cn("rounded-full px-2 py-0.5 text-xs font-semibold", TYPE_STYLE[s.type])}>
            {TYPE_LABEL[s.type]}
          </span>
          <span className="text-sm text-muted-foreground">اطمینان {s.confidence.toFixed(1)}٪</span>
          <span className="ms-auto truncate text-xs text-muted-foreground">{s.model}</span>
        </li>
      ))}
    </ul>
  );
}
