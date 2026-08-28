import { vi } from 'vitest';
import { fetchNasdaqRankings } from '@/lib/api/ranking';
import { apiClient } from '@/lib/api';

vi.mock('@/lib/api', () => ({
  apiClient: {
    get: vi.fn() } }));

describe('fetchNasdaqRankings', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should call the correct endpoint with query params', async () => {
    const mock = apiClient.get as unknown as {
      mockResolvedValue: (value: unknown) => void;
    };
    mock.mockResolvedValue({
      data: { status: 'success', total: 2, data: [] } });

    await fetchNasdaqRankings({ limit: 10, offset: 20, sort_by: 'technical', order: 'asc' });

    expect(apiClient.get).toHaveBeenCalledWith('/ranking/nasdaq?limit=10&offset=20&sort_by=technical&order=asc');
  });

  it('should normalize envelope with data array', async () => {
    const mock = apiClient.get as unknown as {
      mockResolvedValue: (value: unknown) => void;
    };
    mock.mockResolvedValue({
      data: {
        status: 'success',
        total: 2,
        data: [
          { symbol: 'AAPL', name: 'Apple', rank: 1, overall_score: 90, grade: 'A_STRONG_BUY', fundamental: 80, technical: 95, sentiment: 85, risk: 90, macro: 70, ai: 88 },
          { symbol: 'MSFT', name: 'Microsoft', rank: 2, overall_score: 85, grade: 'B_BUY' }
        ] } });

    const result = await fetchNasdaqRankings({ limit: 2, offset: 0 });

    expect(result.items).toHaveLength(2);
    expect(result.items[0].symbol).toBe('AAPL');
    expect(result.items[0].name).toBe('Apple');
    expect(result.items[0].overall_score).toBe(90);
    expect(result.items[0].grade).toBe('A_STRONG_BUY');
    expect(result.items[1].name).toBe('MSFT');
    expect(result.total).toBe(2);
  });

  it('should normalize envelope with items array fallback', async () => {
    const mock = apiClient.get as unknown as {
      mockResolvedValue: (value: unknown) => void;
    };
    mock.mockResolvedValue({
      data: {
        status: 'success',
        total: 1,
        items: [
          { symbol: 'GOOGL', overall_score: 70, grade: 'C_HOLD' }
        ] } });

    const result = await fetchNasdaqRankings();

    expect(result.items).toHaveLength(1);
    expect(result.items[0].symbol).toBe('GOOGL');
    expect(result.items[0].name).toBe('GOOGL');
    expect(result.items[0].overall_score).toBe(70);
  });

  it('should normalize plain array response', async () => {
    const mock = apiClient.get as unknown as {
      mockResolvedValue: (value: unknown) => void;
    };
    mock.mockResolvedValue({
      data: [
        { symbol: 'TSLA', rank: 3, overall_score: 60, grade: 'D_SELL' }
      ] });

    const result = await fetchNasdaqRankings();

    expect(result.items).toHaveLength(1);
    expect(result.items[0].symbol).toBe('TSLA');
    expect(result.total).toBe(1);
  });

  it('should default missing numeric fields to 0 and grade to C_HOLD', async () => {
    const mock = apiClient.get as unknown as {
      mockResolvedValue: (value: unknown) => void;
    };
    mock.mockResolvedValue({
      data: {
        total: 1,
        data: [
          { symbol: 'NVDA' }
        ] } });

    const result = await fetchNasdaqRankings();

    expect(result.items[0].name).toBe('NVDA');
    expect(result.items[0].rank).toBe(0);
    expect(result.items[0].overall_score).toBe(0);
    expect(result.items[0].grade).toBe('C_HOLD');
    expect(result.items[0].fundamental).toBe(0);
    expect(result.items[0].technical).toBe(0);
  });
});
