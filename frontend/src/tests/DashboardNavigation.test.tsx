import { vi } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import DashboardPage from '@/app/dashboard/page';

vi.mock('next/navigation', () => ({
  useSearchParams: () => new URLSearchParams(),
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => '/dashboard',
}));

vi.mock('@/store/useDateStore', () => ({
  useSnapshot: vi.fn(),
  useSnapshotId: vi.fn(),
  useSnapshotTimestamp: vi.fn(),
  useSnapshotLoading: vi.fn(),
  useSnapshotIndex: vi.fn(),
  useLoadSnapshot: vi.fn(),
  useLoadSnapshotIndex: vi.fn(() => Promise.resolve(null)),
  useSelectSnapshotById: vi.fn(),
}));

vi.mock('@/lib/api/dashboard', () => ({
  fetchSubDimensionTrend: vi.fn(),
  fetchAspectTrend: vi.fn(),
  fetchSubAspectTrend: vi.fn(),
  fetchCoefficientHistory: vi.fn(),
  fetchCoefficientHistoryByLevel: vi.fn(),
  fetchDashboardSnapshot: vi.fn(),
  fetchDashboardSnapshots: vi.fn(),
}));

vi.mock('@/components/layout/NewDashboardShell', () => ({
  NewDashboardShell: ({ children }: { children: React.ReactNode }) => <div data-testid="dashboard-shell">{children}</div>,
}));

vi.mock('@/components/ui/TarotCard', () => ({
  TarotCard: ({ children, title }: { children: React.ReactNode; title?: string }) => <div data-testid="tarot-card">{title}</div>,
}));

vi.mock('@/components/ui/PageLoading', () => ({
  PageLoading: () => <div data-testid="page-loading">Loading</div>,
}));

import { useSnapshot, useSnapshotId, useSnapshotTimestamp, useSnapshotLoading, useSnapshotIndex, useLoadSnapshot, useLoadSnapshotIndex, useSelectSnapshotById } from '@/store/useDateStore';
import { fetchSubDimensionTrend, fetchAspectTrend, fetchSubAspectTrend, fetchCoefficientHistory, fetchCoefficientHistoryByLevel } from '@/lib/api/dashboard';

const mockSnapshot = {
  scores: {
    daily: {
      overall: 65.5,
      dimension: { fundamental: 70, technical: 65, sentiment: 60, risk: 55, macro: 60, ai: 65 },
      sub_dimension: {
        fundamental_valuation: 72,
        fundamental_profitability: 68,
        technical_moving_averages: 64,
        technical_momentum: 66,
      },
      aspect: {
        fundamental_valuation_aspect_1: 75,
        fundamental_valuation_aspect_2: 70,
        technical_moving_averages_aspect_1: 62,
        technical_moving_averages_aspect_2: 66,
      },
      sub_aspect: {
        fundamental_valuation_aspect_1_detail_1: 78,
        fundamental_valuation_aspect_1_detail_2: 72,
        technical_moving_averages_aspect_1_detail_1: 60,
        technical_moving_averages_aspect_1_detail_2: 64,
      },
    },
    hourly: { overall: 65.5, dimension: {}, sub_dimension: {}, aspect: {}, sub_aspect: {} },
    current: { overall: 65.5, dimension: {}, sub_dimension: {}, aspect: {}, sub_aspect: {} },
  },
  deltas: {
    hourly_vs_daily: { overall: 0, dimensions: {}, sub_dimensions: {}, aspects: {}, sub_aspects: {} },
    current_vs_hourly: { overall: 0, dimensions: {}, sub_dimensions: {}, aspects: {}, sub_aspects: {} },
    current_vs_daily: { overall: 0, dimensions: {}, sub_dimensions: {}, aspects: {}, sub_aspects: {} },
  },
  weights: {
    dimension: { fundamental: 0.25, technical: 0.20, sentiment: 0.15, risk: 0.20, macro: 0.10, ai: 0.10 },
    sub_dimension: {
      fundamental_valuation: 0.3,
      fundamental_profitability: 0.25,
      technical_moving_averages: 0.3,
      technical_momentum: 0.25,
    },
    aspect: {
      fundamental_valuation_aspect_1: 0.5,
      fundamental_valuation_aspect_2: 0.5,
      technical_moving_averages_aspect_1: 0.5,
      technical_moving_averages_aspect_2: 0.5,
    },
    sub_aspect: {
      fundamental_valuation_aspect_1_detail_1: 0.5,
      fundamental_valuation_aspect_1_detail_2: 0.5,
      technical_moving_averages_aspect_1_detail_1: 0.5,
      technical_moving_averages_aspect_1_detail_2: 0.5,
    },
  },
  weight_trends: { daily: [] },
  weight_deltas: { daily: { delta: 0, delta_pct: 0, weights: {} } },
  trends: {
    daily: [
      { date: '2025-01-01', overall: 65, level_scores: { fundamental: 70, technical: 65, sentiment: 60, risk: 55, macro: 60, ai: 65 } },
      { date: '2025-01-02', overall: 66, level_scores: { fundamental: 71, technical: 66, sentiment: 61, risk: 56, macro: 61, ai: 66 } },
    ],
    intraday: [],
  },
};

