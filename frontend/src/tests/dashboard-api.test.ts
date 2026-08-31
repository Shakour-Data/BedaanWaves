import { vi } from 'vitest'
import { fetchDashboardData } from '@/lib/api/dashboard'
import { apiClient } from '@/lib/api'

vi.mock('@/lib/api', () => ({
  apiClient: {
    get: vi.fn() } }))

describe('Dashboard API Service', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should fetch dashboard data when all APIs succeed', async () => {
    ;(apiClient.get as any).mockImplementation((url: string) => {
      if (url.includes('market/market-overview')) {
        return Promise.resolve({ data: {
          status: 'success',
          market: 'NASDAQ',
          total_assets: 500,
          sectors: { 'Technology': 100, 'Finance': 80 },
          timestamp: '2023-01-01'
        }})
      }
      if (url.includes('market/nasdaq-dashboard')) {
        return Promise.resolve({ data: {
          status: 'success',
          market: 'NASDAQ',
          total_symbols: 1000,
          average_change_pct: 1.5,
          top_gainers: [{ symbol: 'AAPL', name: 'Apple', last_close: 150, change_pct: 5 }],
          top_losers: [{ symbol: 'MSFT', name: 'Microsoft', last_close: 380, change_pct: -3 }],
          timestamp: '2023-01-01'
        }})
      }
      if (url.includes('watchlists')) {
        return Promise.resolve({ data: [
          {
            id: '1',
            name: 'My Watchlist',
            description: 'My assets',
            is_default: true,
            items: [{ asset: { symbol: 'AAPL', name: 'Apple', market: 'NASDAQ' } }]
          }
        ]})
      }
      if (url.includes('market/latest-prices')) {
        return Promise.resolve({ data: {
          status: 'success',
          timestamp: '2023-01-01',
          data: {
            AAPL: { price: 150, change_pct: 5, volume: 50000, timestamp: '2023-01-01' }
          }
        }})
      }
      if (url.includes('analysis/signals-summary')) {
        if (!url.includes('signal_type')) {
          return Promise.resolve({ data: {
            status: 'success',
            timestamp: '2023-01-01',
            total_signals: 5,
            summary: { BUY: 2, SELL: 1, HOLD: 1 },
            average_confidence: { BUY: 0.8, SELL: 0.7, HOLD: 0.6 }
          }})
        }
      }
      if (url.includes('analysis/signals')) {
        return Promise.resolve({ data: {
          status: 'success',
          timestamp: '2023-01-01',
          data: [
            { symbol: 'AAPL', name: 'Apple', signal_type: 'BUY', confidence: 0.8, model: 'ML', generated_at: '2023-01-01' },
            { symbol: 'MSFT', name: 'Microsoft', signal_type: 'SELL', confidence: 0.7, model: 'ML', generated_at: '2023-01-01' },
            { symbol: 'GOOGL', name: 'Google', signal_type: 'HOLD', confidence: 0.6, model: 'ML', generated_at: '2023-01-01' },
          ]
        }})
      }
      if (url.includes('news/market')) {
        return Promise.resolve({ data: {
          status: 'success',
          count: 1,
          data: [{ title: 'Test News', source: 'Test Source', published_at: '2023-01-01T10:00:00Z' }]
        }})
      }
      throw new Error('Unmatched URL: ' + url)
    })

    const result = await fetchDashboardData()

    expect(result.live).toBe(true)
    expect(result.marketStats).toHaveLength(3)
    expect(result.topMovers).toHaveLength(2)
    expect(result.watchlist).toHaveLength(1)
    expect(result.signals).toHaveLength(3)
    expect(result.news).toHaveLength(1)
  })

  it('should handle API failures gracefully', async () => {
    ;(apiClient.get as any).mockImplementation((url: string) => {
      return Promise.reject(new Error('API Error'))
    })

    const result = await fetchDashboardData()

    expect(Array.isArray(result.marketStats)).toBe(true)
    expect(Array.isArray(result.topMovers)).toBe(true)
    expect(Array.isArray(result.watchlist)).toBe(true)
    expect(Array.isArray(result.signals)).toBe(true)
    expect(Array.isArray(result.news)).toBe(true)
    expect(result.marketStats).toHaveLength(0)
    expect(result.topMovers).toHaveLength(0)
    expect(result.watchlist).toHaveLength(0)
    expect(result.signals).toHaveLength(0)
    expect(result.news).toHaveLength(0)
  })
})