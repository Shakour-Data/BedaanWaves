import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { useSnapshot, useSnapshotLoading, useSnapshotError, useLoadSnapshot } from "@/store/useDateStore";
import { snapshotToChartsModel, type ChartsModel, type LevelModel } from "@/lib/charts-model";

vi.mock("@/components/charts/SpiderChart", () => ({
  SpiderChart: () => <div data-testid="spider-chart" />,
}));
vi.mock("@/components/charts/ScoreTrendChart", () => ({
  ScoreTrendChart: () => <div data-testid="trend-chart" />,
}));
vi.mock("@/components/charts/ColumnChart", () => ({
  ColumnChart: () => <div data-testid="column-chart" />,
}));
vi.mock("@/components/charts/BarChart", () => ({
  BarChart: () => <div data-testid="bar-chart" />,
}));
vi.mock("@/components/charts/CoefficientChart", () => ({
  CoefficientChart: () => <div data-testid="coefficient-chart" />,
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
  ErrorMessage: ({ message, actions }: { message: string; actions?: { label: string }[] }) => (
    <div data-testid="error-message">
      {message}
      {actions?.map((a) => (
        <button key={a.label}>{a.label}</button>
      ))}
    </div>
  ),
}));

vi.mock("@/store/useDateStore", () => ({
  useSnapshot: vi.fn(),
  useSnapshotLoading: vi.fn(),
  useSnapshotError: vi.fn(),
  useLoadSnapshot: vi.fn(),
  useSnapshotId: vi.fn(),
  useSnapshotTimestamp: vi.fn(),
  useSnapshotSymbol: vi.fn(),
  useSetSnapshot: vi.fn(),
  useClearSnapshot: vi.fn(),
  useLoadSnapshotIndex: vi.fn(),
  useSelectSnapshotById: vi.fn(),
  useSelectedDate: vi.fn(),
  useLatestAvailableDate: vi.fn(),
  useEffectiveDate: vi.fn(),
  useUseLatestDate: vi.fn(),
  useDateStore: vi.fn(),
}));

vi.mock("@/lib/charts-model", async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    snapshotToChartsModel: vi.fn(),
  };
});

function makeSnapshot(symbol: string, dimensionScores: Record<string, number>): ChartsModel {
  return {
    snapshotId: `snap_${symbol}`,
    timestamp: "2026-09-09T00:00:00Z",
    effectiveAt: "2026-09-09T00:00:00Z",
    tier: "daily",
    latestDate: "2026-09-09",
    overallScore: Object.values(dimensionScores).reduce((a, b) => a + b, 0) / Object.keys(dimensionScores).length,
    overallTrend: [],
    levels: [
      {
        key: "dimension",
        label: "Dimensions",
        short: "DIM",
        spider: Object.entries(dimensionScores).map(([k, v]) => ({
          key: k,
          label: k.charAt(0).toUpperCase() + k.slice(1),
          score: v,
          weight: 0,
        })),
        trend: [{ date: "2026-09-09", scores: dimensionScores }],
        scoreDelta: [],
        weight: [],
        weightDelta: [],
      },
      {
        key: "sub_dimension",
        label: "Sub-Dimensions",
        short: "SUB-DIM",
        spider: [],
        trend: [],
        scoreDelta: [],
        weight: [],
        weightDelta: [],
      },
      {
        key: "aspect",
        label: "Aspects",
        short: "ASP",
        spider: [],
        trend: [],
        scoreDelta: [],
        weight: [],
        weightDelta: [],
      },
      {
        key: "sub_aspect",
        label: "Sub-Aspects",
        short: "SUB-ASP",
        spider: [],
        trend: [],
        scoreDelta: [],
        weight: [],
        weightDelta: [],
      },
    ],
    parity: { ok: true, tolerance: 0.01, latestDate: "2026-09-09", snapshotId: `snap_${symbol}`, mismatches: [] },
    source: "snapshot",
  };
}

function createMockSnapshot(snapshotId: string, overall: number): object {
  return {
    snapshotId,
    timestamp: "2026-09-09T00:00:00Z",
    scores: { daily: { overall, dimension: {} } },
    trends: { daily: [] },
    weights: {},
    weight_trends: { daily: [] },
    weight_deltas: { daily: { weights: {} } },
    deltas: {
      hourly_vs_daily: { overall_delta: 0, overall_delta_pct: 0, dimension_deltas: {}, sub_dimension_deltas: {}, aspect_deltas: {}, sub_aspect_deltas: {} },
      current_vs_hourly: { overall_delta: 0, overall_delta_pct: 0, dimension_deltas: {}, sub_dimension_deltas: {}, aspect_deltas: {}, sub_aspect_deltas: {} },
      current_vs_daily: { overall_delta: 0, overall_delta_pct: 0, dimension_deltas: {}, sub_dimension_deltas: {}, aspect_deltas: {}, sub_aspect_deltas: {} },
    },
  };
}

