import {
  toTimestamp,
  normalizeChartData,
  createOrdinalTickMarkFormatter,
} from "@/components/charts/chart-time";

describe("toTimestamp", () => {
  it("passes finite numeric timestamps through unchanged", () => {
    expect(toTimestamp(1705276800, 0, new Map())).toBe(1705276800);
  });

  it("converts a valid ISO date string to epoch seconds", () => {
    const labels = new Map<number, string>();
    const result = toTimestamp("2024-01-15", 0, labels);
    expect(result).toBe(Math.floor(Date.parse("2024-01-15") / 1000));
    expect(labels.has(0)).toBe(false);
  });

  it("treats the crashing symbol ACONW as an ordinal label instead of a date", () => {
    const labels = new Map<number, string>();
    const result = toTimestamp("ACONW", 3, labels);
    expect(result).toBe(3);
    expect(labels.get(3)).toBe("ACONW");
  });

  it("treats a symbol-looking string with digits as an ordinal label", () => {
    const labels = new Map<number, string>();
    expect(toTimestamp("NASDAQ-100", 1, labels)).toBe(1);
    expect(labels.get(1)).toBe("NASDAQ-100");
  });

  it("treats non-date strings as ordinal labels", () => {
    const labels = new Map<number, string>();
    expect(toTimestamp("Hello", 5, labels)).toBe(5);
    expect(labels.get(5)).toBe("Hello");
  });
});

describe("normalizeChartData", () => {
  it("keeps date-based series as epoch timestamps with no ordinal labels", () => {
    const { data, ordinalLabels } = normalizeChartData([
      { time: "2024-01-15", value: 72.5 },
      { time: "2024-01-16", value: 80.0 },
    ]);
    expect(data).toHaveLength(2);
    expect(data[0].time).toBe(Math.floor(Date.parse("2024-01-15") / 1000));
    expect(data[1].time).toBe(Math.floor(Date.parse("2024-01-16") / 1000));
    expect(ordinalLabels.size).toBe(0);
  });

  it("converts symbol-based series into ordinal indices with symbol labels", () => {
    const { data, ordinalLabels } = normalizeChartData([
      { time: "ACONW", value: 72.5 },
      { time: "AAPL", value: 80.0 },
    ]);
    expect(data).toEqual([
      { time: 0, value: 72.5 },
      { time: 1, value: 80.0 },
    ]);
    expect(ordinalLabels.get(0)).toBe("ACONW");
    expect(ordinalLabels.get(1)).toBe("AAPL");
  });
});

describe("createOrdinalTickMarkFormatter", () => {
  it("returns the symbol label for a registered ordinal tick", () => {
    const labels = new Map<number, string>([
      [0, "ACONW"],
      [1, "AAPL"],
    ]);
    const formatter = createOrdinalTickMarkFormatter(labels);
    expect(formatter(0, 0, "en-US")).toBe("ACONW");
    expect(formatter(1, 1, "en-US")).toBe("AAPL");
  });

  it("returns an empty string for ticks without a registered label", () => {
    const formatter = createOrdinalTickMarkFormatter(new Map());
    expect(formatter(42, 0, "en-US")).toBe("");
  });
});
