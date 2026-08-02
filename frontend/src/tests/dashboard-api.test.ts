import { vi } from 'vitest'
import { fetchDashboardData } from '@/lib/api/dashboard'
import { apiClient } from '@/lib/api'

vi.mock('@/lib/api')

describe('Dashboard API Service', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should fetch all dashboard data components in parallel', async () => {
    // Mock all API calls
    ;(apiClient.get as any).mockImplementation((url: string) => {
      if (url.includes('market/tse-dashboard')) {
        return Promise.resolve({
          status: 'success',
          total_symbols: 1000,
          average_change_pct: 1.5,
          top_gainers: [{ symbol: 'TEST', name: 'Test', last_close: 1000, change_pct: 5 }],
          top_losers: [{ symbol: 'TEST2', name: 'Test2', last_close: 500, change_pct: -3 }],
          timestamp: '2023-01-01'
        })
      }
      if (url.includes('market/market-overview')) {
        return Promise.resolve({
          status: 'success',
          market: 'TSE',
          total_assets: 500,
          sectors: { 'Technology': 100, 'Finance': 80 },
          timestamp: '2023-01-01'
        })
      }
      if (url.includes('watchlists')) {
        return Promise.resolve([
          {
            id: '1',
            name: 'My Watchlist',
            description: 'My assets',
            is_default: true,
            items: [{ asset: { symbol: 'TEST', name: 'Test', market: 'TSE' } }]
          }
        ])
      }
      if (url.includes('latest-prices')) {
        return Promise.resolve({
          status: 'success',
          timestamp: '2023-01-01',
          data: {
            TEST: { price: 1000, change_pct: 5, volume: 50000, timestamp: '2023-01-01' }
          }
        })
      }
      if (url.includes('signals-summary')) {
        return Promise.resolve({
          status: 'success',
          timestamp: '2023-01-01',
          total_signals: 5,
          summary: { BUY: 2, SELL: 1, HOLD: 1 },
          average_confidence: { BUY: 0.8, SELL: 0.7, HOLD: 0.6 }
        })
      }
      if (url.includes('news/market')) {
        return Promise.resolve({
          status: 'success',
          count: 1,
          data: [{ title: 'Test News', source: 'Test Source', published_at: '2023-01-01T10:00:00Z' }]
        })
      }
      return Promise.reject(new Error('Unknown URL'))
    })
    
    const result = await fetchDashboardData()
    
    expect(result.live).toBe(true)
    expect(result.marketStats).toHaveLength(2)
    expect(result.topMovers).toHaveLength(2)
    expect(result.watchlist).toHaveLength(1)
    expect(result.signals).toHaveLength(5)
    expect(result.news).toHaveLength(1)
  })

  it('should set live to false when API calls fail', async () => {
    ;(apiClient.get as any).mockRejectedValue(new Error('API Error'))
    
    const result = await fetchDashboardData()
    
    expect(result.live).toBe(false)
  })
})