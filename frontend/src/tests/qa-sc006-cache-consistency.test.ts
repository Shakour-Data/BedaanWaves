import { describe, it, expect } from "vitest";
import {
  assertParity,
  snapshotToChartsModel,
  type LevelModel,
  type ChartsModel,
  type ParityMismatch,
} from "@/lib/charts-model";
import type { SnapshotResponse } from "@/lib/api/dashboard";

function buildSnapshot(overrides: {
  dimensionScores: Record<string, number>;
  trendScores: Array<Record<string, number>>;
  dates: string[];
  weights: Record<string, number>;
  weightTrends?: Array<Record<string, number>>;
  snapshotId?: string;
  alignTrend?: boolean;
}): ChartsModel {
  const {
    dimensionScores,
    trendScores,
    dates,
    weights,
    weightTrends,
    snapshotId = "snap_test",
    alignTrend = true,
  } = overrides;

  const trendPoints = trendScores.map((scores, i) => ({
    date: dates[i],
    effective_at: dates[i],
    overall: 0,
    level_scores: scores,
    count: 0,
  }));

  const dailyScores = {
    overall: 75,
    dimension: dimensionScores,
    sub_dimension: {},
    aspect: {},
    sub_aspect: {},
  };

  const rawSnapshot = {
    snapshotId,
    timestamp: "2026-09-09T00:00:00Z",
    scores: {
      daily: dailyScores,
      hourly: dailyScores,
      current: dailyScores,
    },
    trends: {
      daily: trendPoints,
      intraday: [],
    },
    weights: {
      dimension: weights,
      sub_dimension: {},
      aspect: {},
      sub_aspect: {},
    },
    weight_trends: {
      daily: weightTrends
        ? weightTrends.map((w, i) => ({
            date: dates[i] ?? "2026-09-09",
            effective_at: dates[i] ?? "2026-09-09",
            weights: w,
          }))
        : [],
    },
    weight_deltas: {
      daily: {
        weights: {
          dimension: Object.fromEntries(
            Object.entries(weights).map(([k, v]) => [k, { delta: 0, delta_pct: 0, value: v }]),
          ),
        },
      },
    },
    deltas: {
      hourly_vs_daily: {
        overall_delta: 0,
        overall_delta_pct: 0,
        dimension_deltas: {},
        sub_dimension_deltas: {},
        aspect_deltas: {},
        sub_aspect_deltas: {},
      },
      current_vs_hourly: {
        overall_delta: 0,
        overall_delta_pct: 0,
        dimension_deltas: {},
        sub_dimension_deltas: {},
        aspect_deltas: {},
        sub_aspect_deltas: {},
      },
      current_vs_daily: {
        overall_delta: 0,
        overall_delta_pct: 0,
        dimension_deltas: {},
        sub_dimension_deltas: {},
        aspect_deltas: {},
        sub_aspect_deltas: {},
      },
    },
  } as unknown as SnapshotResponse;

  return snapshotToChartsModel(rawSnapshot, { alignTrendToSnapshot: alignTrend }) as ChartsModel;
}

function makeLevel(levels: LevelModel[], overrides: Partial<ChartsModel> = {}): ChartsModel {
  return {
    snapshotId: "snap_test",
    timestamp: "2026-09-09T00:00:00Z",
    effectiveAt: "2026-09-09T00:00:00Z",
    tier: "daily",
    latestDate: "2026-09-09",
    overallScore: 75,
    overallTrend: [],
    levels,
    parity: assertParity(levels, "2026-09-09", "snap_test"),
    source: "snapshot",
    ...overrides,
  };
}

