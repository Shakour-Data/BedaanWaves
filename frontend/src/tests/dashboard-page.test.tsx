import { vi } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';

const { routerPush, fetchGeneralDashboard, fetchScoreTrend, fetchSubDimensionTrend,
  fetchAspectTrend, fetchSubAspectTrend, fetchCoefficientHistory, fetchDashboardData, addToast }
  = vi.hoisted(() => ({
    routerPush: vi.fn(),
    fetchGeneralDashboard: vi.fn(),
    fetchScoreTrend: vi.fn(),
    fetchSubDimensionTrend: vi.fn(),
    fetchAspectTrend: vi.fn(),
    fetchSubAspectTrend: vi.fn(),
    fetchCoefficientHistory: vi.fn(),
    fetchDashboardData: vi.fn(),
    addToast: vi.fn(),
  }));

import DashboardPage from '@/app/dashboard/page';

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: routerPush,
    replace: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
    prefetch: vi.fn(),
  }),
  useSearchParams: () => ({
    get: (key: string) => (key === 'tab' ? null : null),
  }),
}));

vi.mock('@/lib/api/dashboard', () => ({
  fetchGeneralDashboard,
  fetchScoreTrend,
  fetchSubDimensionTrend,
  fetchAspectTrend,
  fetchSubAspectTrend,
  fetchCoefficientHistory,
  fetchDashboardData,
  fetchTechnicalDashboard: vi.fn(),
  fetchFundamentalDashboard: vi.fn(),
  fetchNewsDashboard: vi.fn(),
  fetchRiskDashboard: vi.fn(),
  fetchBoardDashboard: vi.fn(),
  fetchAiDashboard: vi.fn(),
}));

vi.mock('@/store/useUXStore', () => ({
  useUXStore: (selector: (s: { addToast: typeof addToast }) => unknown) =>
    selector({ addToast }),
}));

vi.mock('@/store/useAppStore', () => ({
  useAppStore: () => ({ theme: 'light' }),
}));

vi.mock('@/components/charts/SpiderChart', () => ({
  SpiderChart: ({
    data,
    onLabelClick,
  }: {
    data: Array<{ label: string; value: number }>;
    onLabelClick?: (label: string) => void;
  }) => (
    <div data-testid="spider-chart">
      {data.map((d) => (
        <button
          key={d.label}
          data-testid={`spider-label-${d.label}`}
          onClick={() => onLabelClick?.(d.label)}
        >
          {d.label}: {d.value}
        </button>
      ))}
    </div>
  ),
}));

vi.mock('@/components/charts/ScoreTrendChart', () => ({
  ScoreTrendChart: () => <div data-testid="score-trend-chart" />,
}));

vi.mock('@/components/charts/CoefficientChart', () => ({
  CoefficientChart: () => <div data-testid="coefficient-chart" />,
}));

vi.mock('@/components/charts/ColumnChart', () => ({
  ColumnChart: () => <div data-testid="column-chart" />,
}));

vi.mock('@/components/charts/BarChart', () => ({
  BarChart: () => <div data-testid="bar-chart" />,
}));

vi.mock('@/components/dashboard/DimensionDashboard', () => ({
  DimensionDashboard: () => <div data-testid="dimension-dashboard" />,
}));

vi.mock('@/components/dashboard/NewsDashboard', () => ({
  NewsDashboard: () => <div data-testid="news-dashboard" />,
}));

vi.mock('@/components/dashboard/BoardDashboard', () => ({
  BoardDashboard: () => <div data-testid="board-dashboard" />,
}));

vi.mock('@/components/dashboard/AiDashboard', () => ({
  AiDashboard: () => <div data-testid="ai-dashboard" />,
}));