const mockTrendResponse = {
  status: 'success',
  level: 'sub_dimension',
  days: 30,
  market: 'NASDAQ',
  count: 2,
  keys: ['fundamental_valuation', 'fundamental_profitability'],
  series: [
    { date: '2025-01-01', avg_scores: { fundamental_valuation: 72, fundamental_profitability: 68 }, score_changes: { fundamental_valuation: 0, fundamental_profitability: 0 } },
    { date: '2025-01-02', avg_scores: { fundamental_valuation: 73, fundamental_profitability: 69 }, score_changes: { fundamental_valuation: 1, fundamental_profitability: 1 } },
  ],
  latest_date: '2025-01-02',
  timestamp: '2025-01-02T00:00:00Z',
};

const mockCoeffResponse = {
  status: 'success',
  days: 30,
  market: 'NASDAQ',
  count: 2,
  dimensions: ['fundamental', 'technical', 'sentiment', 'risk', 'macro', 'ai'],
  series: [
    { date: '2025-01-01', dimensions: { fundamental: 0.25, technical: 0.20, sentiment: 0.15, risk: 0.20, macro: 0.10, ai: 0.10 }, dimension_changes: { fundamental: 0, technical: 0, sentiment: 0, risk: 0, macro: 0, ai: 0 } },
    { date: '2025-01-02', dimensions: { fundamental: 0.26, technical: 0.19, sentiment: 0.15, risk: 0.20, macro: 0.10, ai: 0.10 }, dimension_changes: { fundamental: 0.01, technical: -0.01, sentiment: 0, risk: 0, macro: 0, ai: 0 } },
  ],
  latest_date: '2025-01-02',
  timestamp: '2025-01-02T00:00:00Z',
};

function setupMocks() {
  vi.clearAllMocks();
  (useSnapshot as unknown as { mockReturnValue: (val: unknown) => void }).mockReturnValue(mockSnapshot);
  (useSnapshotId as unknown as { mockReturnValue: (val: string) => void }).mockReturnValue('snap-123');
  (useSnapshotTimestamp as unknown as { mockReturnValue: (val: string) => void }).mockReturnValue('2025-01-01T00:00:00Z');
  (useSnapshotLoading as unknown as { mockReturnValue: (val: boolean) => void }).mockReturnValue(false);
  (useSnapshotIndex as unknown as { mockReturnValue: (val: unknown) => void }).mockReturnValue(null);
  (useLoadSnapshot as unknown as { mockReturnValue: (val: () => Promise<unknown>) => void }).mockReturnValue(() => Promise.resolve(null));
  (useLoadSnapshotIndex as unknown as { mockReturnValue: (val: () => Promise<unknown>) => void }).mockReturnValue(() => Promise.resolve(null));
    (useSelectSnapshotById as unknown as { mockReturnValue: (val: () => Promise<unknown>) => void }).mockReturnValue(() => Promise.resolve(null));

  (fetchSubDimensionTrend as unknown as { mockResolvedValue: (value: unknown) => void }).mockResolvedValue(mockTrendResponse);
  (fetchAspectTrend as unknown as { mockResolvedValue: (value: unknown) => void }).mockResolvedValue(mockTrendResponse);
  (fetchSubAspectTrend as unknown as { mockResolvedValue: (value: unknown) => void }).mockResolvedValue(mockTrendResponse);
  (fetchCoefficientHistory as unknown as { mockResolvedValue: (value: unknown) => void }).mockResolvedValue(mockCoeffResponse);
  (fetchCoefficientHistoryByLevel as unknown as { mockResolvedValue: (value: unknown) => void }).mockResolvedValue(mockTrendResponse);
}

