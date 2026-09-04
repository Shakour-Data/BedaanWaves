import { vi } from 'vitest'
import {
  fetchDashboardData,
  fetchScoreTrend,
  fetchCoefficientHistory,
  fetchSubDimensionTrend,
  fetchAspectTrend,
  fetchSubAspectTrend,
  fetchHierarchicalTrend,
} from '@/lib/api/dashboard'
import { apiClient } from '@/lib/api'

vi.mock('@/lib/api', () => ({
  apiClient: {
    get: vi.fn() } }))

describe('Dashboard API Service', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should fetch dashboard data when all APIs succeed', async () => {
    vi.mocked(apiClient.get).mockImplementation((url: string) => {
      if (url.includes('market/market-overview')) {
        return Promise.resolve({ data: {
          status: 'success',
          market: 'NASDAQ',
          total_assets: 500,
          sectors: { 'Technology': 100, 'Finance': 80 },
          timestamp: '2023-01-01'
        }})
      }
      if (url.includes('analysis/dashboard/general')) {
        return Promise.resolve({ data: {
          status: 'success',
          summary: { total_symbols: 1000, total_signals: 50, total_news: 12 },
          dimensions: {
            fundamental: { avg_score: 70, count: 1000 },
            technical: { avg_score: 65, count: 1000 },
            sentiment: { avg_score: 60, count: 1000 },
            risk: { avg_score: 55, count: 1000 },
            macro: { avg_score: 60, count: 1000 },
            ai: { avg_score: 65, count: 1000 },
          },
          top_performers: [
            { symbol: 'AAPL', name: 'Apple', overall_score: 95 },
            { symbol: 'MSFT', name: 'Microsoft', overall_score: 90 },
            { symbol: 'GOOGL', name: 'Google', overall_score: 88 },
          ],
          bottom_performers: [
            { symbol: 'XYZ', name: 'XYZ Corp', overall_score: 20 },
            { symbol: 'ABC', name: 'ABC Corp', overall_score: 25 },
          ],
          symbols: [],
          coefficients: [
            { key: 'fundamental', label: 'Fundamental', weight: 0.25 },
            { key: 'technical', label: 'Technical', weight: 0.20 },
            { key: 'sentiment', label: 'Sentiment', weight: 0.15 },
            { key: 'risk', label: 'Risk', weight: 0.20 },
            { key: 'macro', label: 'Macro', weight: 0.10 },
            { key: 'ai', label: 'AI', weight: 0.10 },
          ],
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
    expect(result.topMovers.length).toBeGreaterThan(0)
    expect(result.watchlist).toHaveLength(1)
    expect(result.news).toHaveLength(1)
  })

  it('should handle API failures gracefully', async () => {
    vi.mocked(apiClient.get).mockImplementation((url: string) => {
      return Promise.reject(new Error('API Error'))
    })

    const result = await fetchDashboardData()

    expect(Array.isArray(result.marketStats)).toBe(true)
    expect(Array.isArray(result.topMovers)).toBe(true)
    expect(Array.isArray(result.watchlist)).toBe(true)
    expect(Array.isArray(result.news)).toBe(true)
    expect(result.marketStats).toHaveLength(0)
    expect(result.topMovers).toHaveLength(0)
    expect(result.watchlist).toHaveLength(0)
    expect(result.news).toHaveLength(0)
  })

  it('should fetch score trend with day-over-day deltas', async () => {
    vi.mocked(apiClient.get).mockImplementation((url: string) => {
      if (url.includes('analysis/dashboard/score-trend')) {
        return Promise.resolve({ data: {
          status: 'success',
          days: 30,
          market: 'NASDAQ',
          count: 3,
          dimensions: ['fundamental', 'technical', 'sentiment', 'risk', 'macro', 'ai'],
          series: [
            {
              date: '2026-08-01',
              avg_score: 54.76,
              avg_dimensions: { fundamental: 50, technical: 54.84, sentiment: 52, risk: 55, macro: 60, ai: 56 },
              score_change: 0,
              technical_change: 0,
              dimension_changes: { fundamental: 0, technical: 0, sentiment: 0, risk: 0, macro: 0, ai: 0 },
              symbol_count: 5600,
            },
            {
              date: '2026-08-02',
              avg_score: 55.11,
              avg_dimensions: { fundamental: 51, technical: 55.0, sentiment: 53, risk: 56, macro: 60, ai: 57 },
              score_change: 0.35,
              technical_change: 0.16,
              dimension_changes: { fundamental: 1, technical: 0.16, sentiment: 1, risk: 1, macro: 0, ai: 1 },
              symbol_count: 5600,
            },
            {
              date: '2026-08-03',
              avg_score: 55.51,
              avg_dimensions: { fundamental: 52, technical: 55.56, sentiment: 54, risk: 57, macro: 61, ai: 58 },
              score_change: 0.40,
              technical_change: 0.56,
              dimension_changes: { fundamental: 1, technical: 0.56, sentiment: 1, risk: 1, macro: 1, ai: 1 },
              symbol_count: 5600,
            },
          ],
          timestamp: '2026-08-31T22:00:00Z',
        }})
      }
      throw new Error('Unmatched URL: ' + url)
    })

    const trend = await fetchScoreTrend(30, 'NASDAQ')

    expect(trend.status).toBe('success')
    expect(trend.days).toBe(30)
    expect(trend.market).toBe('NASDAQ')
    expect(trend.series).toHaveLength(3)
    expect(trend.dimensions).toHaveLength(6)
    expect(trend.series[0].avg_score).toBe(54.76)
    expect(trend.series[1].score_change).toBeCloseTo(0.35, 2)
    expect(trend.series[2].avg_dimensions.technical).toBe(55.56)
    expect(trend.series[2].dimension_changes.technical).toBeCloseTo(0.56, 2)
  })

  it('should pin the score-trend window to the explicit end_date so the spider and trend charts can never disagree on the latest day', async () => {
    const spy = vi.fn().mockResolvedValue({
      data: {
        status: 'success',
        days: 30,
        market: 'NASDAQ',
        count: 1,
        dimensions: [],
        series: [
          {
            date: '2026-08-31',
            avg_score: 60,
            avg_dimensions: { fundamental: 0, technical: 0, sentiment: 0, risk: 0, macro: 0, ai: 0 },
            symbol_count: 5600,
          },
        ],
        latest_date: '2026-08-31',
        timestamp: '2026-08-31T22:00:00Z',
      },
    })
    ;(apiClient.get as any) = spy

    const latestDate = '2026-08-31'
    await fetchScoreTrend(30, 'NASDAQ', { endDate: latestDate })

    expect(spy).toHaveBeenCalledTimes(1)
    const calledUrl: string = spy.mock.calls[0][0]
    expect(calledUrl).toContain('analysis/dashboard/score-trend')
    expect(calledUrl).toContain(`end_date=${latestDate}`)
    expect(calledUrl).not.toContain('latest=true')
  })

  it('should fall back to latest=true when no end_date is supplied', async () => {
    const spy = vi.fn().mockResolvedValue({
      data: {
        status: 'success',
        days: 30,
        market: 'NASDAQ',
        count: 0,
        dimensions: [],
        series: [],
        latest_date: null,
        timestamp: '2026-08-31T22:00:00Z',
      },
    })
    ;(apiClient.get as any) = spy

    await fetchScoreTrend(30, 'NASDAQ', { latest: true })

    expect(spy).toHaveBeenCalledTimes(1)
    const calledUrl: string = spy.mock.calls[0][0]
    expect(calledUrl).toContain('latest=true')
  })

  it('should append every query param to the coefficient-history URL', async () => {
    const spy = vi.fn().mockResolvedValue({
      data: {
        status: 'success',
        days: 30,
        market: 'NASDAQ',
        count: 0,
        dimensions: [],
        series: [],
        latest_date: null,
        timestamp: '2026-08-31T22:00:00Z',
      },
    })
    ;(apiClient.get as any) = spy

    await fetchCoefficientHistory(30, 'NASDAQ', { endDate: '2026-08-31', latest: true })

    expect(spy).toHaveBeenCalledTimes(1)
    const calledUrl: string = spy.mock.calls[0][0]
    expect(calledUrl).toContain('analysis/dashboard/coefficient-history')
    expect(calledUrl).toContain('days=30')
    expect(calledUrl).toContain('market=NASDAQ')
    expect(calledUrl).toContain('latest=true')
    expect(calledUrl).toContain('end_date=2026-08-31')
    expect(calledUrl).not.toMatch(/\?$/)
    expect(calledUrl).not.toMatch(/\?\?/)
  })

  it('should call the sub-dimension-trend endpoint with correct params', async () => {
    const spy = vi.fn().mockResolvedValue({
      data: {
        status: 'success',
        days: 30,
        market: 'NASDAQ',
        count: 0,
        level: 'sub_dimension',
        keys: [],
        series: [],
        latest_date: null,
        timestamp: '2026-08-31T22:00:00Z',
      },
    })
    ;(apiClient.get as any) = spy

    await fetchSubDimensionTrend(30, 'NASDAQ', { endDate: '2026-08-31', latest: true })

    expect(spy).toHaveBeenCalledTimes(1)
    const calledUrl: string = spy.mock.calls[0][0]
    expect(calledUrl).toContain('analysis/dashboard/sub-dimension-trend')
    expect(calledUrl).toContain('days=30')
    expect(calledUrl).toContain('market=NASDAQ')
    expect(calledUrl).toContain('latest=true')
    expect(calledUrl).toContain('end_date=2026-08-31')
    expect(calledUrl).not.toMatch(/\?$/)
    expect(calledUrl).not.toMatch(/\?\?/)
  })

  it('should call the aspect-trend endpoint with correct params', async () => {
    const spy = vi.fn().mockResolvedValue({
      data: {
        status: 'success',
        days: 30,
        market: 'NASDAQ',
        count: 0,
        level: 'aspect',
        keys: [],
        series: [],
        latest_date: null,
        timestamp: '2026-08-31T22:00:00Z',
      },
    })
    ;(apiClient.get as any) = spy

    await fetchAspectTrend(30, 'NASDAQ', { endDate: '2026-08-31', latest: true })

    expect(spy).toHaveBeenCalledTimes(1)
    const calledUrl: string = spy.mock.calls[0][0]
    expect(calledUrl).toContain('analysis/dashboard/aspect-trend')
    expect(calledUrl).toContain('days=30')
    expect(calledUrl).toContain('market=NASDAQ')
    expect(calledUrl).toContain('latest=true')
    expect(calledUrl).toContain('end_date=2026-08-31')
    expect(calledUrl).not.toMatch(/\?$/)
    expect(calledUrl).not.toMatch(/\?\?/)
  })

  it('should call the sub-aspect-trend endpoint with correct params', async () => {
    const spy = vi.fn().mockResolvedValue({
      data: {
        status: 'success',
        days: 30,
        market: 'NASDAQ',
        count: 0,
        level: 'sub_aspect',
        keys: [],
        series: [],
        latest_date: null,
        timestamp: '2026-08-31T22:00:00Z',
      },
    })
    ;(apiClient.get as any) = spy

    await fetchSubAspectTrend(30, 'NASDAQ', { endDate: '2026-08-31', latest: true })

    expect(spy).toHaveBeenCalledTimes(1)
    const calledUrl: string = spy.mock.calls[0][0]
    expect(calledUrl).toContain('analysis/dashboard/sub-aspect-trend')
    expect(calledUrl).toContain('days=30')
    expect(calledUrl).toContain('market=NASDAQ')
    expect(calledUrl).toContain('latest=true')
    expect(calledUrl).toContain('end_date=2026-08-31')
    expect(calledUrl).not.toMatch(/\?$/)
    expect(calledUrl).not.toMatch(/\?\?/)
  })

  it('should call the hierarchical-trend endpoint with the level param', async () => {
    const spy = vi.fn().mockResolvedValue({
      data: {
        status: 'success',
        level: 'sub_dimension',
        days: 30,
        market: 'NASDAQ',
        parent: 'fundamental',
        count: 0,
        latest_date: null,
        series: [],
        timestamp: '2026-08-31T22:00:00Z',
      },
    })
    ;(apiClient.get as any) = spy

    await fetchHierarchicalTrend('sub_dimension', 30, 'NASDAQ', {
      endDate: '2026-08-31',
      latest: true,
      parent: 'fundamental',
    })

    expect(spy).toHaveBeenCalledTimes(1)
    const calledUrl: string = spy.mock.calls[0][0]
    expect(calledUrl).toContain('analysis/dashboard/hierarchical-trend')
    expect(calledUrl).toContain('level=sub_dimension')
    expect(calledUrl).toContain('days=30')
    expect(calledUrl).toContain('market=NASDAQ')
    expect(calledUrl).toContain('latest=true')
    expect(calledUrl).toContain('end_date=2026-08-31')
    expect(calledUrl).toContain('parent=fundamental')
    expect(calledUrl).not.toMatch(/\?$/)
    expect(calledUrl).not.toMatch(/\?\?/)
  })
})
