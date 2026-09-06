import { vi } from 'vitest';
import {
  fetchWatchlists,
  createWatchlist,
  updateWatchlist,
  deleteWatchlist,
  addWatchlistItem,
  removeWatchlistItem,
} from '@/lib/api/watchlist';
import { apiClient } from '@/lib/api';

vi.mock('@/lib/api', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

const mockedApiClient = apiClient as unknown as {
  get: ReturnType<typeof vi.fn>;
  post: ReturnType<typeof vi.fn>;
  put: ReturnType<typeof vi.fn>;
  delete: ReturnType<typeof vi.fn>;
};

describe('watchlist API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should fetch watchlists', async () => {
    mockedApiClient.get.mockResolvedValue({
      data: [{ id: '1', name: 'My List', items: [] }],
    });

    const result = await fetchWatchlists();

    expect(mockedApiClient.get).toHaveBeenCalledWith('/watchlists');
    expect(result).toHaveLength(1);
    expect(result[0].name).toBe('My List');
  });

  it('should create a watchlist', async () => {
    mockedApiClient.post.mockResolvedValue({
      data: { id: '1', name: 'New List', description: null, is_default: false, items: [] },
    });

    const result = await createWatchlist({ name: 'New List' });

    expect(mockedApiClient.post).toHaveBeenCalledWith('/watchlists', { name: 'New List' });
    expect(result.name).toBe('New List');
  });

  it('should update a watchlist', async () => {
    mockedApiClient.put.mockResolvedValue({
      data: { id: '1', name: 'Updated', description: null, is_default: false, items: [] },
    });

    const result = await updateWatchlist('1', { name: 'Updated' });

    expect(mockedApiClient.put).toHaveBeenCalledWith('/watchlists/1', { name: 'Updated' });
    expect(result.name).toBe('Updated');
  });

  it('should delete a watchlist', async () => {
    mockedApiClient.delete.mockResolvedValue({});

    await deleteWatchlist('1');

    expect(mockedApiClient.delete).toHaveBeenCalledWith('/watchlists/1');
  });

  it('should add an item to a watchlist', async () => {
    mockedApiClient.post.mockResolvedValue({
      data: { id: 'item-1', watchlist_id: '1', asset_id: 'asset-1', note: null, alert_threshold_pct: null },
    });

    const result = await addWatchlistItem('1', { asset_id: 'asset-1' });

    expect(mockedApiClient.post).toHaveBeenCalledWith('/watchlists/1/items', { asset_id: 'asset-1' });
    expect(result.id).toBe('item-1');
  });

  it('should remove an item from a watchlist', async () => {
    mockedApiClient.delete.mockResolvedValue({});

    await removeWatchlistItem('1', 'item-1');

    expect(mockedApiClient.delete).toHaveBeenCalledWith('/watchlists/1/items/item-1');
  });
});
