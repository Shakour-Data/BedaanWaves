import { vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import RankingPage from '@/app/ranking/page';
import { fetchNasdaqRankings } from '@/lib/api/ranking';
import { useAuthStore } from '@/store/useAuthStore';

vi.mock('@/lib/api/ranking', () => ({
  fetchNasdaqRankings: vi.fn(),
}));

vi.mock('@/store/useAuthStore', () => ({
  useAuthStore: vi.fn(),
}));

vi.mock('@/components/layout/NewDashboardShell', () => ({
  NewDashboardShell: ({ children }: { children: React.ReactNode }) => <div data-testid="dashboard-shell">{children}</div>,
}));

vi.mock('@/components/ui/TarotCard', () => ({
  TarotCard: ({ children }: { children: React.ReactNode }) => <div data-testid="tarot-card">{children}</div>,
}));

vi.mock('@/components/ui/PrimaryButton', () => ({
  PrimaryButton: (props: Record<string, unknown>) => <button data-testid="primary-button" {...props}>{props.children as string}</button>,
}));

vi.mock('@/components/ui/PageLoading', () => ({
  PageLoading: () => <div data-testid="page-loading">Loading</div>,
}));

vi.mock('@/components/ui/ErrorMessage', () => ({
  ErrorMessage: (props: Record<string, unknown>) => <div data-testid="error-message">{props.message as string}</div>,
}));

describe('RankingPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (useAuthStore as unknown as { mockReturnValue: (val: { currentLang: string }) => void }).mockReturnValue({ currentLang: 'en' });
  });

  it('should show loading state initially', () => {
    (fetchNasdaqRankings as unknown as { mockImplementation: (fn: () => Promise<never>) => void }).mockImplementation(() => new Promise(() => {}));
    render(<RankingPage />);
    expect(screen.getByTestId('page-loading')).toBeInTheDocument();
  });

  it('should render rankings when data loads', async () => {
    (fetchNasdaqRankings as unknown as { mockResolvedValue: (value: { items: Array<{ symbol: string; name: string; rank: number; overall_score: number; grade: string; fundamental: number; technical: number; sentiment: number; risk: number; macro: number; ai: number }>; total: number }) => void }).mockResolvedValue({
      items: [
        { symbol: 'AAPL', name: 'Apple Inc.', rank: 1, overall_score: 95, grade: 'A_STRONG_BUY', fundamental: 90, technical: 95, sentiment: 92, risk: 88, macro: 80, ai: 94 },
        { symbol: 'MSFT', name: 'Microsoft Corp.', rank: 2, overall_score: 88, grade: 'B_BUY', fundamental: 85, technical: 87, sentiment: 86, risk: 82, macro: 78, ai: 90 }
      ],
      total: 2
    });

    render(<RankingPage />);

    await waitFor(() => expect(screen.getByText('Apple Inc.')).toBeInTheDocument());
    expect(screen.getByText('Microsoft Corp.')).toBeInTheDocument();
    expect(screen.getByText('Strong Buy')).toBeInTheDocument();
    expect(screen.getByText('Buy')).toBeInTheDocument();
  });

  it('should show error message on fetch failure', async () => {
    (fetchNasdaqRankings as unknown as { mockRejectedValue: (error: Error) => void }).mockRejectedValue(new Error('API Error'));

    render(<RankingPage />);

    await waitFor(() => expect(screen.getByTestId('error-message')).toBeInTheDocument());
    expect(screen.getByText('Unable to load rankings')).toBeInTheDocument();
  });

  it('should show no results message when items are empty', async () => {
    (fetchNasdaqRankings as unknown as { mockResolvedValue: (value: { items: []; total: number }) => void }).mockResolvedValue({ items: [], total: 0 });

    render(<RankingPage />);

    await waitFor(() => expect(screen.getByText('No stocks found')).toBeInTheDocument());
  });

  it('should change page when next button is clicked', async () => {
    (fetchNasdaqRankings as unknown as { mockResolvedValue: (value: { items: Array<{ symbol: string; name: string; rank: number; overall_score: number; grade: string; fundamental: number; technical: number; sentiment: number; risk: number; macro: number; ai: number }>; total: number }) => void }).mockResolvedValue({
      items: Array.from({ length: 20 }).map((_, i) => ({
        symbol: `SYM${i}`, name: `Symbol ${i}`, rank: i + 1, overall_score: 50, grade: 'C_HOLD', fundamental: 50, technical: 50, sentiment: 50, risk: 50, macro: 50, ai: 50
      })),
      total: 40
    });

    render(<RankingPage />);

    await waitFor(() => expect(screen.getByText('Symbol 0')).toBeInTheDocument());

    const nextButton = screen.getByText('Next');
    nextButton.click();

    await waitFor(() => expect(fetchNasdaqRankings).toHaveBeenCalledWith(expect.objectContaining({ offset: 20 })));
  });
});