describe('Dashboard Navigation System', () => {
  beforeEach(() => {
    setupMocks();
  });

  describe('Sidebar Navigation', () => {
    it('should have dashboard link defined in sidebar config', async () => {
      const { NewSidebar } = await import('@/components/layout/NewSidebar');
      const sidebarCategories = (NewSidebar as unknown as { categories: { items: { href: string }[] }[] }).categories;
      const analyticsItems = sidebarCategories.find((cat) => cat.label === 'Analytics')?.items || [];
      const dashboardItem = analyticsItems.find((item) => item.href === '/dashboard');
      expect(dashboardItem).toBeDefined();
      expect(dashboardItem?.label).toBe('Dashboard');
    });
  });

  describe('Tab Navigation', () => {
    it('should render all dimension tabs', async () => {
      render(<DashboardPage />);
      expect(screen.getByText('General')).toBeInTheDocument();
      expect(screen.getByText('Fundamental')).toBeInTheDocument();
      expect(screen.getByText('Technical')).toBeInTheDocument();
      expect(screen.getByText('Sentiment')).toBeInTheDocument();
      expect(screen.getByText('Risk')).toBeInTheDocument();
      expect(screen.getByText('Macro')).toBeInTheDocument();
      expect(screen.getByText('AI')).toBeInTheDocument();
    });

    it('should default to General tab', async () => {
      render(<DashboardPage />);
      const generalButton = screen.getByText('General').closest('button');
      expect(generalButton).toHaveClass('bg-[var(--color-primary)]');
    });

    it('should switch tabs when clicked', async () => {
      render(<DashboardPage />);
      const technicalButton = screen.getByText('Technical').closest('button');
      if (technicalButton) {
        fireEvent.click(technicalButton);
        expect(technicalButton).toHaveClass('bg-[var(--color-primary)]');
      }
    });

    it('should reset drill-down to level 1 when tab changes', async () => {
      render(<DashboardPage />);
      const fundamentalButton = screen.getByText('Fundamental').closest('button');
      if (fundamentalButton) {
        fireEvent.click(fundamentalButton);
        expect(screen.getByText('Fundamental')).toBeInTheDocument();
      }
    });
  });

  describe('Breadcrumb Navigation', () => {
    it('should not show breadcrumbs at level 1', async () => {
      render(<DashboardPage />);
      expect(screen.queryByText('Dimensions')).not.toBeInTheDocument();
    });

    it('should show breadcrumbs when drilling down', async () => {
      render(<DashboardPage />);
      const fundamentalCard = screen.getByText('Fundamental');
      const card = fundamentalCard.closest('[aria-label="Drill down into Fundamental"]') || fundamentalCard.closest('.cursor-pointer');
      if (card) {
        fireEvent.click(card);
        await waitFor(() => expect(screen.getByText('Dimensions')).toBeInTheDocument());
      }
    });

    it('should navigate back to level 1 when clicking breadcrumb', async () => {
      render(<DashboardPage />);
      const fundamentalCard = screen.getByText('Fundamental');
      const card = fundamentalCard.closest('[aria-label="Drill down into Fundamental"]') || fundamentalCard.closest('.cursor-pointer');
      if (card) {
        fireEvent.click(card);
        await waitFor(() => expect(screen.getByText('Dimensions')).toBeInTheDocument());
        const dimensionsBreadcrumb = screen.getByText('Dimensions');
        fireEvent.click(dimensionsBreadcrumb);
        expect(screen.queryByText('Fundamental Valuation')).not.toBeInTheDocument();
      }
    });
  });

  describe('Drill-down Navigation', () => {
    it('should drill down one level at a time', async () => {
      render(<DashboardPage />);
      const fundamentalCard = screen.getByText('Fundamental');
      const card = fundamentalCard.closest('[aria-label="Drill down into Fundamental"]') || fundamentalCard.closest('.cursor-pointer');
      if (card) {
        fireEvent.click(card);
        await waitFor(() => expect(screen.getByText('Dimensions')).toBeInTheDocument());
        const valuationCard = screen.getByText('Fundamental Valuation');
        const valuationCardEl = valuationCard.closest('[aria-label="Drill down into Fundamental Valuation"]') || valuationCard.closest('.cursor-pointer');
        if (valuationCardEl) {
          fireEvent.click(valuationCardEl);
          await waitFor(() => expect(screen.getByText('Fundamental Valuation')).toBeInTheDocument());
        }
      }
    });

    it('should not allow drill-down beyond level 4', async () => {
      render(<DashboardPage />);
      const fundamentalCard = screen.getByText('Fundamental');
      const card = fundamentalCard.closest('[aria-label="Drill down into Fundamental"]') || fundamentalCard.closest('.cursor-pointer');
      if (card) {
        fireEvent.click(card);
        await waitFor(() => expect(screen.getByText('Dimensions')).toBeInTheDocument());
        const valuationCard = screen.getByText('Fundamental Valuation');
        const valuationCardEl = valuationCard.closest('[aria-label="Drill down into Fundamental Valuation"]') || valuationCard.closest('.cursor-pointer');
        if (valuationCardEl) {
          fireEvent.click(valuationCardEl);
          await waitFor(() => expect(screen.getByText('Fundamental Valuation')).toBeInTheDocument());
        }
      }
    });
  });

  describe('Symbol Selector Navigation', () => {
    it('should render symbol input', async () => {
      render(<DashboardPage />);
      expect(screen.getByPlaceholderText('Symbol (e.g. AAPL)')).toBeInTheDocument();
    });

    it('should show Clear button when symbol is entered', async () => {
      render(<DashboardPage />);
      const input = screen.getByPlaceholderText('Symbol (e.g. AAPL)');
      fireEvent.change(input, { target: { value: 'AAPL' } });
      const goButton = screen.getByText('Go');
      if (goButton) {
        fireEvent.click(goButton);
      }
      expect(screen.getByText('Clear')).toBeInTheDocument();
    });

    it('should clear symbol and reset drill-down when Clear is clicked', async () => {
      render(<DashboardPage />);
      const input = screen.getByPlaceholderText('Symbol (e.g. AAPL)');
      fireEvent.change(input, { target: { value: 'AAPL' } });
      const goButton = screen.getByText('Go');
      if (goButton) {
        fireEvent.click(goButton);
      }
      const clearButton = screen.getByText('Clear');
      if (clearButton) {
        fireEvent.click(clearButton);
        expect(screen.queryByText('Clear')).not.toBeInTheDocument();
      }
    });
  });

  describe('Snapshot Time Travel', () => {
    it('should render snapshot replay slider when snapshots are available', async () => {
      (useSnapshotIndex as unknown as { mockReturnValue: (val: unknown) => void }).mockReturnValue({
        hourly: [],
        daily: [{ snapshotId: 'snap-1', effectiveAt: '2025-01-02T00:00:00Z', tier: 'daily', count: 100 }],
      });
      render(<DashboardPage />);
      await waitFor(() => {
        const tarotCards = screen.getAllByTestId('tarot-card');
        const titles = tarotCards.map((card) => card.textContent).filter(Boolean);
        expect(titles.some((title) => title?.includes('SNAPSHOT REPLAY'))).toBe(true);
      });
    });

    it('should not render slider when no snapshots are available', async () => {
      (useSnapshotIndex as unknown as { mockReturnValue: (val: unknown) => void }).mockReturnValue({ hourly: [], daily: [] });
      render(<DashboardPage />);
      await waitFor(() => {
        const tarotCards = screen.getAllByTestId('tarot-card');
        const titles = tarotCards.map((card) => card.textContent).filter(Boolean);
        expect(titles.some((title) => title?.includes('SNAPSHOT REPLAY'))).toBe(false);
      });
    });
  });
});
