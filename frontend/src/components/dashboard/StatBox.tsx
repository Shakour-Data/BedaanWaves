import { cn } from "@/lib/cn";

interface StatBoxProps {
  label: string;
  value: string;
  hint?: string;
}

export function StatBox({ label, value, hint }: StatBoxProps) {
  return (
    <div className="rounded-xl border border-border bg-surface p-4 shadow-sm">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className="mt-1 block text-xl font-bold text-foreground">{value}</span>
      {hint ? <span className="text-xs text-muted-foreground">{hint}</span> : null}
    </div>
  );
}
