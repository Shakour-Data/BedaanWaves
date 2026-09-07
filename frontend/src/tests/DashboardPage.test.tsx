import { vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
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

describe('DashboardPage', () => {
  const mockSnapshot = {
    scores: {
      daily: {
        overall: 65.5,
        dimension: { fundamental: 70, technical: 65, sentiment: 60, risk: 55, macro: 60, ai: 65 },
        sub_dimension: { fundamental_valuation: 72, fundamental_profitability: 68, technical_moving_averages: 64, technical_momentum: 66 },
        aspect: { fundamental_valuation_aspect_1: 75, fundamental_valuation_aspect_2: 70 },
        sub_aspect: { fundamental_valuation_aspect_1_detail_1: 78, fundamental_valuation_aspect_1_detail_2: 72 },
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
      sub_dimension: {},
      aspect: {},
      sub_aspect: {},
    },
    weight_trends: { daily: [] },
    weight_deltas: { daily: { delta: 0, delta_pct: 0, weights: {} } },
    trends: { daily: [], intraday: [] },
  } as const;

  beforeEach(() => {
    vi.clearAllMocks();
    (useSnapshot as unknown as { mockReturnValue: (val: unknown) => void }).mockReturnValue(mockSnapshot);
    (useSnapshotId as unknown as { mockReturnValue: (val: string) => void }).mockReturnValue('snap-123');
    (useSnapshotTimestamp as unknown as { mockReturnValue: (val: string) => void }).mockReturnValue('2025-01-01T00:00:00Z');
    (useSnapshotLoading as unknown as { mockReturnValue: (val: boolean) => void }).mockReturnValue(false);
    (useSnapshotIndex as unknown as { mockReturnValue: (val: unknown) => void }).mockReturnValue(null);
    (useLoadSnapshot as unknown as { mockReturnValue: (val: () => Promise<unknown>) => void }).mockReturnValue(() => Promise.resolve(null));
    (useLoadSnapshotIndex as unknown as { mockReturnValue: (val: () => Promise<unknown>) => void }).mockReturnValue(() => Promise.resolve(null));
    (useSelectSnapshotById as unknown as { mockReturnValue: (val: unknown) => void }).mockReturnValue(null);

    (fetchSubDimensionTrend as unknown as { mockResolvedValue: (value: unknown) => void }).mockResolvedValue({
      status: 'success',
      level: 'sub_dimension',
      days: 30,
      market: 'NASDAQ',
      count: 10,
      keys: ['fundamental_valuation', 'fundamental_profitability'],
      series: [],
      latest_date: '2025-01-01',
      timestamp: '2025-01-01T00:00:00Z',
    });
    (fetchAspectTrend as unknown as { mockResolvedValue: (value: unknown) => void }).mockResolvedValue({
      status: 'success',
      level: 'aspect',
      days: 30,
      market: 'NASDAQ',
      count: 10,
      keys: ['fundamental_valuation_aspect_1', 'fundamental_valuation_aspect_2'],
      series: [],
      latest_date: '2025-01-01',
      timestamp: '2025-01-01T00:00:00Z',
    });
    (fetchSubAspectTrend as unknown as { mockResolvedValue: (value: unknown) => void }).mockResolvedValue({
      status: 'success',
      level: 'sub_aspect',
      days: 30,
      market: 'NASDAQ',
      count: 10,
      keys: ['fundamental_valuation_aspect_1_detail_1', 'fundamental_valuation_aspect_1_detail_2'],
      series: [],
      latest_date: '2025-01-01',
      timestamp: '2025-01-01T00:00:00Z',
    });
    (fetchCoefficientHistory as unknown as { mockResolvedValue: (value: unknown) => void }).mockResolvedValue({
      status: 'success',
      days: 30,
      market: 'NASDAQ',
      count: 10,
      dimensions: ['fundamental', 'technical', 'sentiment', 'risk', 'macro', 'ai'],
      series: [],
      latest_date: '2025-01-01',
      timestamp: '2025-01-01T00:00:00Z',
    });
    (fetchCoefficientHistoryByLevel as unknown as { mockResolvedValue: (value: unknown) => void }).mockResolvedValue({
      status: 'success',
      level: 'sub_dimension',
      days: 30,
      market: 'NASDAQ',
      parent: null,
      count: 10,
      latest_date: '2025-01-01',
      series: [],
      timestamp: '2025-01-01T00:00:00Z',
    });
  });

  it('should render dashboard shell', async () => {
    render(<DashboardPage />);
    expect(screen.getByTestId('dashboard-shell')).toBeInTheDocument();
  });

  it('should render general tab by default', async () => {
    render(<DashboardPage />);
    expect(screen.getByText('General')).toBeInTheDocument();
  });

  it('should render all dimension tabs', async () => {
    render(<DashboardPage />);
    expect(screen.getByText('Fundamental')).toBeInTheDocument();
    expect(screen.getByText('Technical')).toBeInTheDocument();
    expect(screen.getByText('Sentiment')).toBeInTheDocument();
    expect(screen.getByText('Risk')).toBeInTheDocument();
    expect(screen.getByText('Macro')).toBeInTheDocument();
    expect(screen.getByText('AI')).toBeInTheDocument();
  });

  it('should render dimension cards at level 1', async () => {
    render(<DashboardPage />);
    await waitFor(() => expect(screen.getByText('Fundamental')).toBeInTheDocument());
    expect(screen.getByText('Technical')).toBeInTheDocument();
  });

  it('should show symbol input', async () => {
    render(<DashboardPage />);
    expect(screen.getByPlaceholderText('Symbol (e.g. AAPL)')).toBeInTheDocument();
  });
});
