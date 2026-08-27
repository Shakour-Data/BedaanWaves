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
      if (url.includes('/market/market/market-overview')) {
        return { data: {
          status: 'success',
          market: 'NASDAQ',
          total_assets: 500,
          sectors: { 'Technology': 100, 'Finance': 80 },
          timestamp: '2023-01-01'
        }}
      }
      if (url.includes('/market/market/tse-dashboard')) {
        return { data: {
          status: 'success',
          market: 'TSE',
          total_symbols: 1000,
          average_change_pct: 1.5,
          top_gainers: [{ symbol: 'TEST', name: 'Test', last_close: 1000, change_pct: 5 }],
          top_losers: [{ symbol: 'TEST2', name: 'Test2', last_close: 500, change_pct: -3 }],
          timestamp: '2023-01-01'
        }}
      }
      if (url.includes('/watchlists/watchlists')) {
        return { data: [
          {
            id: '1',
            name: 'My Watchlist',
            description: 'My assets',
            is_default: true,
            items: [{ asset: { symbol: 'TEST', name: 'Test', market: 'TSE' } }]
          }
        ]}
      }
      if (url.includes('/market/market/latest-prices')) {
        return { data: {
          status: 'success',
          timestamp: '2023-01-01',
          data: {
            TEST: { price: 1000, change_pct: 5, volume: 50000, timestamp: '2023-01-01' }
          }
        }}
      }
      if (url.includes('/analysis/analysis/signals-summary')) {
        if (!url.includes('signal_type')) {
          return { data: {
            status: 'success',
            timestamp: '2023-01-01',
            total_signals: 5,
            summary: { BUY: 2, SELL: 1, HOLD: 1 },
            average_confidence: { BUY: 0.8, SELL: 0.7, HOLD: 0.6 }
          }}
        }
        if (url.includes('signal_type=BUY')) {
          return { data: {
            status: 'success',
            data: {
              summary: [
                { symbol: 'BUY1', signal_type: 'BUY', confidence: 85.5, model_name: 'ScoringService-6D' },
                { symbol: 'BUY2', signal_type: 'BUY', confidence: 80.0, model_name: 'ScoringService-6D' }
              ]
            }
          }}
        }
        if (url.includes('signal_type=SELL')) {
          return { data: {
            status: 'success',
            data: {
              summary: [{ symbol: 'SELL1', signal_type: 'SELL', confidence: 72.3, model_name: 'RiskAnalysisService' }]
            }
          }}
        }
        if (url.includes('signal_type=HOLD')) {
          return { data: {
            status: 'success',
            data: {
              summary: [{ symbol: 'HOLD1', signal_type: 'HOLD', confidence: 55.0, model_name: 'MomentumService' }]
            }
          }}
        }
      }
      if (url.includes('/news/news/market')) {
        return { data: {
          status: 'success',
          count: 1,
          data: [{ title: 'Test News', source: 'Test Source', published_at: '2023-01-01T10:00:00Z' }]
        }}
      }
      throw new Error('Unmatched URL')
    })

    const result = await fetchDashboardData()

    expect(result.live).toBe(true)
    expect(result.marketStats).toHaveLength(2)
    expect(result.topMovers).toHaveLength(2)
    expect(result.watchlist).toHaveLength(1)
    expect(result.signals).toHaveLength(4)
    expect(result.news).toHaveLength(1)
  })

  it('should handle API failures gracefully', async () => {
    ;(apiClient.get as any).mockImplementation((url: string) => {
      return Promise.reject(new Error('API Error'))
    })

    const result = await fetchDashboardData()

    // Functions return default/fallback values on error
    expect(Array.isArray(result.marketStats)).toBe(true)
    expect(Array.isArray(result.topMovers)).toBe(true)
    expect(Array.isArray(result.watchlist)).toBe(true)
    expect(Array.isArray(result.signals)).toBe(true)
    expect(Array.isArray(result.news)).toBe(true)
    // marketStats always returns defaults even on failure
    expect(result.live).toBe(true)
    expect(result.topMovers).toHaveLength(0)
    expect(result.watchlist).toHaveLength(0)
    expect(result.signals).toHaveLength(0)
    expect(result.news).toHaveLength(0)
  })
})