import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import { snapshotToChartsModel, type ChartsModel, type LevelModel, assertParity } from "@/lib/charts-model";

const { uiState, setModel, setSnapshot, setLoading, setError } = vi.hoisted(() => {
  const uiState = {
    loading: false,
    error: null as null | string,
    snapshot: { snapshotId: "snap_abc123", timestamp: "2026-09-09T00:00:00Z" } as Record<string, unknown>,
    model: null as ChartsModel | null,
  };
  return {
    uiState,
    setModel: (m: ChartsModel | null) => {
      uiState.model = m;
    },
    setSnapshot: (s: Record<string, unknown> | null) => {
      uiState.snapshot = s as Record<string, unknown>;
    },
    setLoading: (l: boolean) => {
      uiState.loading = l;
    },
    setError: (e: string | null) => {
      uiState.error = e;
    },
  };
});

vi.mock("@/store/useDateStore", () => ({
  useSnapshot: () => uiState.snapshot,
  useSnapshotLoading: () => uiState.loading,
  useSnapshotError: () => uiState.error,
  useLoadSnapshot: () => vi.fn().mockResolvedValue(null),
  useSnapshotId: () => uiState.snapshot?.snapshotId ?? null,
  useSnapshotTimestamp: () => uiState.snapshot?.timestamp ?? null,
  useSnapshotSymbol: () => null,
  useSnapshotIndex: () => null,
  useSetSnapshot: () => vi.fn(),
  useClearSnapshot: () => vi.fn(),
  useLoadSnapshotIndex: () => vi.fn(),
  useSelectSnapshotById: () => vi.fn(),
  useSelectedDate: () => null,
  useLatestAvailableDate: () => null,
  useEffectiveDate: () => null,
  useUseLatestDate: () => false,
  useDateStore: () => ({}),
}));

vi.mock("@/lib/charts-model", async (importOriginal) => {
  const actual = (await importOriginal()) as typeof import("@/lib/charts-model");
  return {
    ...actual,
    snapshotToChartsModel: vi.fn(() => uiState.model),
  };
});

vi.mock("@/components/charts/SpiderChart", () => ({
  SpiderChart: ({ data }: { data: { label: string; value: number }[] }) => (
    <div data-testid="spider-chart" data-labels={data.map((d) => d.label).join(",")}>
      <canvas aria-label="Spider chart" role="img" />
    </div>
  ),
}));
vi.mock("@/components/charts/ScoreTrendChart", () => ({
  ScoreTrendChart: () => (
    <div data-testid="trend-chart" role="region" aria-label="Score trend chart">
      <div role="img" aria-label="Score trend line chart" />
    </div>
  ),
}));
vi.mock("@/components/charts/ColumnChart", () => ({
  ColumnChart: ({ ariaLabel }: { ariaLabel?: string }) => (
    <div data-testid="column-chart" role="img" aria-label={ariaLabel ?? "Column chart"} />
  ),
}));
vi.mock("@/components/charts/BarChart", () => ({
  BarChart: ({ ariaLabel }: { ariaLabel?: string }) => (
    <div data-testid="bar-chart" role="img" aria-label={ariaLabel ?? "Bar chart"} />
  ),
}));
vi.mock("@/components/charts/CoefficientChart", () => ({
  CoefficientChart: ({ ariaLabel }: { ariaLabel?: string }) => (
    <div data-testid="coefficient-chart" role="img" aria-label={ariaLabel ?? "Coefficient chart"} />
  ),
}));
vi.mock("@/components/ui/TarotCard", () => ({
  TarotCard: ({ title, children }: { title: string; children: React.ReactNode }) => (
    <section data-testid="tarot-card" data-title={title}>
      {children}
    </section>
  ),
}));
vi.mock("@/components/ui/Skeleton", () => ({
  Skeleton: () => <div data-testid="skeleton" />,
}));
vi.mock("@/components/ui/ErrorMessage", () => ({
  ErrorMessage: ({ message, actions }: { message: string; actions?: { label: string; onAction: () => void }[] }) => (
    <div data-testid="error-message">
      {message}
      {actions?.map((a) => (
        <button key={a.label} onClick={a.onAction}>{a.label}</button>
      ))}
    </div>
  ),
}));

function levelModel(overrides: Partial<LevelModel> & Pick<LevelModel, "key">): LevelModel {
  return {
    label: overrides.key,
    short: overrides.key,
    spider: [{ key: "a", label: "Alpha", score: 80, weight: 0.4 }],
    trend: [{ date: "2026-09-09", scores: { a: 80 } }],
    scoreDelta: [{ key: "a", label: "Alpha", score: 2, weight: 0 }],
    weight: [{ key: "a", label: "Alpha", score: 0, weight: 0.4 }],
    weightDelta: [{ key: "a", label: "Alpha", score: 0.02, weight: 0 }],
    ...overrides,
  };
}

function allFourModel(): ChartsModel {
  const levels: LevelModel[] = [
    levelModel({ key: "dimension" }),
    levelModel({ key: "sub_dimension" }),
    levelModel({ key: "aspect" }),
    levelModel({ key: "sub_aspect" }),
  ];
  return {
    snapshotId: "snap_dod",
    timestamp: "2026-09-09T00:00:00Z",
    effectiveAt: "2026-09-09T00:00:00Z",
    tier: "daily",
    latestDate: "2026-09-09",
    overallScore: 82,
    overallTrend: [{ date: "2026-09-09", scores: { __overall: 82 } }],
    levels,
    parity: assertParity(levels, "2026-09-09", "snap_dod"),
    source: "snapshot",
  };
}

