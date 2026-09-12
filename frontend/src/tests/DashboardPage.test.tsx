import { vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import DashboardPage from '@/app/dashboard/page';

const { setSearchParams, getSearchParams } = vi.hoisted(() => {
  let params = new URLSearchParams();
  return {
    getSearchParams: () => params,
    setSearchParams: (p: URLSearchParams) => {
      params = p;
    },
  };
});

vi.mock('next/navigation', () => ({
  useSearchParams: () => getSearchParams(),
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => '/dashboard',
}));

vi.mock('@/components/layout/NewDashboardShell', () => ({
  NewDashboardShell: ({ children, title }: { children: React.ReactNode; title?: string }) => (
    <div data-testid="dashboard-shell" data-title={title ?? ''}>
      {children}
    </div>
  ),
}));

vi.mock('@/components/ui/PageLoading', () => ({
  PageLoading: () => <div data-testid="page-loading">Loading</div>,
}));

vi.mock('@/components/ui/ErrorMessage', () => ({
  ErrorMessage: ({ message }: { message: string }) => <div data-testid="error-message">{message}</div>,
}));

const { mockFetchDashboardData, mockFetchGeneralDashboard } = vi.hoisted(() => ({
  mockFetchDashboardData: vi.fn(),
  mockFetchGeneralDashboard: vi.fn(),
}));

vi.mock('@/lib/api/dashboard', () => ({
  fetchDashboardData: mockFetchDashboardData,
  fetchGeneralDashboard: mockFetchGeneralDashboard,
}));

vi.mock('@/components/search/UnifiedSearchBar', () => ({
  UnifiedSearchBar: () => <div data-testid="unified-search" />,
}));

vi.mock('@/components/dashboard/GeneralDashboardTab', () => ({
  GeneralDashboardTab: () => <section data-testid="general-dashboard-tab">Analytical view</section>,
}));

const generalResponse = {
  status: 'success',
  summary: { total_symbols: 1234, total_signals: 12, total_news: 50 },
  dimensions: {
    fundamental: { avg_score: 72, min_score: 30, max_score: 95, stdev: 10, count: 100, distribution: { strong: 40, neutral: 40, weak: 20 } },
    technical: { avg_score: 65, min_score: 25, max_score: 90, stdev: 12, count: 100, distribution: { strong: 30, neutral: 50, weak: 20 } },
    sentiment: { avg_score: 55, min_score: 10, max_score: 85, stdev: 18, count: 100, distribution: { strong: 20, neutral: 50, weak: 30 } },
  },
  coefficients: [
    { key: 'fundamental', label: 'Fundamental', weight: 0.4 },
    { key: 'technical', label: 'Technical', weight: 0.3 },
    { key: 'sentiment', label: 'Sentiment', weight: 0.3 },
  ],
  symbols: [],
  top_performers: [
    { symbol: 'AAPL', name: 'Apple Inc.', overall_score: 92.3 },
    { symbol: 'NVDA', name: 'NVIDIA', overall_score: 89.1 },
  ],
  bottom_performers: [
    { symbol: 'XYZ', name: 'XYZ Corp', overall_score: 22.1 },
  ],
  latest_date: '2025-01-15',
  timestamp: '2025-01-15T00:00:00Z',
};

const legacyResponse = {
  marketStats: [{ label: 'Active Symbols', value: '1,234', changePct: 0 }],
  topMovers: [
    { symbol: 'AAPL', name: 'Apple Inc.', market: 'NASDAQ' as const, price: 178.45, changePct: 2.3 },
  ],
  watchlist: [],
  news: [
    { title: 'Markets hit new high', source: 'Bloomberg', time: '2m ago' },
  ],
  live: true,
};

describe('DashboardPage (new)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setSearchParams(new URLSearchParams());
    mockFetchGeneralDashboard.mockResolvedValue(generalResponse);
    mockFetchDashboardData.mockResolvedValue(legacyResponse);
  });

  it('renders the dashboard shell', async () => {
    render(<DashboardPage />);
    await waitFor(() => expect(screen.getByTestId('dashboard-shell')).toBeInTheDocument());
  });

  it('shows a loading skeleton on first render', () => {
    mockFetchGeneralDashboard.mockImplementation(() => new Promise(() => {}));
    mockFetchDashboardData.mockImplementation(() => new Promise(() => {}));
    render(<DashboardPage />);
    expect(screen.getByTestId('page-loading')).toBeInTheDocument();
  });

  it('shows KPI cards once data is loaded', async () => {
    render(<DashboardPage />);
    await waitFor(() => expect(screen.getByText('Universe')).toBeInTheDocument());
    expect(screen.getByText('Avg Score')).toBeInTheDocument();
    expect(screen.getByText('Top Scorer')).toBeInTheDocument();
    expect(screen.getByText('1234')).toBeInTheDocument();
  });

  it('renders the top performers and underperformers', async () => {
    render(<DashboardPage />);
    await waitFor(() => expect(screen.getByText('AAPL')).toBeInTheDocument());
    expect(screen.getByText('NVDA')).toBeInTheDocument();
    expect(screen.getByText('XYZ')).toBeInTheDocument();
  });

  it('renders news headlines', async () => {
    render(<DashboardPage />);
    await waitFor(() => expect(screen.getByText('Markets hit new high')).toBeInTheDocument());
  });

  it('renders the unified search bar', async () => {
    render(<DashboardPage />);
    await waitFor(() => expect(screen.getByTestId('unified-search')).toBeInTheDocument());
  });

  it('shows an error state when both endpoints fail', async () => {
    mockFetchGeneralDashboard.mockRejectedValue(new Error('boom'));
    mockFetchDashboardData.mockRejectedValue(new Error('boom'));
    render(<DashboardPage />);
    await waitFor(() => expect(screen.getByTestId('error-message')).toBeInTheDocument());
  });

  it('renders the overview by default and shows KPI cards', async () => {
    render(<DashboardPage />);
    await waitFor(() => expect(screen.getByText('Market Dashboard')).toBeInTheDocument());
    expect(screen.getByText('Universe')).toBeInTheDocument();
  });

  it('renders the analytical tab view when ?tab=general', async () => {
    setSearchParams(new URLSearchParams('tab=general'));
    render(<DashboardPage />);
    await waitFor(() => expect(screen.getByTestId('general-dashboard-tab')).toBeInTheDocument());
    expect(screen.queryByText('Market Dashboard')).not.toBeInTheDocument();
  });

  it('renders a tab switcher with Overview and Analytical tabs', async () => {
    render(<DashboardPage />);
    await waitFor(() => expect(screen.getByRole('tablist', { name: /dashboard views/i })).toBeInTheDocument());
    expect(screen.getByRole('tab', { name: 'Overview' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'Analytical' })).toBeInTheDocument();
  });
});
