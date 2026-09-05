import { cn } from "@/lib/cn";

interface ScoreBadgeProps {
  score: number;
  size?: "sm" | "md" | "lg";
  className?: string;
}

export function ScoreBadge({ score, size = "md", className }: ScoreBadgeProps) {
  const colorClass = score >= 80
    ? "bg-[var(--color-success)]/15 text-[var(--color-success)]"
    : score >= 50
      ? "bg-[var(--color-warning)]/15 text-[var(--color-warning)]"
      : "bg-[var(--color-error)]/15 text-[var(--color-error)]";

  const sizeClasses = size === "lg" ? "px-3 py-1.5 text-lg" : size === "sm" ? "px-2 py-0.5 text-xs" : "px-2.5 py-1 text-sm";

  return (
    <span
      className={cn(
        "inline-flex items-center justify-center rounded-lg font-bold tabular-nums",
        colorClass,
        sizeClasses,
        className,
      )}
    >
      {score.toFixed(1)}
    </span>
  );
}

interface ChangeBadgeProps {
  change: number;
  changePct: number;
  size?: "sm" | "md" | "lg";
  className?: string;
}

export function ChangeBadge({ change, changePct, size = "md", className }: ChangeBadgeProps) {
  const isPositive = change >= 0;
  const colorClass = isPositive
    ? "bg-[var(--color-success)]/15 text-[var(--color-success)]"
    : "bg-[var(--color-error)]/15 text-[var(--color-error)]";

  const sizeClasses = size === "lg" ? "px-3 py-1.5 text-lg" : size === "sm" ? "px-2 py-0.5 text-xs" : "px-2.5 py-1 text-sm";

  return (
    <div className={cn("flex items-center gap-1.5", colorClass, "rounded-lg px-2.5 py-1", size === "lg" ? "px-3 py-1.5" : size === "sm" ? "px-2 py-0.5" : "", className)}>
      {isPositive ? (
        <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round">
          <path d="M18 15l-6-6-6 6" />
        </svg>
      ) : (
        <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round">
          <path d="M6 9l6 6 6-6" />
        </svg>
      )}
      <span className={cn("font-bold tabular-nums", sizeClasses)}>
        {isPositive ? "+" : ""}{change.toFixed(2)}
      </span>
      <span className={cn("font-medium", sizeClasses)}>
        ({isPositive ? "+" : ""}{changePct.toFixed(2)}%)
      </span>
    </div>
  );
}

interface GradeBadgeProps {
  grade: string;
  className?: string;
}

export function GradeBadge({ grade, className }: GradeBadgeProps) {
  const gradeUpper = grade.toUpperCase();
  let colorClass = "bg-[var(--color-text-secondary)]/15 text-[var(--color-text-secondary)]";
  if (gradeUpper === "A+" || gradeUpper === "A" || gradeUpper === "A-") {
    colorClass = "bg-[var(--color-success)]/15 text-[var(--color-success)]";
  } else if (gradeUpper === "B+" || gradeUpper === "B" || gradeUpper === "B-") {
    colorClass = "bg-[var(--color-primary)]/15 text-[var(--color-primary)]";
  } else if (gradeUpper === "C+" || gradeUpper === "C" || gradeUpper === "C-") {
    colorClass = "bg-[var(--color-warning)]/15 text-[var(--color-warning)]";
  } else if (gradeUpper === "D" || gradeUpper === "F") {
    colorClass = "bg-[var(--color-error)]/15 text-[var(--color-error)]";
  }

  return (
    <span
      className={cn(
        "inline-flex items-center justify-center rounded-md px-2 py-0.5 text-xs font-bold uppercase tracking-wider",
        colorClass,
        className,
      )}
    >
      {grade || "—"}
    </span>
  );
}