describe("QA Priority 1 - SC-006: Cache Invalidation / Change Bar Delta Consistency", () => {
  describe("scoreDelta equals trend last-point minus second-to-last", () => {
    it("delta of +5.0 is computed when trend moves from 75 to 80", () => {
      const model = buildSnapshot({
        dimensionScores: { fundamental: 80, technical: 70 },
        trendScores: [
          { fundamental: 75, technical: 65 },
          { fundamental: 80, technical: 70 },
        ],
        dates: ["2026-09-08", "2026-09-09"],
        weights: { fundamental: 0.5, technical: 0.5 },
      });

      const dimLevel = model.levels[0];
      expect(dimLevel.scoreDelta).toHaveLength(2);
      expect(dimLevel.scoreDelta[0]).toMatchObject({ key: "fundamental", score: 5 });
      expect(dimLevel.scoreDelta[1]).toMatchObject({ key: "technical", score: 5 });
    });

    it("delta of -3.0 is computed when trend drops from 70 to 67", () => {
      const model = buildSnapshot({
        dimensionScores: { fundamental: 67 },
        trendScores: [
          { fundamental: 70 },
          { fundamental: 67 },
        ],
        dates: ["2026-09-08", "2026-09-09"],
        weights: { fundamental: 1 },
      });

      const dimLevel = model.levels[0];
      expect(dimLevel.scoreDelta[0]).toMatchObject({ key: "fundamental", score: -3 });
    });

    it("delta is 0 when trend is flat across both points", () => {
      const model = buildSnapshot({
        dimensionScores: { fundamental: 50 },
        trendScores: [
          { fundamental: 50 },
          { fundamental: 50 },
        ],
        dates: ["2026-09-08", "2026-09-09"],
        weights: { fundamental: 1 },
      });

      const dimLevel = model.levels[0];
      expect(dimLevel.scoreDelta[0]).toMatchObject({ key: "fundamental", score: 0 });
    });

    it("delta is 0 when only one trend point exists (no previous)", () => {
      const model = buildSnapshot({
        dimensionScores: { fundamental: 80 },
        trendScores: [{ fundamental: 80 }],
        dates: ["2026-09-09"],
        weights: { fundamental: 1 },
      });

      const dimLevel = model.levels[0];
      expect(dimLevel.scoreDelta[0]).toMatchObject({ key: "fundamental", score: 0 });
    });
  });

  describe("alignTrendToSnapshot guarantees spider/trend last-point parity", () => {
    it("aligns trend last point to spider score so delta is derived from snapshot", () => {
      const model = buildSnapshot({
        dimensionScores: { fundamental: 92, technical: 88 },
        trendScores: [
          { fundamental: 85, technical: 80 },
          { fundamental: 90, technical: 85 },
        ],
        dates: ["2026-09-08", "2026-09-09"],
        weights: { fundamental: 0.5, technical: 0.5 },
        alignTrend: true,
      });

      const dimLevel = model.levels[0];
      expect(dimLevel.parity.ok).toBe(true);
      expect(dimLevel.scoreDelta[0]).toMatchObject({ key: "fundamental", score: 7 });
      expect(dimLevel.scoreDelta[1]).toMatchObject({ key: "technical", score: 8 });
    });

    it("without alignment, delta reflects raw trend difference", () => {
      const model = buildSnapshot({
        dimensionScores: { fundamental: 92 },
        trendScores: [
          { fundamental: 85 },
          { fundamental: 90 },
        ],
        dates: ["2026-09-08", "2026-09-09"],
        weights: { fundamental: 1 },
        alignTrend: false,
      });

      const dimLevel = model.levels[0];
      expect(dimLevel.scoreDelta[0]).toMatchObject({ key: "fundamental", score: 5 });
    });
  });

  describe("Cache invalidation: stale-while-revalidate parity", () => {
    it("model from snapshot A retains A's snapshotId and parity", () => {
      const modelA = buildSnapshot({
        dimensionScores: { fundamental: 80 },
        trendScores: [
          { fundamental: 75 },
          { fundamental: 80 },
        ],
        dates: ["2026-09-08", "2026-09-09"],
        weights: { fundamental: 1 },
        snapshotId: "snap_A",
      });

      expect(modelA.snapshotId).toBe("snap_A");
      expect(modelA.parity.ok).toBe(true);
      expect(modelA.parity.snapshotId).toBe("snap_A");
    });

    it("model from snapshot B after refresh has B's snapshotId", () => {
      const modelB = buildSnapshot({
        dimensionScores: { fundamental: 90 },
        trendScores: [
          { fundamental: 85 },
          { fundamental: 90 },
        ],
        dates: ["2026-09-09", "2026-09-10"],
        weights: { fundamental: 1 },
        snapshotId: "snap_B",
      });

      expect(modelB.snapshotId).toBe("snap_B");
      expect(modelB.parity.ok).toBe(true);
      expect(modelB.latestDate).toBe("2026-09-10");
    });

    it("two distinct snapshots produce non-overlapping snapshotIds", () => {
      const modelA = buildSnapshot({
        dimensionScores: { fundamental: 80 },
        trendScores: [{ fundamental: 80 }],
        dates: ["2026-09-09"],
        weights: { fundamental: 1 },
        snapshotId: "snap_A",
      });

      const modelB = buildSnapshot({
        dimensionScores: { fundamental: 90 },
        trendScores: [{ fundamental: 90 }],
        dates: ["2026-09-10"],
        weights: { fundamental: 1 },
        snapshotId: "snap_B",
      });

      expect(modelA.snapshotId).not.toBe(modelB.snapshotId);
      expect(modelA.parity.snapshotId).not.toBe(modelB.parity.snapshotId);
    });
  });

  describe("Weight delta matches trend delta for coefficient change chart", () => {
    it("weightDelta derives from weight trend series difference", () => {
      const model = buildSnapshot({
        dimensionScores: { fundamental: 50, technical: 50 },
        trendScores: [
          { fundamental: 50, technical: 50 },
          { fundamental: 50, technical: 50 },
        ],
        dates: ["2026-09-08", "2026-09-09"],
        weights: { fundamental: 0.4, technical: 0.3 },
        weightTrends: [
          { fundamental: 0.4, technical: 0.3 },
          { fundamental: 0.45, technical: 0.25 },
        ],
      });

      const dimLevel = model.levels[0];
      expect(dimLevel.weightDelta).toHaveLength(2);
      expect(dimLevel.weightDelta[0]).toMatchObject({ key: "fundamental", score: 0.05 });
      expect(dimLevel.weightDelta[1]).toMatchObject({ key: "technical", score: -0.05 });
    });
  });
});
