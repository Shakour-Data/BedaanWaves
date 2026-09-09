import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { GeneralDashboardTab } from "@/components/dashboard/GeneralDashboardTab";

vi.mock("@/store/useDateStore", () => ({
  useSnapshot: () => null,
  useSnapshotLoading: () => false,
  useSnapshotError: () => null,
  useLoadSnapshot: () => vi.fn(),
  useSnapshotId: () => null,
  useSnapshotTimestamp: () => null,
  useSnapshotSymbol: () => null,
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
  const actual = await importOriginal();
  return {
    ...actual,
    snapshotToChartsModel: vi.fn(() => null),
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

describe("QA Priority 1 - GeneralDashboardTab UI", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders skeleton grid while loading with no model", () => {
    render(<GeneralDashboardTab />);
    const skeletons = screen.getAllByTestId("skeleton");
    expect(skeletons.length).toBeGreaterThanOrEqual(16);
  });

  it("renders error message when model is null and error is present", () => {
    const { useSnapshotError } = require("@/store/useDateStore");
    vi.mocked(useSnapshotError).mockReturnValue("Failed to load snapshot");

    render(<GeneralDashboardTab />);
    expect(screen.getByTestId("error-message")).toHaveTextContent("Failed to load snapshot");
  });

  it("renders retry button in error state", () => {
    const { useSnapshotError, useLoadSnapshot } = require("@/store/useDateStore");
    vi.mocked(useSnapshotError).mockReturnValue("Network error");
    const mockRetry = vi.fn();
    vi.mocked(useLoadSnapshot).mockReturnValue(mockRetry);

    render(<GeneralDashboardTab />);
    const retryButton = screen.getByRole("button", { name: /retry/i });
    expect(retryButton).toBeInTheDocument();
  });

  it("shows parity verified badge when model is valid", () => {
    const { useSnapshot, useSnapshotLoading } = require("@/store/useDateStore");
    const { snapshotToChartsModel } = require("@/lib/charts-model");

    const mockSnapshot = {
      snapshotId: "snap_001",
      timestamp: "2026-09-09T00:00:00Z",
      effectiveAt: "2026-09-09T00:00:00Z",
      tier: "daily" as const,
      scores: {
        daily: {
          fundamental: 80,
          technical: 75,
          sentiment: 70,
          risk: 65,
          macro: 60,
          ai: 55,
          overall: 72,
        },
      },
      trends: {
        daily: [
          {
            date: "2026-09-09",
            overall: 72,
            level_scores: {
              fundamental: 80,
              technical: 75,
              sentiment: 70,
              risk: 65,
              macro: 60,
              ai: 55,
            },
          },
        ],
      },
      weights: {
        dimension: {
          fundamental: 0.4,
          technical: 0.3,
          sentiment: 0.15,
          risk: 0.1,
          macro: 0.05,
          ai: 0,
        },
      },
    };

    vi.mocked(useSnapshot).mockReturnValue(mockSnapshot);
    vi.mocked(useSnapshotLoading).mockReturnValue(false);

    const mocked = vi.mocked(snapshotToChartsModel);
    mocked.mockReturnValue({
      snapshotId: "snap_001",
      timestamp: "2026-09-09T00:00:00Z",
      effectiveAt: "2026-09-09T00:00:00Z",
      tier: "daily",
      latestDate: "2026-09-09",
      overallScore: 72,
      overallTrend: [],
      levels: [
        {
          key: "dimension",
          label: "Dimensions",
          short: "DIM",
          spider: [
            { key: "fundamental", label: "Fundamental", score: 80, weight: 0.4 },
            { key: "technical", label: "Technical", score: 75, weight: 0.3 },
            { key: "sentiment", label: "Sentiment", score: 70, weight: 0.15 },
            { key: "risk", label: "Risk", score: 65, weight: 0.1 },
            { key: "macro", label: "Macro", score: 60, weight: 0.05 },
            { key: "ai", label: "AI", score: 55, weight: 0 },
          ],
          trend: [{ date: "2026-09-09", scores: { fundamental: 80, technical: 75, sentiment: 70, risk: 65, macro: 60, ai: 55 } }],
          scoreDelta: [],
          weight: [],
          weightDelta: [],
        },
      ],
      parity: { ok: true, tolerance: 0.01, latestDate: "2026-09-09", snapshotId: "snap_001", mismatches: [] },
      source: "snapshot",
    });

    render(<GeneralDashboardTab />);
    expect(screen.getByRole("status")).toHaveTextContent("Data parity verified");
  });

  it("renders parity mismatch banner when model reports mismatches", () => {
    const { useSnapshot, useSnapshotLoading } = require("@/store/useDateStore");
    const { snapshotToChartsModel } = require("@/lib/charts-model");

    const mockSnapshot = {
      snapshotId: "snap_001",
      timestamp: "2026-09-09T00:00:00Z",
      effectiveAt: "2026-09-09T00:00:00Z",
      tier: "daily" as const,
      scores: {
        daily: {
          fundamental: 80,
          overall: 72,
        },
      },
      trends: {
        daily: [
          {
            date: "2026-09-09",
            overall: 72,
            level_scores: {
              fundamental: 80,
            },
          },
        ],
      },
      weights: {},
    };

    vi.mocked(useSnapshot).mockReturnValue(mockSnapshot);
    vi.mocked(useSnapshotLoading).mockReturnValue(false);

    const mocked = vi.mocked(snapshotToChartsModel);
    mocked.mockReturnValue({
      snapshotId: "snap_001",
      timestamp: "2026-09-09T00:00:00Z",
      effectiveAt: "2026-09-09T00:00:00Z",
      tier: "daily",
      latestDate: "2026-09-09",
      overallScore: 72,
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
        snapshotId: "snap_001",
        mismatches: [{ level: "dimension", key: "fundamental", spider: 80, trendLast: 82 }],
      },
      source: "snapshot",
    });

    render(<GeneralDashboardTab />);
    expect(screen.getByRole("status")).toHaveTextContent(/1 parity mismatch/i);
  });

  it("passes symbol prop through to snapshot loader", () => {
    const { useLoadSnapshot } = require("@/store/useDateStore");
    const mockLoad = vi.fn().mockResolvedValue({});
    vi.mocked(useLoadSnapshot).mockReturnValue(mockLoad);

    render(<GeneralDashboardTab symbol="AAPL" />);
    expect(mockLoad).toHaveBeenCalledWith(expect.objectContaining({ symbol: "AAPL" }));
  });
});