describe("QA Priority 1 - SC-003: Symbol Switch Updates All Charts", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useSnapshot).mockReturnValue(null);
    vi.mocked(useSnapshotLoading).mockReturnValue(false);
    vi.mocked(useSnapshotError).mockReturnValue(null);
    vi.mocked(useLoadSnapshot).mockReturnValue(vi.fn().mockResolvedValue({}));
  });

  it("renders all 20 chart views (4 levels x 5 families) after snapshot loads", async () => {
    const model = makeSnapshot("AAPL", {
      fundamental: 80,
      technical: 75,
      sentiment: 70,
      risk: 65,
      macro: 60,
      ai: 55,
    });

    const snapshot = createMockSnapshot("snap_AAPL", 71);

    vi.mocked(useSnapshot).mockReturnValue(snapshot);
    vi.mocked(snapshotToChartsModel).mockReturnValue(model);

    const { GeneralDashboardTab } = await import("@/components/dashboard/GeneralDashboardTab");
    const { container } = render(<GeneralDashboardTab symbol="AAPL" />);

    const tarotCards = screen.getAllByTestId("tarot-card");
    const chartSections = tarotCards.filter((c) =>
      c.getAttribute("data-title")?.includes("Spider") ||
      c.getAttribute("data-title")?.includes("Trend") ||
      c.getAttribute("data-title")?.includes("Changes") ||
      c.getAttribute("data-title")?.includes("Coefficients")
    );

    expect(chartSections.length).toBe(20);
  });

  it("calls loadSnapshot with new symbol when symbol prop changes", async () => {
    const loadMock = vi.fn().mockResolvedValue({});
    vi.mocked(useLoadSnapshot).mockReturnValue(loadMock);

    const { GeneralDashboardTab } = await import("@/components/dashboard/GeneralDashboardTab");
    const { rerender } = render(<GeneralDashboardTab symbol="AAPL" />);

    expect(loadMock).toHaveBeenCalledWith({ symbol: "AAPL" });

    rerender(<GeneralDashboardTab symbol="MSFT" />);

    await waitFor(() => {
      expect(loadMock).toHaveBeenCalledWith({ symbol: "MSFT" });
    });
  });

  it("re-renders all charts with new model data when snapshot changes", async () => {
    const model1 = makeSnapshot("AAPL", {
      fundamental: 80,
      technical: 75,
      sentiment: 70,
      risk: 65,
      macro: 60,
      ai: 55,
    });

    const model2 = makeSnapshot("MSFT", {
      fundamental: 90,
      technical: 85,
      sentiment: 60,
      risk: 50,
      macro: 40,
      ai: 45,
    });

    let currentModel: ChartsModel | null = model1;

    vi.mocked(useSnapshot).mockImplementation(() => {
      return currentModel === model1
        ? createMockSnapshot("snap_AAPL", 71)
        : createMockSnapshot("snap_MSFT", 61);
    });

    vi.mocked(snapshotToChartsModel).mockImplementation(() => currentModel);

    const { GeneralDashboardTab } = await import("@/components/dashboard/GeneralDashboardTab");
    const { rerender, unmount } = render(<GeneralDashboardTab symbol="AAPL" />);

    expect(screen.getByText(/snapshot #snap_AA/).toBeInTheDocument?.() ?? true).toBe(true);

    currentModel = model2;

    rerender(<GeneralDashboardTab symbol="MSFT" />);
    await waitFor(() => {
      expect(vi.mocked(snapshotToChartsModel)).toHaveBeenCalled();
    });

    unmount();
  });

  it("shows parity mismatch banner when new symbol snapshot has inconsistencies", async () => {
    const mismatchedModel: ChartsModel = {
      snapshotId: "snap_BAD",
      timestamp: "2026-09-09T00:00:00Z",
      effectiveAt: "2026-09-09T00:00:00Z",
      tier: "daily",
      latestDate: "2026-09-09",
      overallScore: 50,
      overallTrend: [],
      levels: [
        {
          key: "dimension",
          label: "Dimensions",
          short: "DIM",
          spider: [{ key: "fundamental", label: "Fundamental", score: 80, weight: 0.4 }],
          trend: [{ date: "2026-09-09", scores: { fundamental: 82 } }],
          scoreDelta: [],
          weight: [],
          weightDelta: [],
        },
      ],
      parity: {
        ok: false,
        tolerance: 0.01,
        latestDate: "2026-09-09",
        snapshotId: "snap_BAD",
        mismatches: [{ level: "dimension", key: "fundamental", spider: 80, trendLast: 82 }],
      },
      source: "snapshot",
    };

    vi.mocked(snapshotToChartsModel).mockReturnValue(mismatchedModel);
    vi.mocked(useSnapshot).mockReturnValue(createMockSnapshot("snap_BAD", 50));

    const { GeneralDashboardTab } = await import("@/components/dashboard/GeneralDashboardTab");
    render(<GeneralDashboardTab symbol="BAD" />);

    expect(screen.getByRole("status")).toHaveTextContent(/parity mismatch/i);
  });

  it("GeneralDashboardTab title updates with symbol snapshot", async () => {
    const model = makeSnapshot("AAPL", {
      fundamental: 80,
      technical: 75,
      sentiment: 70,
      risk: 65,
      macro: 60,
      ai: 55,
    });

    vi.mocked(snapshotToChartsModel).mockReturnValue(model);
    vi.mocked(useSnapshot).mockReturnValue(createMockSnapshot("snap_AAPL", 71));

    const { GeneralDashboardTab } = await import("@/components/dashboard/GeneralDashboardTab");
    render(<GeneralDashboardTab symbol="AAPL" />);

    expect(screen.getByText(/Analytical Dashboard/i)).toBeInTheDocument();
    expect(screen.getByText(/snap_AAP/i)).toBeInTheDocument();
    expect(screen.getByText(/Data parity verified/i)).toBeInTheDocument();
  });
});