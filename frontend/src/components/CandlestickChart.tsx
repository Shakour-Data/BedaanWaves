/**
 * CandlestickChart.tsx
 * ---------------------------------------------------------------------------
 * Fetches OHLCV candle data from the backend `/api/v1/market/price-history`
 * endpoint and renders it as a lightweight SVG candlestick chart.
 */

import React, { useEffect, useRef, useState } from 'react';
import { fetchPriceHistory, Candle, FetchPriceHistoryParams } from '@/lib/api/stocks';

export interface CandlestickChartProps extends FetchPriceHistoryParams {
  width?: number;
  height?: number;
}

const CandlestickChart: React.FC<CandlestickChartProps> = ({
  symbol,
  timeframe = '1d',
  limit = 100,
  width = 800,
  height = 400,
}) => {
  const [data, setData] = useState<Candle[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const candles = await fetchPriceHistory({ symbol, timeframe, limit });
        setData(candles);
      } catch (err: any) {
        setError(err.message || 'Failed to load chart data');
      } finally {
        setLoading(false);
      }
    };

    if (symbol) {
      fetchData();
    }
  }, [symbol, timeframe, limit]);

  const padding = { top: 20, right: 30, bottom: 30, left: 60 };
  const innerWidth = width - padding.left - padding.right;
  const innerHeight = height - padding.top - padding.bottom;

  const renderChart = () => {
    if (!data.length) return null;

    const maxHigh = Math.max(...data.map((c) => c.high));
    const minPrice = Math.min(...data.map((c) => c.low));
    const maxPrice = maxHigh;
    const priceRange = maxPrice - minPrice || 1;

    const xScale = (i: number) => (i / (data.length - 1)) * innerWidth;
    const yScale = (price: number) =>
      innerHeight - ((price - minPrice) / priceRange) * innerHeight;

    const candleWidth = Math.max(2, innerWidth / data.length / 2);

    return (
      <svg width={width} height={height} className="w-full h-auto">
        <g transform={`translate(${padding.left}, ${padding.top})`}>
          {/* Y-axis gridlines */}
          {[0, 0.25, 0.5, 0.75, 1].map((t) => {
            const price = minPrice + t * priceRange;
            return (
              <g key={`grid-y-${t}`}>
                <line
                  x1={0}
                  y1={yScale(price)}
                  x2={innerWidth}
                  y2={yScale(price)}
                  stroke="#eee"
                  strokeWidth={1}
                />
                <text
                  x={-10}
                  y={yScale(price)}
                  fontSize={10}
                  textAnchor="end"
                  dominantBaseline="middle"
                >
                  {price.toFixed(2)}
                </text>
              </g>
            );
          })}

          {/* Candles */}
          {data.map((candle, i) => {
            const x = xScale(i);
            const openY = yScale(candle.open);
            const closeY = yScale(candle.close);
            const highY = yScale(candle.high);
            const lowY = yScale(candle.low);
            const isBullish = candle.close > candle.open;
            const color = isBullish ? '#4ade80' : '#f87171';

            return (
              <g key={`candle-${i}`} transform={`translate(${x}, 0)`}>
                <line
                  x1={candleWidth}
                  y1={highY}
                  x2={candleWidth}
                  y2={lowY}
                  stroke={color}
                  strokeWidth={1}
                />
                <rect
                  x={0}
                  y={Math.min(openY, closeY)}
                  width={candleWidth * 2}
                  height={Math.abs(closeY - openY)}
                  fill={color}
                  opacity={0.7}
                  stroke={color}
                />
                <text
                  x={candleWidth}
                  y={innerHeight + 15}
                  fontSize={8}
                  textAnchor="middle"
                  fill="#666"
                >
                  {new Date(candle.timestamp).toLocaleTimeString([], {
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </text>
              </g>
            );
          })}
        </g>
      </svg>
    );
  };

  return (
    <div className="relative w-full max-w-4xl mx-auto">
      <h3 className="text-sm font-medium mb-2">{symbol} price chart ({timeframe})</h3>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
          <span className="ml-2">Loading chart data...</span>
        </div>
      ) : error ? (
        <div className="p-4 text-red-500 bg-red-50 border border-red-200 rounded">
          Error: {error}
        </div>
      ) : data.length > 0 ? (
        renderChart()
      ) : (
        <div className="text-center py-8 text-gray-500">No data available</div>
      )}
    </div>
  );
};

export default CandlestickChart;
