/**
 * StockDashboardWidget.tsx
 * Dashboard widget that fetches tradable symbols and their latest prices
 * from the backend /api/v1/market/symbols and /api/v1/market/latest-prices endpoints.
 */

import React, { useEffect, useState } from 'react';
import { Asset, LatestPrice, fetchLatestPrices, fetchSymbols } from '@/lib/api/stocks';

export interface StockDashboardWidgetProps {
  symbolFilter?: string[];
  limit?: number;
  className?: string;
}

const StockDashboardWidget: React.FC<StockDashboardWidgetProps> = ({
  symbolFilter = [],
  limit = 50,
  className = '',
}) => {
  const [symbols, setSymbols] = useState<Asset[]>([]);
  const [latestPrices, setLatestPrices] = useState<Record<string, LatestPrice>>({});
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadSymbols = async () => {
      try {
        setLoading(true);
        setError(null);

        const assets = await fetchSymbols({ limit });
        setSymbols(assets);
      } catch (err: any) {
        setError(err.message || 'Failed to load symbols');
      } finally {
        setLoading(false);
      }
    };

    loadSymbols();
  }, [limit]);

  useEffect(() => {
    const loadPrices = async () => {
      if (!symbols.length) {
        return;
      }

      let filteredSymbols = symbols.map((s) => s.symbol);

      if (symbolFilter.length) {
        const filterUpper = symbolFilter.map((s) => s.toUpperCase());
        filteredSymbols = filteredSymbols.filter((s) =>
          filterUpper.includes(s.toUpperCase()),
        );
      }

      try {
        const prices = await fetchLatestPrices(filteredSymbols);
        setLatestPrices(prices);
      } catch (err: any) {
        console.error('Error fetching prices:', err);
      }
    };

    loadPrices();
  }, [symbols, symbolFilter]);

  const filteredRows = symbols.filter((asset) => {
    if (!symbolFilter.length) {
      return true;
    }
    const filterUpper = symbolFilter.map((s) => s.toUpperCase());
    return filterUpper.includes(asset.symbol.toUpperCase());
  });

  return (
    <div className={`bg-white rounded-lg shadow p-4 ${className}`}>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold">Market Dashboard</h2>
        {loading && (
          <div className="text-sm text-gray-500 animate-pulse">Updating...</div>
        )}
      </div>

      {error && (
        <div className="p-3 mb-3 text-sm text-red-600 bg-red-50 border border-red-200 rounded">
          Error: {error}
        </div>
      )}

      {!loading && !error && (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Symbol
                </th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Name
                </th>
                <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Price
                </th>
                <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Change
                </th>
                <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Volume
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredRows.map((asset) => {
                const price = latestPrices[asset.symbol];
                const displayPrice = price ? price.price.toFixed(2) : '--';
                const change = price ? price.change.toFixed(2) : '--';
                const changePct = price ? price.change_pct.toFixed(2) : '--';
                const isPositive = price && price.change_pct >= 0;

                return (
                  <tr key={asset.symbol} className="hover:bg-gray-50">
                    <td className="px-4 py-2 whitespace-nowrap text-sm font-medium text-gray-900">
                      {asset.symbol}
                    </td>
                    <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-500">
                      {asset.name}
                    </td>
                    <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-900 text-right">
                      {displayPrice}
                    </td>
                    <td
                      className={`px-4 py-2 whitespace-nowrap text-sm text-right font-medium ${
                        isPositive ? 'text-green-600' : 'text-red-600'
                      }`}
                    >
                      {change} ({changePct}%)
                    </td>
                    <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-500 text-right">
                      {price ? price.volume.toLocaleString() : '--'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>

          {filteredRows.length === 0 && (
            <div className="text-center py-6 text-gray-500">
              No symbols found
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default StockDashboardWidget;