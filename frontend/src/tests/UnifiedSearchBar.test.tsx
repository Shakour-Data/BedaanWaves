import { render, screen, fireEvent } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { UnifiedSearchBar } from '@/components/search/UnifiedSearchBar';
import { useUnifiedSearch } from '@/hooks/useUnifiedSearch';

const { mockPush } = vi.hoisted(() => ({ mockPush: vi.fn() }));

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: vi.fn(),
    back: vi.fn(),
    refresh: vi.fn(),
    prefetch: vi.fn(),
  }),
}));

vi.mock('@/hooks/useUnifiedSearch');

const setQuery = vi.fn();
const clear = vi.fn();

const baseHook = {
  query: '',
  debouncedQuery: '',
  status: 'idle' as const,
  error: null,
  groups: [] as { label: string; items: unknown[] }[],
  total: 0,
  isStockLoading: false,
  isNewsLoading: false,
  setQuery,
  clear,
};

const stockResults = [
  {
    kind: 'stock' as const,
    symbol: 'AAPL',
    name: 'Apple Inc.',
    sector: 'Technology',
    price: 178.45,
    change: 4.0,
    changePct: 2.3,
  },
  {
    kind: 'stock' as const,
    symbol: 'NVDA',
    name: 'NVIDIA Corp.',
    sector: 'Technology',
    price: 540.2,
    change: 12.5,
    changePct: 2.4,
  },
];

const newsResults = [
  {
    kind: 'news' as const,
    id: 'n1',
    title: 'Apple announces new product line',
    source: 'Bloomberg',
    url: 'https://example.com/a',
    publishedAt: new Date().toISOString(),
    category: 'technology',
    isMarketMoving: true,
  },
];

const pageResults = [
  {
    kind: 'page' as const,
    id: 'page-leaderboard',
    title: 'Leaderboard',
    href: '/leaderboard',
    description: 'Top scoring NASDAQ equities by overall or dimension',
    category: 'Analytics' as const,
    keywords: ['leaderboard', 'top', 'ranking'],
  },
];

beforeEach(() => {
  vi.mocked(useUnifiedSearch).mockReturnValue({ ...baseHook });
  mockPush.mockClear();
  setQuery.mockClear();
  clear.mockClear();
});

const focusInput = () => fireEvent.focus(screen.getByRole('combobox'));

describe('UnifiedSearchBar', () => {
  it('renders the search input with the provided placeholder', () => {
    render(<UnifiedSearchBar placeholder="Find anything..." />);
    expect(screen.getByRole('combobox')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Find anything...')).toBeInTheDocument();
  });

  it('typing propagates the query to the hook', () => {
    render(<UnifiedSearchBar />);
    fireEvent.change(screen.getByRole('combobox'), { target: { value: 'app' } });
    expect(setQuery).toHaveBeenCalledWith('app');
  });

  it('renders stock results grouped under "Stocks"', () => {
    vi.mocked(useUnifiedSearch).mockReturnValue({
      ...baseHook,
      query: 'app',
      debouncedQuery: 'app',
      status: 'success',
      groups: [{ label: 'Stocks', items: stockResults }],
      total: stockResults.length,
    });

    render(<UnifiedSearchBar />);
    focusInput();

    expect(screen.getByText('Stocks')).toBeInTheDocument();
    expect(screen.getAllByText((content, element) => element?.textContent?.includes('Apple Inc.') ?? false).length).toBeGreaterThan(0);
    expect(screen.getByText('NVDA')).toBeInTheDocument();
    expect(screen.getAllByText((content, element) => element?.textContent?.includes('178.45') ?? false).length).toBeGreaterThan(0);
  });

  it('renders news results with source and timestamp', () => {
    vi.mocked(useUnifiedSearch).mockReturnValue({
      ...baseHook,
      query: 'apple',
      debouncedQuery: 'apple',
      status: 'success',
      groups: [{ label: 'News', items: newsResults }],
      total: newsResults.length,
    });

    render(<UnifiedSearchBar />);
    focusInput();

    expect(screen.getByText('News')).toBeInTheDocument();
    expect(screen.getAllByText((content, element) => element?.textContent?.includes('Apple announces new product line') ?? false).length).toBeGreaterThan(0);
    expect(screen.getByText(/Bloomberg/)).toBeInTheDocument();
  });

  it('renders page results with category and description', () => {
    vi.mocked(useUnifiedSearch).mockReturnValue({
      ...baseHook,
      query: 'leader',
      debouncedQuery: 'leader',
      status: 'success',
      groups: [{ label: 'Pages', items: pageResults }],
      total: pageResults.length,
    });

    render(<UnifiedSearchBar />);
    focusInput();

    expect(screen.getByText('Pages')).toBeInTheDocument();
    expect(screen.getAllByText((content, element) => element?.textContent?.includes('Leaderboard') ?? false).length).toBeGreaterThan(0);
    expect(screen.getAllByText((content, element) => element?.textContent?.includes('Analytics') ?? false).length).toBeGreaterThan(0);
  });

  it('clicking a stock result navigates to the stock page', () => {
    vi.mocked(useUnifiedSearch).mockReturnValue({
      ...baseHook,
      query: 'app',
      debouncedQuery: 'app',
      status: 'success',
      groups: [{ label: 'Stocks', items: stockResults }],
      total: stockResults.length,
    });

    render(<UnifiedSearchBar />);
    focusInput();

    fireEvent.click(screen.getAllByRole('option')[0]);
    expect(mockPush).toHaveBeenCalledWith('/stocks/AAPL');
  });

  it('clicking a page result navigates to the page href', () => {
    vi.mocked(useUnifiedSearch).mockReturnValue({
      ...baseHook,
      query: 'leader',
      debouncedQuery: 'leader',
      status: 'success',
      groups: [{ label: 'Pages', items: pageResults }],
      total: pageResults.length,
    });

    render(<UnifiedSearchBar />);
    focusInput();

    fireEvent.click(screen.getByRole('option', { name: /Leaderboard/i }));
    expect(mockPush).toHaveBeenCalledWith('/leaderboard');
  });

  it('shows an empty-state message when there are no results', () => {
    vi.mocked(useUnifiedSearch).mockReturnValue({
      ...baseHook,
      query: 'zzz',
      debouncedQuery: 'zzz',
      status: 'empty',
    });

    render(<UnifiedSearchBar />);
    focusInput();

    expect(screen.getByText(/No results for/)).toBeInTheDocument();
  });

  it('shows an error message when the search fails', () => {
    vi.mocked(useUnifiedSearch).mockReturnValue({
      ...baseHook,
      query: 'foo',
      debouncedQuery: 'foo',
      status: 'error',
      error: 'Boom',
    });

    render(<UnifiedSearchBar />);
    focusInput();

    expect(screen.getByText('Boom')).toBeInTheDocument();
  });

  it('clear button resets the hook state', () => {
    vi.mocked(useUnifiedSearch).mockReturnValue({
      ...baseHook,
      query: 'app',
      debouncedQuery: 'app',
      status: 'success',
    });

    render(<UnifiedSearchBar />);
    fireEvent.click(screen.getByLabelText('Clear search'));
    expect(clear).toHaveBeenCalled();
  });
});