const mockGeneralData = {
  status: 'success',
  summary: { total_symbols: 1000, total_signals: 50, total_news: 12 },
  dimensions: {
    fundamental: { avg_score: 70, min_score: 30, max_score: 95, stdev: 8, count: 1000, distribution: { strong: 100, neutral: 500, weak: 400 } },
    technical: { avg_score: 65, min_score: 25, max_score: 90, stdev: 7, count: 1000, distribution: { strong: 80, neutral: 520, weak: 400 } },
    sentiment: { avg_score: 60, min_score: 20, max_score: 85, stdev: 6, count: 1000, distribution: { strong: 70, neutral: 530, weak: 400 } },
    risk: { avg_score: 55, min_score: 15, max_score: 80, stdev: 5, count: 1000, distribution: { strong: 60, neutral: 540, weak: 400 } },
    macro: { avg_score: 60, min_score: 18, max_score: 88, stdev: 6, count: 1000, distribution: { strong: 65, neutral: 535, weak: 400 } },
    ai: { avg_score: 65, min_score: 22, max_score: 92, stdev: 7, count: 1000, distribution: { strong: 75, neutral: 525, weak: 400 } },
  },
  coefficients: [
    { key: 'fundamental', label: 'Fundamental', weight: 0.25 },
    { key: 'technical', label: 'Technical', weight: 0.20 },
    { key: 'sentiment', label: 'Sentiment', weight: 0.15 },
    { key: 'risk', label: 'Risk', weight: 0.20 },
    { key: 'macro', label: 'Macro', weight: 0.10 },
    { key: 'ai', label: 'AI', weight: 0.10 },
  ],
  symbols: [],
  top_performers: [{ symbol: 'AAPL', name: 'Apple', overall_score: 95 }],
  bottom_performers: [{ symbol: 'XYZ', name: 'XYZ Corp', overall_score: 20 }],
  latest_date: '2026-08-31',
  timestamp: '2026-08-31T22:00:00Z',
};

const mockScoreTrend = {
  status: 'success',
  days: 30,
  market: 'NASDAQ',
  count: 3,
  dimensions: ['fundamental', 'technical', 'sentiment', 'risk', 'macro', 'ai'],
  series: [
    {
      date: '2026-08-29',
      avg_score: 54.76,
      avg_dimensions: { fundamental: 50, technical: 54.84, sentiment: 52, risk: 55, macro: 60, ai: 56 },
      score_change: 0,
      technical_change: 0,
      dimension_changes: { fundamental: 0, technical: 0, sentiment: 0, risk: 0, macro: 0, ai: 0 },
      symbol_count: 5600,
    },
    {
      date: '2026-08-30',
      avg_score: 55.11,
      avg_dimensions: { fundamental: 51, technical: 55.0, sentiment: 53, risk: 56, macro: 60, ai: 57 },
      score_change: 0.35,
      technical_change: 0.16,
      dimension_changes: { fundamental: 1, technical: 0.16, sentiment: 1, risk: 1, macro: 0, ai: 1 },
      symbol_count: 5600,
    },
    {
      date: '2026-08-31',
      avg_score: 55.51,
      avg_dimensions: { fundamental: 52, technical: 55.56, sentiment: 54, risk: 57, macro: 61, ai: 58 },
      score_change: 0.40,
      technical_change: 0.56,
      dimension_changes: { fundamental: 1, technical: 0.56, sentiment: 1, risk: 1, macro: 1, ai: 1 },
      symbol_count: 5600,
    },
  ],
  latest_date: '2026-08-31',
  timestamp: '2026-08-31T22:00:00Z',
};

const mockLevelTrend = (level: 'sub_dimension' | 'aspect' | 'sub_aspect') => ({
  status: 'success',
  level,
  days: 30,
  market: 'NASDAQ',
  count: 1,
  keys: level === 'sub_dimension'
    ? ['valuation', 'profitability']
    : level === 'aspect'
      ? ['aspect_a']
      : ['sub_aspect_a'],
  series: [
    {
      date: '2026-08-31',
      avg_scores: level === 'sub_dimension'
        ? { valuation: 60, profitability: 55 }
        : level === 'aspect'
          ? { aspect_a: 60 }
          : { sub_aspect_a: 60 },
      score_changes: level === 'sub_dimension'
        ? { valuation: 1, profitability: 0.5 }
        : level === 'aspect'
          ? { aspect_a: 1 }
          : { sub_aspect_a: 1 },
      symbol_count: 5600,
    },
  ],
  latest_date: '2026-08-31',
  timestamp: '2026-08-31T22:00:00Z',
});

