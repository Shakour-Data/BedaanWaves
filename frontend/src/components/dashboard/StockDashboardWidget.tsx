"use client';

import { useSSELatest } from '@/hooks/useSSE';
import { exportData } from '@/lib/export';
import { buildGraphQLQuery, executeGraphQLQuery } from '@/lib/graphql';

interface StockData {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  marketCap: number;
}

export function StockDashboardWidget() {
  const realTimePrice = useSSELatest<StockData>('stock_dashboard', '/stocks/events', {
    onMessage: (event) => {
      console.log('Real-time stock update:', event.data);
    },
  });

  const sampleData = [
    { symbol: 'AAPL', price: 150.25, change: 1.5, changePercent: 1.0, volume: 1000000, marketCap: 2300000000000 },
    { symbol: 'GOOGL', price: 2800.75, change: -12.3, changePercent: -0.44, volume: 800000, marketCap: 1800000000000 },
    { symbol: 'MSFT', price: 320.50, change: 8.2, changePercent: 2.62, volume: 1500000, marketCap: 2400000000000 },
    { symbol: 'AMZN', price: 145.30, change: -2.1, changePercent: -1.43, volume: 900000, marketCap: 1500000000000 },
    { symbol: 'TSLA', price: 245.80, change: 15.3, changePercent: 6.26, volume: 2000000, marketCap: 700000000000 },
  ];

  const handleExport = () => {
    exportData(sampleData, {
      filename: `stock-data-${Date.now()}`, 
      format: 'csv',
      includeHeaders: true,
    });
  };

  const handleExportExcel = () => {
    exportData(sampleData, {
      filename: `stock-data-${Date.now()}`, 
      format: 'xlsx',
      includeHeaders: true,
    });
  };

  const handleExportJSON = () => {
    exportData(sampleData, {
      filename: `stock-data-${Date.now()}`, 
      format: 'json',
      includeHeaders: true,
    });
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold text-gray-900">Live Stock Dashboard</h2>
        <div className="flex items-center space-x-2">
          <div className={`h-2 w-2 rounded-full ${realTimePrice ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className="text-sm text-gray-600">
            {realTimePrice ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        {sampleData.map((stock) => (
          <div key={stock.symbol} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
            <div className="flex justify-between items-start">
              <h3 className="font-semibold text-gray-900">{stock.symbol}</h3>
              <span className={`text-sm ${stock.change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {stock.change >= 0 ? '+' : ''}{stock.change.toFixed(2)}
              </span>
            </div>
            <div className="mt-2">
              <p className="text-2xl font-bold text-gray-900">
                ${stock.price.toFixed(2)}
              </p>
              <p className={`text-sm ${stock.changePercent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {stock.changePercent >= 0 ? '+' : ''}{stock.changePercent.toFixed(2)}%
              </p>
            </div>
            <div className="mt-3 text-xs text-gray-500">
              <p>Volume: {stock.volume.toLocaleString()}</p>
              <p>Market Cap: ${(stock.marketCap / 1e9).toFixed(1)}B</p>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-6 flex justify-between items-center">
        <div className="text-sm text-gray-600">
          Last Update: {realTimePrice ? new Date().toLocaleTimeString() : 'No data'}
        </div>
        <div className="flex space-x-2">
          <button
            onClick={handleExport}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
          >
            Export CSV
          </button>
          <button
            onClick={handleExportExcel}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm"
          >
            Export Excel
          </button>
          <button
            onClick={handleExportJSON}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors text-sm"
          >
            Export JSON
          </button>
        </div>
      </div>
    </div>
  );
}