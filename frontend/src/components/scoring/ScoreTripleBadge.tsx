/**
 * ScoreTripleBadge.tsx
 * ---------------------------------------------------------------------------
 * Renders the three-frame score reference: PREV DAY / PREV HOUR / CURRENT.
 *
 * ARCHITECTURAL CONTRACT (Temporal Scoring Snapshot Spec):
 *   - All three scores originate from the SAME snapshotId to guarantee parity.
 *   - Each score is accompanied by a numeric delta against its left-side neighbour:
 *       PREV HOUR  shows delta vs PREV DAY   (hourly_vs_daily)
 *       CURRENT    shows delta vs PREV HOUR  (current_vs_hourly)
 *   - A secondary optional secondary delta (CURRENT vs PREV DAY) can be rendered
 *     via `showDailyDelta=true` using current_vs_daily DeltaFrame.
 *
 * NO-ICON DISCIPLINE (project hard constraint):
 *   - Arrows use characters UP/DOWN: "UP +N.N" / "DOWN -N.N"
 *   - No lucide/svg icons inside; text-only status labels.
 *
 * ACCESSIBILITY (WCAG 2.1 AA):
 *   - Each score frame is an aria-roled group with labelled-by
 *   - Delta values are announced as "increase" / "decrease" via visually-hidden span
 *   - Tabular numerals for visual vertical alignment.
 */

import { cn } from "@/lib/cn";
import type { HierarchyScores, DeltaFrame } from "@/lib/api/dashboard";

export interface ScoreTripleBadgeProps {
  scores: {
    daily: HierarchyScores;
    hourly: HierarchyScores;
    current: HierarchyScores;
  };
  deltas: {
    hourly_vs_daily: DeltaFrame;
    current_vs_hourly: DeltaFrame;
    current_vs_daily: DeltaFrame;
  };
  dimensionKey?: string;
  showDailyDelta?: boolean;
  size?: "sm" | "md" | "lg";
  className?: string;
}

type ScoreSize = NonNullable<ScoreTripleBadgeProps["size"]>;

const SIZE: Record<
  ScoreSize,
  { frame: string; label: string; score: string; delta: string; gap: string }
> = {
  sm: {
    frame: "px-3 py-2",
    label: "text-[10px] uppercase tracking-wider",
    score: "text-lg font-bold",
    delta: "text-[11px]",
    gap: "gap-2",
  },
  md: {
    frame: "px-4 py-3",
    label: "text-xs uppercase tracking-wider",
    score: "text-2xl font-bold",
    delta: "text-xs",
    gap: "gap-3",
  },
  lg: {
    frame: "px-5 py-4",
    label: "text-sm uppercase tracking-wider",
    score: "text-3xl font-bold",
    delta: "text-sm",
    gap: "gap-4",
  },
};

function pickOverallOrDimension(h: HierarchyScores, dim?: string): number | null {
  if (!dim) return h.overall ?? null;
  const v = h.dimension?.[dim];
  return typeof v === "number" ? v : null;
}

function pickDeltaOrDimension(
  df: DeltaFrame,
  dim?: string,
): { delta: number | null; pct: number | null } {
  if (!dim) {
    return { delta: df.overall_delta ?? null, pct: df.overall_delta_pct ?? null };
  }
  const d = df.dimension_deltas?.[dim];
  if (!d) return { delta: null, pct: null };
  return { delta: d.delta ?? null, pct: d.delta_pct ?? null };
}

function scoreColor(score: number | null): string {
  if (score === null) return "text-[var(--color-text-secondary)]";
  if (score >= 80) return "text-[var(--color-success)]";
  if (score >= 50) return "text-[var(--color-warning)]";
  return "text-[var(--color-error)]";
}

