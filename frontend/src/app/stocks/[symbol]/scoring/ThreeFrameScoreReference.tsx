"use client";

import { cn } from "@/lib/cn";
import { TarotCard } from "@/components/ui/TarotCard";
import { ScoreTripleBadge } from "@/components/scoring/ScoreTripleBadge";
import type { SnapshotResponse } from "@/store/useDateStore";
import type { HierarchyScores } from "@/lib/api/scoring";
import type { ScoringTab } from "./useScoringData";

interface ThreeFrameScoreReferenceProps {
  snapshot: SnapshotResponse | null;
  hierarchy: HierarchyScores;
  scoringTab: ScoringTab;
}

export function ThreeFrameScoreReference({ snapshot, hierarchy, scoringTab }: ThreeFrameScoreReferenceProps) {
  return (
    <TarotCard title="✦ THREE-FRAME SCORE REFERENCE">
      <div className="flex flex-col gap-3">
        {snapshot ? (
          <ScoreTripleBadge
            scores={snapshot.scores}
            deltas={snapshot.deltas}
            showDailyDelta={scoringTab === "HISTORICAL"}
            size="lg"
          />
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            {(["PREV DAY", "PREV HOUR", "CURRENT"] as const).map((lbl, i) => (
              <div
                key={lbl}
                role="group"
                aria-label={`${lbl} score frame. Snapshot pipeline pending.`}
                className={cn(
                  "flex flex-col items-start rounded-xl border border-dashed border-[var(--color-border)] bg-[var(--color-neutral)]/30 px-5 py-4",
                  i === 2 && "border-[var(--color-primary)]/20 ring-1 ring-[var(--color-primary)]/5"
                )}
              >
                <div className="flex w-full items-center justify-between">
                  <span className="text-sm uppercase tracking-wider font-semibold text-[var(--color-text-secondary)]">{lbl}</span>
                  {i === 2 && (
                    <span className="rounded px-1.5 py-0.5 bg-[var(--color-primary)]/10 text-[var(--color-primary)] font-semibold text-sm">
                      LIVE
                    </span>
                  )}
                </div>
                <div className="mt-1 text-3xl font-bold tabular-nums text-[var(--color-text-secondary)]">
                  {i === 2 && hierarchy ? hierarchy.overallScore : "—"}
                </div>
                <div className="mt-1 text-sm text-[var(--color-text-secondary)]/80">
                  {i === 2
                    ? hierarchy?.grade?.replace("_", " ") ?? "Pending snapshot"
                    : "Pending snapshot pipeline"}
                </div>
              </div>
            ))}
          </div>
        )}
        {!snapshot && (
          <div className="rounded-lg border border-dashed border-[var(--color-border)] bg-[var(--color-neutral)]/40 p-3 text-xs text-muted-foreground">
            ◇ NOTE: Snapshot pipeline has not yet produced rows for this symbol. The CURRENT frame above is derived from the legacy daily REST endpoint (single-frame score only). Three-frame PREV-DAY / PREV-HOUR / CURRENT parity activates once HourlyScoreRecompute and DailyScoreRecalculation scheduler jobs populate ScoringSnapshot tier rows.
          </div>
        )}
      </div>
    </TarotCard>
  );
}
