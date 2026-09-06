import { renderHook, waitFor } from '@testing-library/react';
import { act } from 'react';
import { vi, describe, it, expect, beforeEach } from 'vitest';

vi.mock('@/lib/api', () => {
  const createMockClient = () => ({
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
    request: vi.fn(),
    defaults: { headers: { common: {} } },
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
  });

  const apiClient = createMockClient();
  return {
    apiClient,
    getApiErrorMessage: (err: unknown) => {
      if (err instanceof Error) return err.message;
      return String(err);
    },
  };
});

import { apiClient } from '@/lib/api';
import { useRecentSearches } from '@/hooks/useRecentSearches';

const getSpy = apiClient.get;
const postSpy = apiClient.post;

beforeEach(() => {
  apiClient.get.mockReset();
  apiClient.post.mockReset();
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
    getSpy.mockRejectedValueOnce(new Error('Network Error'));

    const { result } = renderHook(() => useRecentSearches());

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.recent).toEqual([]);
    expect(result.current.error).toBe('Network Error');
  });

  it('records a search and updates the list from the response', async () => {
    getSpy.mockResolvedValueOnce({ data: { recent_searches: [] } });
    postSpy.mockImplementation(async (_url: string, _data: unknown) => {
      void _url;
      void _data;
      return Promise.resolve({
        data: { status: 'success', recent_searches: ['MSFT'] },
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {},
      } as unknown);
    });

    const { result } = renderHook(() => useRecentSearches());
    await waitFor(() => expect(result.current.loading).toBe(false), { timeout: 3000 });

    await act(async () => {
      await result.current.addRecent('msft');
    });

    await act(async () => {
      await new Promise((r) => setTimeout(r, 100));
    });

    expect(result.current.recent).toEqual(['MSFT']);
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