function ScoreFrame({
  label,
  asOfLabel,
  score,
  delta,
  deltaPct,
  size,
  highlight,
  ariaLabel,
}: {
  label: string;
  asOfLabel?: string;
  score: number | null;
  delta?: number | null;
  deltaPct?: number | null;
  size: ScoreSize;
  highlight?: boolean;
  ariaLabel: string;
}) {
  const s = SIZE[size];
  const deltaNum = typeof delta === "number" ? delta : null;
  const isPositive = deltaNum === null ? null : deltaNum >= 0;
  const deltaColor =
    deltaNum === null
      ? "text-[var(--color-text-secondary)]"
      : isPositive
        ? "text-[var(--color-success)]"
        : "text-[var(--color-error)]";

  const deltaWord =
    deltaNum === null
      ? null
      : isPositive
        ? "UP"
        : "DOWN";
  const signedDelta =
    deltaNum === null
      ? "—"
      : `${isPositive ? "+" : ""}${deltaNum.toFixed(2)}`;
  const signedPct =
    typeof deltaPct === "number"
      ? `${isPositive ?? deltaPct >= 0 ? "+" : ""}${deltaPct.toFixed(2)}%`
      : null;

  const scoreDisplay = score === null ? "—" : score.toFixed(1);
  const scoreColorCls = scoreColor(score);

  return (
    <div
      role="group"
      aria-label={ariaLabel}
      className={cn(
        "flex flex-col items-start rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-sm",
        s.frame,
        highlight && "border-[var(--color-primary)]/40 ring-1 ring-[var(--color-primary)]/10",
      )}
    >
      <div className="flex w-full items-center justify-between">
        <span
          className={cn(
            "font-semibold text-[var(--color-text-secondary)]",
            s.label,
          )}
        >
          {label}
        </span>
        {highlight && (
          <span
            className={cn(
              "rounded px-1.5 py-0.5 bg-[var(--color-primary)]/10 text-[var(--color-primary)] font-semibold",
              s.delta,
            )}
          >
            LIVE
          </span>
        )}
      </div>
      <div className={cn("mt-1 font-bold tabular-nums", s.score, scoreColorCls)}>
        {scoreDisplay}
      </div>
      {deltaWord !== null && (
        <div
          className={cn(
            "mt-1 flex items-center gap-1 font-semibold tabular-nums",
            s.delta,
            deltaColor,
          )}
          aria-hidden="false"
        >
          <span>{deltaWord}</span>
          <span>{signedDelta}</span>
          {signedPct && <span>({signedPct})</span>}
          <span className="sr-only">
            {isPositive ? "increase" : "decrease"} of {Math.abs(deltaNum ?? 0).toFixed(2)} points.
          </span>
        </div>
      )}
      {asOfLabel && (
        <div
          className={cn(
            "mt-1 font-medium text-[var(--color-text-secondary)]/80",
            s.delta,
          )}
        >
          {asOfLabel}
        </div>
      )}
    </div>
  );
}

export function ScoreTripleBadge({
  scores,
  deltas,
  dimensionKey,
  showDailyDelta = false,
  size = "md",
  className,
}: ScoreTripleBadgeProps) {
  const s = SIZE[size];

  const daily = pickOverallOrDimension(scores.daily, dimensionKey);
  const hourly = pickOverallOrDimension(scores.hourly, dimensionKey);
  const current = pickOverallOrDimension(scores.current, dimensionKey);

  const hvd = pickDeltaOrDimension(deltas.hourly_vs_daily, dimensionKey);
  const cvh = pickDeltaOrDimension(deltas.current_vs_hourly, dimensionKey);
  const cvd = pickDeltaOrDimension(deltas.current_vs_daily, dimensionKey);

  const labelDim = dimensionKey
    ? ` for ${dimensionKey.replace(/_/g, " ")}`
    : " overall";

  return (
    <div
      className={cn(
        "grid grid-cols-1 sm:grid-cols-3 items-stretch",
        s.gap,
        className,
      )}
    >
      <ScoreFrame
        label="PREV DAY"
        score={daily}
        size={size}
        ariaLabel={`Previous day${labelDim} score. Reference baseline 00:00 UTC.`}
      />
      <ScoreFrame
        label="PREV HOUR"
        score={hourly}
        delta={hvd.delta}
        deltaPct={hvd.pct}
        size={size}
        ariaLabel={`Previous hour${labelDim} score. ${
          hvd.delta === null
            ? "No delta data available."
            : `Delta versus previous day: ${hvd.delta.toFixed(2)}.`
        }`}
      />
      <ScoreFrame
        label="CURRENT"
        score={current}
        delta={showDailyDelta ? cvd.delta : cvh.delta}
        deltaPct={showDailyDelta ? cvd.pct : cvh.pct}
        size={size}
        highlight
        ariaLabel={`Current${labelDim} score. ${
          (showDailyDelta ? cvd.delta : cvh.delta) === null
            ? ""
            : `Delta versus ${showDailyDelta ? "previous day" : "previous hour"}: ${(
                showDailyDelta ? cvd.delta : cvh.delta
              )?.toFixed(2)}.`
        }`}
      />
    </div>
  );
}

export default ScoreTripleBadge;
