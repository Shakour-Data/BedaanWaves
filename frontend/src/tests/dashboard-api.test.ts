import { vi } from 'vitest'
import { fetchDashboardData } from '@/lib/api/dashboard'
import { apiClient } from '@/lib/api'

vi.mock('@/lib/api')

describe('Dashboard API Service', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should fetch dashboard data when all APIs succeed', async () => {
    // Mock the various API endpoints
    ;(apiClient.get as any).mockImplementationOnce(
      Promise.resolve({ 
        status: 'success', 
        total_symbols: 1000, 
        average_change_pct: 1.5, 
        top_gainers: [{ symbol: 'TEST', name: 'Test', last_close: 1000, change_pct: 5 }],
        top_losers: [{ symbol: 'TEST2', name: 'Test2', last_close: 500, change_pct: -3 }],
        timestamp: '2023-01-01' 
      })
    ).mockImplementationOnce(
      Promise.resolve({ 
        status: 'success',
        market: 'TSE',
        total_assets: 500,
        sectors: { 'Technology': 100, 'Finance': 80 },
        timestamp: '2023-01-01' 
      })
    ).mockImplementationOnce(
      Promise.resolve([
        {
          id: '1',
          name: 'My Watchlist',
          description: 'My assets',
          is_default: true,
          items: [{ asset: { symbol: 'TEST', name: 'Test', market: 'TSE' } }]
        }
      ])
    ).mockImplementationOnce(
      Promise.resolve({
        status: 'success',
        timestamp: '2023-01-01',
        data: {
          TEST: { price: 1000, change_pct: 5, volume: 50000, timestamp: '2023-01-01' }
        }
      })
    ).mockImplementationOnce(
      Promise.resolve({
        status: 'success',
        timestamp: '2023-01-01',
        total_signals: 5,
        summary: { BUY: 2, SELL: 1, HOLD: 1 },
        average_confidence: { BUY: 0.8, SELL: 0.7, HOLD: 0.6 }
      })
    ).mockImplementationOnce(
      Promise.resolve({
        status: 'success',
        count: 1,
        data: [{ title: 'Test News', source: 'Test Source', published_at: '2023-01-01T10:00:00Z' }]
      })
    )
    
    const result = await fetchDashboardData()
    
    expect(result.live).toBe(true)
    expect(result.marketStats).toHaveLength(2) // Should have 2 stats
    expect(result.topMovers).toHaveLength(2) // Gainers + Losers
    expect(result.watchlist).toHaveLength(1) // One watchlist item
    expect(result.signals).toHaveLength(5) // 5 signals
    expect(result.news).toHaveLength(1) // One news item
  })

  it('should handle API failures gracefully', async () => {
    // Mock all API calls to fail
    ;(apiClient.get as any).mockRejectedValueOnce(new Error('API Error'))
      .mockRejectedValueOnce(new Error('API Error'))
      .mockRejectedValueOnce(new Error('API Error'))
      .mockRejectedValueOnce(new Error('API Error'))
      .mockRejectedValueOnce(new Error('API Error'))
      .mockRejectedValueOnce(new Error('API Error'))
    
    const result = await fetchDashboardData()
    
    // Should still return data structure but with default/fallback values
    expect(result.live).toBe(false)
    expect(Array.isArray(result.marketStats)).toBe(true)
    expect(Array.isArray(result.topMovers)).toBe(true)
    expect(Array.isArray(result.watchlist)).toBe(true)
    expect(Array.isArray(result.signals)).toBe(true)
    expect(Array.isArray(result.news)).toBe(true)
  })
})