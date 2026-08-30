import { cn } from "@/lib/cn";
import type { SignalRow } from "@/lib/dashboard-data";
import { Badge } from "@/components/ui/Badge";

const TYPE_STYLE: Record<SignalRow["type"], "default" | "success" | "error" | "warning" | "info" | "neutral"> = {
  BUY: "success",
  SELL: "error",
  HOLD: "warning",
  STRONG_BUY: "success",
  STRONG_SELL: "error",
};

const TYPE_LABEL: Record<SignalRow["type"], string> = {
  BUY: "خرید",
  SELL: "فروش",
  HOLD: "نگهداری",
  STRONG_BUY: "خرید قوی",
  STRONG_SELL: "فروش قوی" };

export function SignalList({ signals }: { signals: SignalRow[] }) {
  return (
    <ul className="flex flex-col gap-2">
      {signals.map((s) => (
        <li key={`${s.symbol}-${s.model}`} className="flex items-center gap-3">
          <span className="w-16 font-semibold text-sm text-primary">{s.symbol}</span>
          <Badge variant={TYPE_STYLE[s.type]} size="sm">
            {TYPE_LABEL[s.type]}
          </Badge>
          <span className="text-sm text-muted-foreground">اطمینان {Math.max(0, Math.min(100, s.confidence)).toFixed(1)}٪</span>
          <span className="ms-auto truncate text-xs text-muted-foreground">{s.model}</span>
        </li>
      ))}
    </ul>
  );
}
