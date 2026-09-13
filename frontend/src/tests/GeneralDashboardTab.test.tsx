import { vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { GeneralDashboardTab } from "@/components/dashboard/GeneralDashboardTab";
import type { ChartsModel, LevelModel } from "@/lib/charts-model";

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
  ErrorMessage: ({ message }: { message: string }) => (
    <div data-testid="error-message">{message}</div>
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
    weightDelta: [{ key: "a", label: "Alpha", score: 2, weight: 0 }],
    ...overrides,
  };
}

function sampleModel(levels: LevelModel[]): ChartsModel {
  return {
    snapshotId: "snap_abc123",
    timestamp: "2026-09-09T00:00:00Z",
    effectiveAt: "2026-09-09T00:00:00Z",
    tier: "daily",
    latestDate: "2026-09-09",
    overallScore: 82,
    overallTrend: [{ date: "2026-09-09", scores: { __overall: 82 } }],
    levels,
    parity: { ok: true, tolerance: 0.01, latestDate: "2026-09-09", snapshotId: "snap_abc123", mismatches: [] },
    source: "snapshot",
  };
}

describe("GeneralDashboardTab", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setSnapshot({ snapshotId: "snap_abc123", timestamp: "2026-09-09T00:00:00Z" });
    setLoading(false);
    setError(null);
    setModel(null);
  });

  it("renders a skeleton grid while loading and there is no model", () => {
    setLoading(true);
    setSnapshot({ snapshotId: "snap_abc123", timestamp: "2026-09-09T00:00:00Z" });
    setModel(null);
    render(<GeneralDashboardTab />);
    expect(screen.getAllByTestId("skeleton").length).toBeGreaterThanOrEqual(16);
  });

  it("renders the error message when model is null and an error is present", () => {
    setLoading(false);
    setModel(null);
    setError("boom");
    render(<GeneralDashboardTab />);
    expect(screen.getByTestId("error-message")).toHaveTextContent("boom");
  });

  it("renders the analytical charts once the model is available", () => {
    setModel(
      sampleModel([
        levelModel({ key: "dimension" }),
        levelModel({ key: "aspect" }),
      ]),
    );
    render(<GeneralDashboardTab />);

    expect(screen.getByText("Analytical Dashboard")).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent("Data parity verified");
    expect(screen.getByText(/snapshot #/)).toBeInTheDocument();

    expect(screen.getByText(/Dimensions \(1 items\)/)).toBeInTheDocument();
    expect(screen.getByText(/Aspects \(1 items\)/)).toBeInTheDocument();

    expect(screen.getAllByTestId("spider-chart")).toHaveLength(2);
    expect(screen.getAllByTestId("trend-chart")).toHaveLength(2);
    expect(screen.getAllByTestId("column-chart")).toHaveLength(2);
    expect(screen.getAllByTestId("coefficient-chart")).toHaveLength(2);
    expect(screen.getAllByTestId("bar-chart")).toHaveLength(2);
    expect(screen.getAllByTestId("tarot-card")).toHaveLength(10);
  });

  it("renders a parity mismatch banner when the model reports mismatches", () => {
    const model = sampleModel([levelModel({ key: "dimension" })]);
    model.parity = {
      ok: false,
      tolerance: 0.01,
      latestDate: "2026-09-09",
      snapshotId: "snap_abc123",
      mismatches: [{ level: "dimension", key: "a", spider: 80, trendLast: 75 }],
    };
    setModel(model);
    render(<GeneralDashboardTab />);
    expect(screen.getByRole("status")).toHaveTextContent(/1 parity mismatch/i);
  });

  it("passes a symbol prop through to the snapshot loader", () => {
    setModel(sampleModel([levelModel({ key: "dimension" })]));
    render(<GeneralDashboardTab symbol="AAPL" />);
    expect(screen.getByText(/snapshot #/)).toBeInTheDocument();
  });
});