const mockCoefficientHistory = {
  status: 'success',
  days: 30,
  market: 'NASDAQ',
  count: 1,
  dimensions: ['fundamental', 'technical'],
  series: [
    {
      date: '2026-08-31',
      dimensions: { fundamental: 0.25, technical: 0.20 },
      dimension_changes: { fundamental: 0, technical: 0 },
    },
  ],
  latest_date: '2026-08-31',
  timestamp: '2026-08-31T22:00:00Z',
};

const mockDashboardData = {
  marketStats: [
    { label: 'Active Symbols', value: '1,000', changePct: 0 },
  ],
  topMovers: [
    { symbol: 'AAPL', name: 'Apple', market: 'NASDAQ' as const, price: 0, changePct: 0 },
  ],
  watchlist: [],
  news: [
    { title: 'Test News', source: 'Test Source', time: '2 hours ago' },
  ],
  live: true,
};

function setupSuccessfulMocks() {
  fetchGeneralDashboard.mockResolvedValue(mockGeneralData);
  fetchScoreTrend.mockResolvedValue(mockScoreTrend);
  fetchSubDimensionTrend.mockResolvedValue(mockLevelTrend('sub_dimension'));
  fetchAspectTrend.mockResolvedValue(mockLevelTrend('aspect'));
  fetchSubAspectTrend.mockResolvedValue(mockLevelTrend('sub_aspect'));
  fetchCoefficientHistory.mockResolvedValue(mockCoefficientHistory);
  fetchDashboardData.mockResolvedValue(mockDashboardData);
}

beforeEach(() => {
  vi.clearAllMocks();
  routerPush.mockClear();
  setupSuccessfulMocks();
});

describe('DashboardPage', () => {
  it('renders loading state initially', () => {
    fetchGeneralDashboard.mockImplementation(() => new Promise(() => {}));
    fetchScoreTrend.mockImplementation(() => new Promise(() => {}));
    fetchDashboardData.mockImplementation(() => new Promise(() => {}));

    render(<DashboardPage />);

    expect(screen.getAllByRole('presentation', { hidden: true }).length).toBeGreaterThanOrEqual(0);
  });

  it('renders the SpiderChart with 6D scores after data loads', async () => {
    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByTestId('spider-chart')).toBeInTheDocument();
    });

    expect(screen.getByTestId('spider-label-Fundamental')).toBeInTheDocument();
    expect(screen.getByTestId('spider-label-Technical')).toBeInTheDocument();
    expect(screen.getByTestId('spider-label-Sentiment')).toBeInTheDocument();
    expect(screen.getByTestId('spider-label-Risk')).toBeInTheDocument();
    expect(screen.getByTestId('spider-label-Macro')).toBeInTheDocument();
    expect(screen.getByTestId('spider-label-AI')).toBeInTheDocument();
  });

  it('renders the "30-Day Trend" section after data loads', async () => {
    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText('30-Day Trend')).toBeInTheDocument();
    });
  });

  it('navigates to the correct tab when a dimension label is clicked', async () => {
    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByTestId('spider-label-Risk')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId('spider-label-Risk'));

    await waitFor(() => {
      expect(routerPush).toHaveBeenCalledWith('/dashboard?tab=risk');
    });
  });

  it('navigates to the fundamental tab when Fundamental label is clicked', async () => {
    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByTestId('spider-label-Fundamental')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId('spider-label-Fundamental'));

    await waitFor(() => {
      expect(routerPush).toHaveBeenCalledWith('/dashboard?tab=fundamental');
    });
  });

  it('can expand the Sub-Level Score Trends section and renders child sections', async () => {
    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText('Sub-Level Score Trends')).toBeInTheDocument();
    });

    expect(screen.queryByText('Sub-Dimension Score Trend')).not.toBeInTheDocument();

    const expandButton = screen.getByRole('button', { name: /Sub-Level Score Trends/i });
    fireEvent.click(expandButton);

    await waitFor(() => {
      expect(screen.getByText('Sub-Dimension Score Trend')).toBeInTheDocument();
      expect(screen.getByText('Aspect Score Trend')).toBeInTheDocument();
      expect(screen.getByText('Sub-Aspect Score Trend')).toBeInTheDocument();
    });
  });
});