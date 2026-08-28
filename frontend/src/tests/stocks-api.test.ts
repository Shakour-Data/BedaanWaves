import { vi } from 'vitest'
import { fetchSymbols, fetchAsset, fetchPriceHistory, fetchLatestPrices, fetchLatestPrice } from '@/lib/api/stocks'
import { apiClient } from '@/lib/api'

vi.mock('@/lib/api')

describe('Stocks API Service', () => {
  const mockAssets = [
    {
      id: '1',
      symbol: 'AAPL',
      name: 'Apple Inc.',
      asset_class: 'EQUITY',
      market: 'NASDAQ',
      sector: 'Technology',
      sub_sector: 'Consumer Electronics',
      country_code: 'US',
      currency: 'USD',
      active: true,
      created_at: '2023-01-01T00:00:00Z',
      updated_at: '2023-01-01T00:00:00Z'
    },
    {
      id: '2',
      symbol: 'GOOGL',
      name: 'Alphabet Inc.',
      asset_class: 'EQUITY',
      market: 'NASDAQ',
      sector: 'Technology',
      sub_sector: 'Internet Content & Information',
      country_code: 'US',
      currency: 'USD',
      active: true,
      created_at: '2023-01-01T00:00:00Z',
      updated_at: '2023-01-01T00:00:00Z'
    }
  ]

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('fetchSymbols', () => {
    it('should return mock assets when called', async () => {
      ;(apiClient.get as any).mockResolvedValueOnce({ data: mockAssets })
      
      const result = await fetchSymbols({ 
        assetClass: 'EQUITY',
        market: 'NASDAQ',
        sector: 'Technology',
        limit: 10
      })
      
      expect(result).toEqual(mockAssets)
      expect(apiClient.get).toHaveBeenCalled()
    })

    it('should fetch symbols without filters', async () => {
      ;(apiClient.get as any).mockResolvedValueOnce({ data: mockAssets })
      
      const result = await fetchSymbols()
      
      expect(result).toEqual(mockAssets)
    })
  })

  describe('fetchAsset', () => {
    it('should find asset when it exists', async () => {
      ;(apiClient.get as any).mockResolvedValueOnce({ data: mockAssets })
      
      const result = await fetchAsset('AAPL')
      
      expect(result?.symbol).toBe('AAPL')
    })

    it('should return null when asset not found', async () => {
      ;(apiClient.get as any).mockResolvedValueOnce({ data: mockAssets })
      
      const result = await fetchAsset('INVALID')
      
      expect(result).toBeNull()
    })
  })

  describe('fetchPriceHistory', () => {
    it('should transform raw candles to Candle array', async () => {
      const mockRawCandles = [{
        timestamp: '2023-01-01T00:00:00Z',
        timeframe: '1d' as const,
        open: 100.0,
        high: 110.0,
        low: 95.0,
        close: 105.0,
        volume: 1000000,
        turnover: 10500000,
        transactions: 1500
      }]

      ;(apiClient.get as any).mockResolvedValueOnce({ data: mockRawCandles })
      
      const result = await fetchPriceHistory({ symbol: 'AAPL', timeframe: '1d', limit: 100 })
      
      expect(apiClient.get).toHaveBeenCalledWith(
        'market/price-history?symbol=AAPL&timeframe=1d&limit=100'
      )
      
      expect(result).toHaveLength(1)
      expect(result[0]).toEqual({
        timestamp: '2023-01-01T00:00:00Z',
        timeframe: '1d',
        open: 100.0,
        high: 110.0,
        low: 95.0,
        close: 105.0,
        volume: 1000000,
        turnover: 10500000,
        transactions: 1500
      })
    })

    it('should handle null/undefined values in price history', async () => {
      const mockDataWithNulls = [{
        timestamp: '2023-01-01T00:00:00Z',
        timeframe: '1d' as const,
        open: null,
        high: '110.0',
        low: 95,
        close: undefined,
        volume: '0',
        turnover: null,
        transactions: null
      }]

      ;(apiClient.get as any).mockResolvedValueOnce({ data: mockDataWithNulls })
      
      const result = await fetchPriceHistory({ symbol: 'TEST' })
      
      expect(result[0]).toEqual({
        timestamp: '2023-01-01T00:00:00Z',
        timeframe: '1d',
        open: 0,
        high: 110.0,
        low: 95.0,
        close: 0,
        volume: 0,
        turnover: null,
        transactions: null
      })
    })
  })

  describe('fetchLatestPrices', () => {
    it('should fetch latest prices for multiple symbols', async () => {
      const mockResponse = {
        status: 'success',
        timestamp: '2023-01-01',
        data: {
          AAPL: {
            price: 150.25,
            change: 2.50,
            change_pct: 1.69,
            volume: 50000000,
            timestamp: '2023-01-01T12:00:00Z'
          },
          GOOGL: {
            price: 2800.75,
            change: -15.25,
            change_pct: -0.54,
            volume: 1500000,
            timestamp: '2023-01-01T12:00:00Z'
          }
        }
      }
      
      ;(apiClient.get as any).mockResolvedValueOnce({ data: mockResponse })
      
      const result = await fetchLatestPrices(['AAPL', 'GOOGL'])
      
      expect(Object.keys(result)).toEqual(['AAPL', 'GOOGL'])
      expect(result.AAPL).toEqual({
        symbol: 'AAPL',
        price: 150.25,
        change: 2.50,
        change_pct: 1.69,
        volume: 50000000,
        timestamp: '2023-01-01T12:00:00Z'
      })
      expect(result.GOOGL).toEqual({
        symbol: 'GOOGL',
        price: 2800.75,
        change: -15.25,
        change_pct: -0.54,
        volume: 1500000,
        timestamp: '2023-01-01T12:00:00Z'
      })
    })

    it('should return empty object for empty symbols array', async () => {
      const result = await fetchLatestPrices([])
      
      expect(result).toEqual({})
      expect(vi.spyOn(apiClient, 'get')).not.toHaveBeenCalled()
    })
  })

  describe('fetchLatestPrice', () => {
    it('should fetch latest price for single symbol', async () => {
      const mockResponse = {
        status: 'success',
        timestamp: '2023-01-01',
        data: {
          AAPL: {
            price: 150.25,
            change: 2.50,
            change_pct: 1.69,
            volume: 50000000,
            timestamp: '2023-01-01T12:00:00Z'
          }
        }
      }
      
      ;(apiClient.get as any).mockResolvedValueOnce({ data: mockResponse })
      
      const result = await fetchLatestPrice('AAPL')
      
      expect(result).toEqual({
        symbol: 'AAPL',
        price: 150.25,
        change: 2.50,
        change_pct: 1.69,
        volume: 50000000,
        timestamp: '2023-01-01T12:00:00Z'
      })
    })

    it('should return null when symbol not found', async () => {
      ;(apiClient.get as any).mockResolvedValueOnce({ 
        data: { status: 'success', timestamp: '', data: {} } 
      })
      
      const result = await fetchLatestPrice('INVALID')
      
      expect(result).toBeNull()
    })
  })
})