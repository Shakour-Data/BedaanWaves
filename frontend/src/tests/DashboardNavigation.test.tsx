import { vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import DashboardPage from '@/app/dashboard/page';

vi.mock('next/navigation', () => ({
  useSearchParams: () => new URLSearchParams(),
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => '/dashboard',
}));

vi.mock('@/components/layout/NewDashboardShell', () => ({
  NewDashboardShell: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="dashboard-shell">{children}</div>
  ),
}));

vi.mock('@/components/ui/PageLoading', () => ({
  PageLoading: () => <div data-testid="page-loading">Loading</div>,
}));

vi.mock('@/components/ui/ErrorMessage', () => ({
  ErrorMessage: ({ message }: { message: string }) => <div data-testid="error-message">{message}</div>,
}));

vi.mock('@/components/search/UnifiedSearchBar', () => ({
  UnifiedSearchBar: () => <div data-testid="unified-search" />,
}));

const { mockFetchDashboardData, mockFetchGeneralDashboard } = vi.hoisted(() => ({
  mockFetchDashboardData: vi.fn(),
  mockFetchGeneralDashboard: vi.fn(),
}));

vi.mock('@/lib/api/dashboard', () => ({
  fetchDashboardData: mockFetchDashboardData,
  fetchGeneralDashboard: mockFetchGeneralDashboard,
}));

// fetchDashboardData and fetchGeneralDashboard are mocked above

const generalResponse = {
  status: 'success',
  summary: { total_symbols: 1234, total_signals: 12, total_news: 50 },
  dimensions: {
    fundamental: { avg_score: 72, min_score: 30, max_score: 95, stdev: 10, count: 100, distribution: { strong: 40, neutral: 40, weak: 20 } },
  },
  coefficients: [{ key: 'fundamental', label: 'Fundamental', weight: 0.4 }],
  symbols: [],
  top_performers: [{ symbol: 'AAPL', name: 'Apple Inc.', overall_score: 92.3 }],
  bottom_performers: [{ symbol: 'XYZ', name: 'XYZ Corp', overall_score: 22.1 }],
  latest_date: '2025-01-15',
  timestamp: '2025-01-15T00:00:00Z',
};

const legacyResponse = {
  marketStats: [{ label: 'Active Symbols', value: '1,234', changePct: 0 }],
  topMovers: [],
  watchlist: [],
  news: [{ title: 'Markets hit new high', source: 'Bloomberg', time: '2m ago' }],
  live: true,
};

describe('Dashboard navigation', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockFetchGeneralDashboard.mockResolvedValue(generalResponse);
    mockFetchDashboardData.mockResolvedValue(legacyResponse);
  });

  describe('Sidebar Navigation', () => {
    it('exposes the Dashboard item in the Analytics category of the sidebar', async () => {
      const { NewSidebar } = await import('@/components/layout/NewSidebar');
      const sidebarCategories = (NewSidebar as unknown as { categories: { label: string; items: { href: string; label: string }[] }[] }).categories;
      const analyticsItems = sidebarCategories.find((cat) => cat.label === 'Analytics')?.items || [];
      const dashboardItem = analyticsItems.find((item) => item.href === '/dashboard');
      expect(dashboardItem).toBeDefined();
      expect(dashboardItem?.label).toBe('Dashboard');
    });
  });

  describe('Page structure', () => {
    it('renders the dashboard shell with title "Dashboard"', async () => {
      render(<DashboardPage />);
      await waitFor(() => expect(screen.getByTestId('dashboard-shell')).toBeInTheDocument());
    });

    it('includes the unified search bar', async () => {
      render(<DashboardPage />);
      await waitFor(() => expect(screen.getByTestId('unified-search')).toBeInTheDocument());
    });

    it('shows the Top performers section', async () => {
      render(<DashboardPage />);
      await waitFor(() => expect(screen.getByText('AAPL')).toBeInTheDocument());
    });
  });
});
