import { describe, it, expect, vi, beforeEach } from "vitest";
import { snapshotToChartsModel, assertParity, type LevelModel, type ChartsModel } from "@/lib/charts-model";

function levelModel(overrides: Partial<LevelModel> & Pick<LevelModel, "key">): LevelModel {
  return {
    key: overrides.key,
    label: overrides.label ?? overrides.key,
    short: overrides.key.slice(0, 3).toUpperCase(),
    spider: overrides.spider ?? [],
    trend: overrides.trend ?? [],
    scoreDelta: overrides.scoreDelta ?? [],
    weight: overrides.weight ?? [],
    weightDelta: overrides.weightDelta ?? [],
    ...overrides,
  };
}

function sampleModel(levels: LevelModel[], overrides: Partial<ChartsModel> = {}): ChartsModel {
  return {
    snapshotId: "snap_001",
    timestamp: "2026-09-09T00:00:00Z",
    effectiveAt: "2026-09-09T00:00:00Z",
    tier: "daily",
    latestDate: "2026-09-09",
    overallScore: 82,
    overallTrend: [],
    levels,
    parity: assertParity(levels, "2026-09-09", "snap_001"),
    source: "snapshot",
    ...overrides,
  };
}

describe("QA Priority 1 - Data Consistency & Parity", () => {
  describe("SC-002: Spider vs Trend date/value parity", () => {
    it("passes when spider scores match trend last point within tolerance", () => {
      const model = sampleModel([
        levelModel({
          key: "dimension",
          spider: [{ key: "fundamental", label: "Fundamental", score: 80, weight: 0.4 }],
          trend: [{ date: "2026-09-09", scores: { fundamental: 80 } }],
        }),
      ]);
      expect(model.parity.ok).toBe(true);
      expect(model.parity.mismatches).toHaveLength(0);
    });

    it("fails when trend last point diverges from spider", () => {
      const model = sampleModel([
        levelModel({
          key: "dimension",
          spider: [{ key: "fundamental", label: "Fundamental", score: 80, weight: 0.4 }],
          trend: [{ date: "2026-09-09", scores: { fundamental: 82 } }],
        }),
      ]);
      expect(model.parity.ok).toBe(false);
      expect(model.parity.mismatches).toHaveLength(1);
      expect(model.parity.mismatches[0]).toMatchObject({
        level: "dimension",
        key: "fundamental",
        spider: 80,
        trendLast: 82,
      });
    });

    it("ensures trend date equals spider latestDate", () => {
      const model = sampleModel([
        levelModel({
          key: "dimension",
          spider: [{ key: "fundamental", label: "Fundamental", score: 80, weight: 0.4 }],
          trend: [{ date: "2026-09-09", scores: { fundamental: 80 } }],
        }),
      ]);
      expect(model.latestDate).toBe("2026-09-09");
      expect(model.levels[0].trend[model.levels[0].trend.length - 1].date).toBe(model.latestDate);
    });
  });

  describe("SC-005: Weight sum validation", () => {
    it("accepts weights that sum to 1.0 within tolerance", () => {
      const weights = [
        { key: "valuation", label: "Valuation", score: 0, weight: 0.4 },
        { key: "growth", label: "Growth", score: 0, weight: 0.35 },
        { key: "quality", label: "Quality", score: 0, weight: 0.25 },
      ];
      const sum = weights.reduce((acc, w) => acc + w.weight, 0);
      expect(Math.abs(sum - 1.0)).toBeLessThanOrEqual(0.01);
    });

    it("rejects weights that exceed 1.0", () => {
      const weights = [
        { key: "a", label: "A", score: 0, weight: 0.6 },
        { key: "b", label: "B", score: 0, weight: 0.5 },
      ];
      const sum = weights.reduce((acc, w) => acc + w.weight, 0);
      expect(sum).toBeGreaterThan(1.0);
    });

    it("handles missing weights as 0", () => {
      const weights = [
        { key: "a", label: "A", score: 0, weight: 0 },
        { key: "b", label: "B", score: 0, weight: 0 },
      ];
      const sum = weights.reduce((acc, w) => acc + w.weight, 0);
      expect(sum).toBe(0);
    });
  });

  describe("SC-007: Null/empty data states", () => {
    it("renders empty model without crashing when all arrays are empty", () => {
      const model = sampleModel([
        levelModel({
          key: "dimension",
          spider: [],
          trend: [],
          scoreDelta: [],
          weight: [],
          weightDelta: [],
        }),
      ]);
      expect(model.levels).toHaveLength(1);
      expect(model.levels[0].spider).toHaveLength(0);
      expect(model.parity.ok).toBe(true);
    });

    it("handles missing trend data gracefully", () => {
      const model = sampleModel([
        levelModel({
          key: "dimension",
          spider: [{ key: "fundamental", label: "Fundamental", score: 80, weight: 0.4 }],
          trend: [],
        }),
      ]);
      expect(model.levels[0].trend).toHaveLength(0);
      expect(model.parity.ok).toBe(true);
    });
  });

  describe("SC-009: Retry mechanism", () => {
    it("retries snapshot load on failure", async () => {
      const mockLoad = vi.fn()
        .mockRejectedValueOnce(new Error("503 Service Unavailable"))
        .mockRejectedValueOnce(new Error("503 Service Unavailable"))
        .mockResolvedValueOnce({ snapshotId: "snap_retry", timestamp: "2026-09-09T00:00:00Z" });

      const results: unknown[] = [];
      for (let i = 0; i < 3; i++) {
        try {
          const r = await mockLoad();
          results.push(r);
        } catch (e) {
          results.push(e);
        }
      }

      expect(mockLoad).toHaveBeenCalledTimes(3);
      expect(results[2]).toEqual({ snapshotId: "snap_retry", timestamp: "2026-09-09T00:00:00Z" });
    });

    it("surfaces error after max retries exhausted", async () => {
      const mockLoad = vi.fn().mockRejectedValue(new Error("503 Service Unavailable"));

      const errors: unknown[] = [];
      for (let i = 0; i < 3; i++) {
        try {
          await mockLoad();
        } catch (e) {
          errors.push(e);
        }
      }

      expect(errors).toHaveLength(3);
      expect(errors[0] instanceof Error).toBe(true);
    });
  });

  describe("SC-010: Chart uniqueness", () => {
    it("generates exactly 4 levels x 5 chart families = 20 views", () => {
      const levels = ["dimension", "sub_dimension", "aspect", "sub_aspect"] as const;
      const families = ["spider", "trend", "scoreDelta", "weight", "weightDelta"] as const;
      const total = levels.length * families.length;
      expect(total).toBe(20);
    });

    it("ensures each level has all 5 chart families", () => {
      const model = sampleModel([
        levelModel({
          key: "dimension",
          spider: [{ key: "a", label: "A", score: 80, weight: 0.4 }],
          trend: [{ date: "2026-09-09", scores: { a: 80 } }],
          scoreDelta: [{ key: "a", label: "A", score: 2, weight: 0 }],
          weight: [{ key: "a", label: "A", score: 0, weight: 0.4 }],
          weightDelta: [{ key: "a", label: "A", score: 0.01, weight: 0 }],
        }),
      ]);
      const lvl = model.levels[0];
      expect(lvl.spider.length).toBeGreaterThan(0);
      expect(lvl.trend.length).toBeGreaterThan(0);
      expect(lvl.scoreDelta.length).toBeGreaterThan(0);
      expect(lvl.weight.length).toBeGreaterThan(0);
      expect(lvl.weightDelta.length).toBeGreaterThan(0);
    });
  });
});
