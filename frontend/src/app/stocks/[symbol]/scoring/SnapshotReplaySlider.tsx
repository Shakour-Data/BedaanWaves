"use client";

import { TarotCard } from "@/components/ui/TarotCard";
import type { SnapshotIndexEntry } from "@/store/useDateStore";

interface SnapshotReplaySliderProps {
  entries: SnapshotIndexEntry[];
  sliderIndex: number;
  onSliderChange: (index: number) => void;
}

export function SnapshotReplaySlider({ entries, sliderIndex, onSliderChange }: SnapshotReplaySliderProps) {
  if (!entries || entries.length === 0) return null;

  const earliest = entries[entries.length - 1];
  const latest = entries[0];
  const current = entries[sliderIndex];

  return (
    <TarotCard title="[SR] SNAPSHOT REPLAY — Drag to travel in time">
      <div className="flex flex-col gap-3">
        <div className="flex items-center justify-between gap-3 text-xs">
          <span className="font-mono text-muted-foreground">
            EARLIEST · {earliest?.effectiveAt?.slice(0, 16)?.replace("T", " ") ?? "—"}
            <span className="ml-2 uppercase text-[10px] text-[var(--color-text-secondary)]">
              {earliest?.tier ?? ""}
            </span>
          </span>
          <span className="font-semibold text-[var(--color-primary)]">
            {current?.effectiveAt?.slice(0, 16)?.replace("T", " ") ?? "NOW"}
            {current?.snapshotId && (
              <span className="ml-2 font-mono text-[10px] text-muted-foreground">
                #{current.snapshotId.slice(0, 8)}
              </span>
            )}
            <span className="ml-2 uppercase text-[10px] text-[var(--color-text-secondary)]">
              {current?.tier ?? ""}
            </span>
          </span>
          <span className="font-mono text-muted-foreground">
            LATEST · {latest?.effectiveAt?.slice(0, 16)?.replace("T", " ") ?? "—"}
            <span className="ml-2 uppercase text-[10px] text-[var(--color-text-secondary)]">
              {latest?.tier ?? ""}
            </span>
          </span>
        </div>
        <input
          type="range"
          min={0}
          max={entries.length - 1}
          value={sliderIndex}
          onChange={(e) => onSliderChange(parseInt(e.target.value, 10))}
          aria-label="Snapshot time travel slider"
          aria-valuemin={0}
          aria-valuemax={entries.length - 1}
          aria-valuenow={sliderIndex}
          className="w-full h-2 bg-[var(--color-neutral)] rounded-full appearance-none cursor-pointer accent-[var(--color-primary)]"
        />
        <div className="text-[10px] text-muted-foreground">
          {entries.length} snapshots available · Drag slider to replay historical scoring states at exact parity across all widgets.
        </div>
      </div>
    </TarotCard>
  );
}
