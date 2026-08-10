"use client";

import { useEffect, useState } from 'react';
import { exportData } from '@/lib/export';
import { Asset, fetchSymbols, fetchLatestPrices, LatestPrice } from '@/lib/api/stocks';

type PriceMap = Record<string, LatestPrice>;

export function StockDashboardWidget() {
  const [symbols, setSymbols] = useState<Asset[]>([]);
  const [prices, setPrices] = useState<PriceMap>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      setError(null);
      try {
        // Fetch symbols first
        const symbolsData = await fetchSymbols({ limit: 20 });
        setSymbols(symbolsData);

        if (symbolsData.length > 0) {
          const priceData = await fetchLatestPrices(symbolsData.map((s) => s.symbol));
          setPrices(priceData || {});
        }
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : 'Failed to load dashboard data');
      } finally {
        setLoading(false);
      }
    };

    loadData();

    // Set up auto-refresh every 30 seconds for real-time updates
    const interval = window.setInterval(loadData, 30000);

    return () => {
      window.clearInterval(interval);
    };
  }, []);

  const getMarketLabel = (symbol: string): string => {
    const price = prices[symbol];
    return price ? price.symbol : 'TSE';
  };

  const getChangeColor = (changePercent: number): string => {
    return changePercent >= 0 ? 'text-green-600' : 'text-red-600';
  };

  const getChangeIcon = (changePercent: number): string => {
    return changePercent >= 0 ? '▲' : '▼';
  };

  const handleExport = (format: 'csv' | 'xlsx' | 'json') => {
    try {
      const timestamp = new Date().toISOString().toLocaleString('fa-IR', {
        timeZone: 'Asia/Tehran',
        formatStyle: 'date',
      });
      
      const filename = `stock-data-${timestamp.replace(/:/g, '-')}.${format}`;
      
      const dataToExport = symbols.map((symbol) => {
        const price = prices[symbol.symbol];
        return {
          symbol: symbol.symbol,
          name: symbol.name,
          market: symbol.market,
          price: price ? price.price : 0,
          change_pct: price ? price.change_pct : 0,
          volume: price ? price.volume : 0,
        };
      });
      
      exportData(dataToExport, {
        filename,
        format,
        includeHeaders: true,
      });
    } catch (err) {
      console.error('Export failed:', err);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold text-gray-900">Market Dashboard</h2>
        <div className="flex items-center space-x-2">
          <div className={`h-2 w-2 rounded-full ${loading ? 'bg-blue-500' : 'bg-green-500'}`} />
          <span className="text-sm text-gray-600">
            {loading ? 'Loading market data' : 'Market Live'}
          </span>
        </div>
      </div>

      {error && (
        <div className="p-3 mb-3 text-red-600 bg-red-50 border border-red-200 rounded">
          Error: {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        {symbols.map((symbol) => {
          const price = prices[symbol.symbol];
          const displayPrice = price ? price.price.toFixed(2) : '--';
          const changePct = price ? price.change_pct : 0;

          return (
            <div key={symbol.symbol} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
              <div className="flex justify-between items-start">
                <h3 className="font-semibold text-gray-900">{symbol.symbol}</h3>
                <span className={`text-sm ${getChangeColor(changePct)}`}>
                  {getChangeIcon(changePct) } {changePct.toFixed(2)}%
                </span>
              </div>
              <div className="mt-2">
                <p className="text-2xl font-bold text-gray-900">${displayPrice}</p>
                <p className={`text-sm ${getChangeColor(changePct)}`}>
                  {price ? price.change.toFixed(2) : '--'}% {getMarketLabel(symbol.symbol)}
                </p>
              </div>
              <div className="mt-3 text-xs text-gray-500">
                <p>Volume: {price ? price.volume.toLocaleString() : 'N/A'}</p>
                <p>Symbol: {symbol.symbol}</p>
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-6 flex justify-between items-center">
        <div className="text-sm text-gray-600">
          Last Update: {loading ? 'Real-time' : new Date().toLocaleTimeString('fa-IR', {
            timeZone: 'Asia/Tehran',
            hour: '2-digit',
            minute: '2-digit',
          })}
        </div>
        <div className="flex space-x-2">
          <button
            onClick={() => handleExport('csv')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm flex-1"
          >
            Export CSV
          </button>
          <button
            onClick={() => handleExport('xlsx')}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm flex-1"
          >
            Export Excel
          </button>
          <button
            onClick={() => handleExport('json')}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors text-sm flex-1"
          >
            Export JSON
          </button>
        </div>
      </div>
    </div>
  );
}