import { render, screen, fireEvent } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { StockSearchBar } from '@/components/search/StockSearchBar';
import { useStockSearch } from '@/hooks/useStockSearch';
import type { StockSearchResult } from '@/hooks/types';

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

vi.mock('@/hooks/useStockSearch');

const setQuery = vi.fn();
const clearResults = vi.fn();

const baseHook = {
  query: '',
  results: [],
  status: 'idle' as const,
  error: null,
  setQuery,
  clearResults,
};

const mockResults: StockSearchResult[] = [
  { symbol: 'AAPL', name: 'Apple Inc.', sector: 'Technology', price: 178.45, change: 4.0, changePct: 2.3 },
  { symbol: 'TSLA', name: 'Tesla Inc.', sector: 'Automotive', price: 240.5, change: -5.2, changePct: -2.1 },
];

beforeEach(() => {
  vi.mocked(useStockSearch).mockReturnValue({ ...baseHook });
  mockPush.mockClear();
  setQuery.mockClear();
  clearResults.mockClear();
});

const focusInput = () => fireEvent.focus(screen.getByRole('combobox'));

describe('StockSearchBar', () => {
  it('renders the search input with the provided placeholder', () => {
    render(<StockSearchBar placeholder="Search stocks..." />);

    expect(screen.getByRole('combobox')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Search stocks...')).toBeInTheDocument();
  });

  it('renders a search icon and keyboard hint when empty', () => {
    render(<StockSearchBar />);

    expect(screen.getByRole('combobox')).toHaveAttribute('aria-expanded', 'false');
    expect(screen.getByText('K')).toBeInTheDocument();
    expect(document.querySelector('kbd')).not.toBeNull();
  });

  it('shows recent-searches quick picks when focused and empty', () => {
    render(<StockSearchBar recentSearches={['AAPL', 'TSLA']} />);

    focusInput();

    expect(screen.getByText('Quick picks')).toBeInTheDocument();
    expect(screen.getByText('AAPL')).toBeInTheDocument();
    expect(screen.getByText('TSLA')).toBeInTheDocument();
  });

  it('typing calls setQuery on the search hook', () => {
    render(<StockSearchBar />);

    fireEvent.change(screen.getByRole('combobox'), { target: { value: 'app' } });

    expect(setQuery).toHaveBeenCalledWith('app');
  });

  it('renders search results with icons, price, and change', () => {
    vi.mocked(useStockSearch).mockReturnValue({
      ...baseHook,
      query: 'app',
      status: 'success',
      results: mockResults,
    });

    render(<StockSearchBar />);
    focusInput();

    expect(screen.getByText('AAPL')).toBeInTheDocument();
    expect(screen.getByRole('option', { name: /Apple Inc/i })).toBeInTheDocument();
    expect(screen.getByText('Technology')).toBeInTheDocument();
    expect(screen.getByText('$178.45')).toBeInTheDocument();
    expect(screen.getByText('TSLA')).toBeInTheDocument();
  });

  it('clicking a result calls onSelect, persists the recent, and navigates', () => {
    const onSelect = vi.fn();
    const onRecent = vi.fn();
    vi.mocked(useStockSearch).mockReturnValue({
      ...baseHook,
      query: 'app',
      status: 'success',
      results: mockResults,
    });

    render(<StockSearchBar onSelect={onSelect} onRecent={onRecent} />);
    focusInput();

    fireEvent.click(screen.getAllByRole('option')[0]);

    expect(onSelect).toHaveBeenCalledWith(expect.objectContaining({ symbol: 'AAPL', name: 'Apple Inc.' }));
    expect(onRecent).toHaveBeenCalledWith('AAPL');
    expect(mockPush).toHaveBeenCalledWith('/stocks/AAPL');
  });

  it('selecting the first result via enter key navigates', () => {
    const onSelect = vi.fn();
    vi.mocked(useStockSearch).mockReturnValue({
      ...baseHook,
      query: 'app',
      status: 'success',
      results: mockResults,
    });

    render(<StockSearchBar onSelect={onSelect} />);
    const input = screen.getByRole('combobox');
    focusInput();

    fireEvent.keyDown(input, { key: 'ArrowDown' });
    fireEvent.keyDown(input, { key: 'Enter' });

    expect(onSelect).toHaveBeenCalledWith(expect.objectContaining({ symbol: 'AAPL', name: 'Apple Inc.' }));
    expect(mockPush).toHaveBeenCalledWith('/stocks/AAPL');
  });

  it('shows a clear button and clears results when clicked', () => {
    vi.mocked(useStockSearch).mockReturnValue({
      ...baseHook,
      query: 'app',
      status: 'idle',
    });

    render(<StockSearchBar />);

    const clear = screen.getByLabelText('Clear search');
    expect(clear).toBeInTheDocument();

    fireEvent.click(clear);

    expect(clearResults).toHaveBeenCalled();
  });

  it('shows a loading spinner while searching', () => {
    vi.mocked(useStockSearch).mockReturnValue({
      ...baseHook,
      query: 'app',
      status: 'loading',
    });

    render(<StockSearchBar />);
    focusInput();

    expect(screen.getByText('Searching...')).toBeInTheDocument();
    expect(screen.queryByLabelText('Clear search')).not.toBeInTheDocument();
  });

  it('shows an empty state with a helpful message', () => {
    vi.mocked(useStockSearch).mockReturnValue({
      ...baseHook,
      query: 'xyz',
      status: 'empty',
    });

    render(<StockSearchBar />);
    focusInput();

    expect(screen.getByText(/No stock matches your query/)).toBeInTheDocument();
  });

  it('shows an error message when the search fails', () => {
    vi.mocked(useStockSearch).mockReturnValue({
      ...baseHook,
      query: 'xyz',
      status: 'error',
      error: 'Network error',
    });

    render(<StockSearchBar />);
    focusInput();

    expect(screen.getByText('Network error')).toBeInTheDocument();
  });

  it('clicking a quick pick populates the query and records it', () => {
    const onRecent = vi.fn();
    vi.mocked(useStockSearch).mockReturnValue({
      ...baseHook,
      query: '',
      status: 'idle',
    });

    render(<StockSearchBar recentSearches={['AAPL']} onRecent={onRecent} />);
    focusInput();

    fireEvent.click(screen.getByRole('option', { name: 'AAPL' }));

    expect(setQuery).toHaveBeenCalledWith('AAPL');
    expect(onRecent).toHaveBeenCalledWith('AAPL');
  });
});
