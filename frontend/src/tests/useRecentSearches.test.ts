import { renderHook, waitFor } from '@testing-library/react';
import { act } from 'react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { apiClient } from '@/lib/api';
import { useRecentSearches } from '@/hooks/useRecentSearches';

const getSpy = vi.spyOn(apiClient, 'get');
const postSpy = vi.spyOn(apiClient, 'post');

beforeEach(() => {
  getSpy.mockReset();
  postSpy.mockReset();
});

describe('useRecentSearches', () => {
  it('loads recent searches from the backend on mount', async () => {
    getSpy.mockResolvedValueOnce({
      data: { status: 'success', recent_searches: ['AAPL', 'TSLA'] },
    });

    const { result } = renderHook(() => useRecentSearches());

    expect(result.current.loading).toBe(true);
    expect(result.current.recent).toEqual([]);

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.recent).toEqual(['AAPL', 'TSLA']);
    expect(result.current.error).toBeNull();
    expect(getSpy).toHaveBeenCalledWith('/settings/recent-searches');
  });

  it('falls back to an empty list when the request fails', async () => {
    getSpy.mockRejectedValueOnce(new Error('Network error'));

    const { result } = renderHook(() => useRecentSearches());

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.recent).toEqual([]);
    expect(result.current.error).toBe('Network error');
  });

  it('records a search and updates the list from the response', async () => {
    getSpy.mockResolvedValueOnce({ data: { recent_searches: [] } });
    postSpy.mockResolvedValueOnce({
      data: { status: 'success', recent_searches: ['MSFT'] },
    });

    const { result } = renderHook(() => useRecentSearches());
    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      await result.current.addRecent('msft');
    });

    await waitFor(() => expect(result.current.recent).toEqual(['MSFT']));
    expect(postSpy).toHaveBeenCalledWith('/settings/recent-searches', { query: 'MSFT' });
    expect(result.current.error).toBeNull();
  });

  it('ignores an empty query when recording', async () => {
    getSpy.mockResolvedValueOnce({ data: { recent_searches: [] } });

    const { result } = renderHook(() => useRecentSearches());
    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      await result.current.addRecent('   ');
    });

    expect(postSpy).not.toHaveBeenCalled();
  });
});