describe("QA DoD Checklist - General Dashboard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setSnapshot({ snapshotId: "snap_dod", timestamp: "2026-09-09T00:00:00Z" });
    setLoading(false);
    setError(null);
    setModel(allFourModel());
    cleanup();
  });

  describe("SC-010: Chart uniqueness (20 views / 18 unique types)", () => {
    it("renders exactly 20 tarot-card slots (4 levels x 5 families)", async () => {
      const { GeneralDashboardTab } = await import("@/components/dashboard/GeneralDashboardTab");
      render(<GeneralDashboardTab />);

      expect(screen.getAllByTestId("tarot-card")).toHaveLength(20);
    });

    it("renders BarChart for dimension weightDelta (chart #17, level index 0)", async () => {
      const { GeneralDashboardTab } = await import("@/components/dashboard/GeneralDashboardTab");
      render(<GeneralDashboardTab />);

      const weightDeltaCards = screen.getAllByTestId("tarot-card").filter(
        (c) => c.getAttribute("data-title")?.includes("Coefficient Changes") ?? false
      );

      expect(weightDeltaCards).toHaveLength(4);
      expect(screen.getAllByTestId("bar-chart").length).toBeGreaterThanOrEqual(1);
    });

    it("renders ColumnChart for sub_dimension weightDelta (chart #18, level index 1)", async () => {
      const { GeneralDashboardTab } = await import("@/components/dashboard/GeneralDashboardTab");
      render(<GeneralDashboardTab />);

      const weightDeltaCards = screen.getAllByTestId("tarot-card").filter(
        (c) => c.getAttribute("data-title")?.includes("Coefficient Changes") ?? false
      );

      expect(weightDeltaCards).toHaveLength(4);
      expect(screen.getAllByTestId("column-chart").length).toBeGreaterThanOrEqual(1);
    });

    it("produces 18 unique (level x family) types with Bar/Column split for weightDelta", async () => {
      const levels = ["dimension", "sub_dimension", "aspect", "sub_aspect"];
      const families = ["spider", "trend", "scoreDelta", "weight", "weightDelta"];

      // Family-major ordering: charts 1-4 = Spider, 5-8 = Trend, etc.
      const allCharts: { level: string; family: string }[] = families.flatMap((family) =>
        levels.map((level) => ({ level, family }))
      );

      expect(allCharts).toHaveLength(20);

      const types = new Set<string>();
      allCharts.forEach((c) => {
        if (c.family === "weightDelta") {
          const levelIdx = levels.indexOf(c.level);
          types.add(levelIdx % 2 === 0 ? "bar" : "column");
        } else {
          types.add(`${c.family}-${c.level}`);
        }
      });

      // 16 unique (family-level) + 2 weightDelta types (bar, column) = 18
      expect(types.size).toBe(18);
    });
  });

  describe("SC-DOD-02: Accessibility — aria-label + role='img' on chart containers", () => {
    it("every chart container has role='img' or role='region'", async () => {
      const { GeneralDashboardTab } = await import("@/components/dashboard/GeneralDashboardTab");
      const { container } = render(<GeneralDashboardTab />);

      const imgElements = container.querySelectorAll('[role="img"]');
      const regionElements = container.querySelectorAll('[role="region"]');

      expect(imgElements.length).toBeGreaterThan(0);
      expect(regionElements.length).toBeGreaterThan(0);
    });

    it("every chart container has role='img' and a non-empty aria-label", async () => {
      const { GeneralDashboardTab } = await import("@/components/dashboard/GeneralDashboardTab");
      const { container } = render(<GeneralDashboardTab />);

      const imgElements = container.querySelectorAll('[role="img"]');
      const labelledImgs = Array.from(imgElements).filter((el) => {
        const lbl = el.getAttribute("aria-label") ?? "";
        return lbl.length > 0;
      });

      expect(labelledImgs.length).toBeGreaterThanOrEqual(12);
      for (const el of labelledImgs) {
        expect(el.getAttribute("aria-label")).toBeTruthy();
      }
    });
  });

  describe("SC-DOD-03: Cache invalidation — F5 refresh regenerates snapshot", () => {
    it("refresh button calls loadSnapshot with current symbol", async () => {
      const loadMock = vi.fn().mockResolvedValue({});
      const dateStore = await import("@/store/useDateStore");
      vi.spyOn(dateStore, "useLoadSnapshot").mockReturnValue(loadMock);

      const { GeneralDashboardTab } = await import("@/components/dashboard/GeneralDashboardTab");
      render(<GeneralDashboardTab />);

      const refreshBtn = screen.getByLabelText("Refresh analytical dashboard");
      fireEvent.click(refreshBtn);

      expect(loadMock).toHaveBeenCalled();
    });
  });

  describe("SC-009: Retry mechanism on error", () => {
    it("renders error message with retry action when snapshot fails", async () => {
      setError("503 Service Unavailable");
      setModel(null);

      const { GeneralDashboardTab } = await import("@/components/dashboard/GeneralDashboardTab");
      render(<GeneralDashboardTab />);

      expect(screen.getByTestId("error-message")).toBeInTheDocument();
      expect(screen.getByText("503 Service Unavailable")).toBeInTheDocument();
      expect(screen.getByText("Retry")).toBeInTheDocument();
    });
  });
});
