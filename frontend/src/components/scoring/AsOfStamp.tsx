/**
 * AsOfStamp.tsx
 * ---------------------------------------------------------------------------
 * Renders an "AS OF <ISO timestamp>" label with a human-friendly time-ago.
 * Used on every page/tile that consumes the unified snapshot so the user
 * always knows the recency of every analytical number on screen.
 *
 * CONTRACT (Temporal Scoring Snapshot Spec):
 *   - One snapshotId per page render; this stamp renders its effectiveAt
 *     + a human relative time ("3 minutes ago").
 *   - If snapshotId is absent, rendering switches to a neutral "LOADING" or
 *     "NO DATA" label with a11y status.
 *
 * ACCESSIBILITY (WCAG 2.1 AA):
 *   - `aria-live="polite"` so when a new snapshot is loaded the change is
 *     announced to screen reader users without interrupting.
 *   - Visually-hidden full ISO stamp alongside the compact one for readers.
 *   - Loading / error states have matching `role="status"` + semantics.
 *
 * NO-ICON DISCIPLINE:
 *   - No clock icons; use text labels ("AS OF", "REFRESH", "LIVE").
 *   - Bullet separator character is the unicode dot (·).
 */

import { useMemo } from "react";
import { cn } from "@/lib/cn";
import { formatTimeAgo } from "@/lib/utils";

export interface AsOfStampProps {
  timestamp: string | null;
  snapshotId?: string | null;
  loading?: boolean;
  error?: string | null;
  variant?: "default" | "compact" | "emphasis";
  className?: string;
  label?: string;
}

function safeIsoToDate(ts: string | null | undefined): Date | null {
  if (!ts) return null;
  try {
    const d = new Date(ts);
    if (Number.isNaN(d.getTime())) return null;
    return d;
  } catch {
    return null;
  }
}

function formatCompactDate(d: Date): string {
  const y = d.getUTCFullYear();
  const m = String(d.getUTCMonth() + 1).padStart(2, "0");
  const day = String(d.getUTCDate()).padStart(2, "0");
  const hh = String(d.getUTCHours()).padStart(2, "0");
  const mm = String(d.getUTCMinutes()).padStart(2, "0");
  return `${y}-${m}-${day} ${hh}:${mm} UTC`;
}

export function AsOfStamp({
  timestamp,
  snapshotId,
  loading = false,
  error = null,
  variant = "default",
  className,
  label = "AS OF",
}: AsOfStampProps) {
  const date = useMemo(() => safeIsoToDate(timestamp), [timestamp]);
  const timeAgo = useMemo(() => {
    if (!date) return null;
    return formatTimeAgo(date.toISOString());
  }, [date]);

  const snapshotShort = snapshotId
    ? snapshotId.slice(0, 8)
    : null;

  if (loading) {
    return (
      <div
        role="status"
        aria-live="polite"
        aria-busy="true"
        className={cn(
          "inline-flex items-center gap-2 text-xs font-medium",
          "text-[var(--color-text-secondary)]",
          variant === "emphasis" && "text-sm font-semibold",
          className,
        )}
      >
        <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-[var(--color-text-secondary)]/60" />
        <span>LOADING</span>
        <span className="sr-only">
          Snapshot timestamp is being retrieved. Please wait.
        </span>
      </div>
    );
  }

  if (error || !timestamp || !date) {
    return (
      <div
        role="status"
        aria-live="polite"
        className={cn(
          "inline-flex items-center gap-2 text-xs font-medium",
          "text-[var(--color-error)]/90",
          variant === "emphasis" && "text-sm font-semibold",
          className,
        )}
      >
        <span>{error ? "DATA STALE" : "NO DATA"}</span>
        {error && (
          <span className="sr-only">
            Reason: {error}
          </span>
        )}
      </div>
    );
  }

  const variantClasses =
    variant === "compact"
      ? "text-[11px] font-medium"
      : variant === "emphasis"
        ? "text-sm font-semibold"
        : "text-xs font-medium";

  return (
    <div
      role="status"
      aria-live="polite"
      className={cn(
        "inline-flex flex-wrap items-center gap-1.5 tabular-nums",
        variantClasses,
        "text-[var(--color-text-secondary)]",
        className,
      )}
    >
      <span className="font-semibold tracking-wide uppercase">
        {label}
      </span>
      <span aria-hidden="true" className="opacity-60">
        ·
      </span>
      <span className="font-medium text-[var(--color-text-primary)]/90">
        {formatCompactDate(date)}
      </span>
      <span aria-hidden="true" className="opacity-60">
        ·
      </span>
      <span
        className="font-medium"
        data-testid="asof-timeago"
      >
        {timeAgo ?? "just now"}
      </span>
      {snapshotShort && (
        <>
          <span aria-hidden="true" className="opacity-40">
            ·
          </span>
          <span
            className="font-mono tracking-tight opacity-70"
            aria-label={`Snapshot identifier ${snapshotId}`}
            title={snapshotId ?? undefined}
          >
            #{snapshotShort}
          </span>
        </>
      )}
      <span className="sr-only">
        Data current as of {date.toISOString()}.
        {timeAgo ? ` That was ${timeAgo}.` : ""}
      </span>
    </div>
  );
}

export default AsOfStamp;
