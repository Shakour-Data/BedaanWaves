import { cn } from "@/lib/cn";

export interface StatBoxProps {
  label: string;
  value: string | number;
  hint?: string;
  className?: string;
}

export function StatBox({ label, value, hint, className }: StatBoxProps) {
  return (
    <div className={cn("rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 shadow-sm", className)}>
      <p className="text-xs font-medium text-[var(--color-text-secondary)]">{label}</p>
      <p className="mt-1 text-lg font-bold text-[var(--color-text-primary)] tabular-nums">{value}</p>
      {hint && (
        <p className="mt-0.5 text-[10px] text-[var(--color-text-secondary)]">{hint}</p>
      )}
    </div>
  );
}
