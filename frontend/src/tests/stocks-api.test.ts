import { vi } from 'vitest'
import {
  fetchSymbols,
  fetchAsset,
  fetchPriceHistory,
  fetchLatestPrices,
  fetchLatestPrice,
  type Asset,
  type AssetRow,
  type Candle
} from '@/lib/api/stocks'

vi.mock('@/lib/api')

describe('Stocks API Service', () => {
  const mockAssets: Asset[] = [
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

  const mockLatestPrices = {
    status: 'success',
    timestamp: '2023-01-01T12:00:00Z',
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

  const mockCandles = [{
    timestamp: '2023-01-01T00:00:00Z',
    timeframe: '1d',
    open: 100.0,
    high: 110.0,
    low: 95.0,
    close: 105.0,
    volume: 1000000,
    turnover?: number | string | null,
    transactions?: number | null
  }]

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('fetchSymbols', () => {
    it('should fetch symbols with filters', async () => {
      ;(apiClient.get as any).mockResolvedValueOnce({ data: mockAssets })
      
      const result = await fetchSymbols({ 
        assetClass: 'EQUITY',
        market: 'NASDAQ',
        sector: 'Technology',
        limit: 10
      })
      
      expect(result).toEqual(mockAssets)
    })

    it('should fetch symbols without filters', async () => {
      ;(apiClient.get as any).mockResolvedValueOnce({ data: mockAssets })
      
      const result = await fetchSymbols()
      
      expect(result).toEqual(mockAssets)
    })
  })

  describe('fetchAsset', () => {
    it('should return asset when found', async () => {
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
    it('should fetch and transform price history correctly', async () => {
      ;(apiClient.get as any).mockResolvedValueOnce({ data: mockCandles })
      
      const result = await fetchPriceHistory({ symbol: 'AAPL', timeframe: '1d', limit: 100 })
      
      expect(apiClient.get).toHaveBeenCalledWith(
        '/market/price-history?symbol=AAPL&timeframe=1d&limit=100'
      )
      
      expect(result).toHaveLength(1)
      const resultItem = result[0]
      expect(resultItem).toEqual({
        timestamp: '2023-01-01T00:00:00Z',
        timeframe: '1d',
        open: 100.0,
        high: 110.0,
        low: 95.0,
        close: 105.0,
        volume: 1000000,
        turnover: null,
        transactions: null,
      })
    })

    it('should handle null/undefined values in price history', async () => {
      const mockDataWithNulls = [{
        timestamp: '2023-01-01T00:00:00Z',
        timeframe: '1d',
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
      ;(apiClient.get as any).mockResolvedValueOnce({
        data: {
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
      })
      
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
      ;(apiClient.get as any).mockResolvedValueOnce({
        data: {
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
      })
      
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