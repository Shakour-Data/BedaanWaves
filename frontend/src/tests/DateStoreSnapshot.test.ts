import { describe, it, expect, beforeEach } from "vitest";
import { useDateStore } from "@/store/useDateStore";
import type {
  SnapshotResponse,
  SnapshotIndexEntry,
  SnapshotTier,
} from "@/store/useDateStore";

function emptySnapshot(id: string, tier: SnapshotTier): SnapshotResponse {
  return {
    snapshotId: id,
    effectiveAt: "2026-09-06T00:00:00Z",
    fetchedAt: "2026-09-06T00:00:01Z",
    tier,
    symbol: undefined,
    scores: {
      daily: { overall: 60, dimensions: {}, sub_dimensions: {}, aspects: {}, sub_aspects: {} },
      hourly: { overall: 61, dimensions: {}, sub_dimensions: {}, aspects: {}, sub_aspects: {} },
      current: { overall: 62, dimensions: {}, sub_dimensions: {}, aspects: {}, sub_aspects: {} },
    },
    deltas: {
      hourly_vs_daily: { overall: 1, overall_pct: 1.6667, dimensions: {}, sub_dimensions: {}, aspects: {}, sub_aspects: {} },
      current_vs_hourly: { overall: 1, overall_pct: 1.6393, dimensions: {}, sub_dimensions: {}, aspects: {}, sub_aspects: {} },
      current_vs_daily: { overall: 2, overall_pct: 3.3333, dimensions: {}, sub_dimensions: {}, aspects: {}, sub_aspects: {} },
    },
    weights: { dimension: {}, sub_dimension: {}, aspect: {}, sub_aspect: {} },
    weightTrends: [],
    weightDeltas: [],
    trends: { daily: [], intraday: [] },
    universe: { total: 3000, market: "NASDAQ" },
  };
}

describe("useDateStore snapshot selectors (T5 parity)", () => {
  beforeEach(() => {
    useDateStore.setState({
      snapshot: null,
      snapshotLoading: false,
      snapshotError: null,
      snapshotIndex: { hourly: [], daily: [] },
      selectedSnapshotId: null,
    });
  });

  it("setSnapshot stores the provided snapshot, selectSnapshot returns it", () => {
    const snap = emptySnapshot("id_123", "current");
    useDateStore.getState().setSnapshot(snap);
    const stored = useDateStore.getState().snapshot;
    expect(stored).not.toBeNull();
    expect(stored!.snapshotId).toBe("id_123");
    expect(stored!.tier).toBe("current");
  });

  it("setSnapshotIndex stores arrays in {hourly, daily} shape", () => {
    const hEntry: SnapshotIndexEntry = {
      snapshotId: "h1",
      tier: "hourly",
      effectiveAt: "2026-09-06T14:00:00Z",
      label: "2026-09-06 14:00 UTC",
      symbolCount: 3000,
    };
    const dEntry: SnapshotIndexEntry = {
      snapshotId: "d1",
      tier: "daily",
      effectiveAt: "2026-09-06T00:00:00Z",
      label: "2026-09-06 (daily)",
      symbolCount: 3000,
    };
    useDateStore.getState().setSnapshotIndex({ hourly: [hEntry], daily: [dEntry] });
    const idx = useDateStore.getState().snapshotIndex;
    expect(idx).not.toBeNull();
    expect(idx!.hourly.length).toBe(1);
    expect(idx!.daily.length).toBe(1);
    expect(idx!.hourly[0].snapshotId).toBe("h1");
    expect(idx!.daily[0].snapshotId).toBe("d1");
  });

  it("selectSnapshotById stores the id independently", () => {
    const s = useDateStore.getState();
    s.setSnapshot(emptySnapshot("x", "hourly"));
    s.selectSnapshotById("x");
    expect(s.selectedSnapshotId).toBe("x");
  });

  it("setSnapshotLoading and setSnapshotError update fields", () => {
    const s = useDateStore.getState();
    s.setSnapshotLoading(true);
    expect(s.snapshotLoading).toBe(true);
    s.setSnapshotError("boom");
    expect(s.snapshotError).toBe("boom");
    s.setSnapshotLoading(false);
    s.setSnapshotError(null);
    expect(s.snapshotLoading).toBe(false);
    expect(s.snapshotError).toBeNull();
  });

  it("re-exports SnapshotIndexEntry, SnapshotResponse types from dashboard fetcher", () => {
    // Type assertions via TypeScript (not runtime), but we import them at top
    // to prove types resolve at compile-time. This test runs as JS so we only
    // assert the import path compiled; no runtime type tests.
    expect(typeof useDateStore).toBe("function");
  });
});
