"use client";

import { useEffect, useState } from 'react';
import { exportData } from '@/lib/export';
import { Asset, fetchSymbols, fetchLatestPrices, LatestPrice } from '@/lib/api/stocks';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { ChangeBadge } from './StatCard';
import { Spinner } from '@/components/ui/Spinner';
import { cn } from '@/lib/cn';

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
        const symbolsData = await fetchSymbols({ limit: 10 });
        setSymbols(symbolsData);

        if (symbolsData.length > 0) {
          const priceData = await fetchLatestPrices(symbolsData.map((s) => s.symbol));
          setPrices(priceData || {});
        }
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : 'خطا در بارگذاری داده‌ها');
      } finally {
        setLoading(false);
      }
    };

    loadData();
    const interval = window.setInterval(loadData, 30000);
    return () => window.clearInterval(interval);
  }, []);

  const handleExport = (format: 'csv' | 'xlsx' | 'json') => {
    try {
      const timestamp = new Date().toISOString();
      const filename = `stock-data-${timestamp}.${format}`;
      
      const dataToExport = symbols.map((symbol) => {
        const price = prices[symbol.symbol];
        return {
          symbol: symbol.symbol,
          name: symbol.name,
          market: symbol.market,
          price: price ? price.price : 0,
          change_pct: price ? price.change_pct : 0,
          volume: price ? price.volume : 0 };
      });
      
      exportData(dataToExport, { filename, format, includeHeaders: true });
    } catch (err) {
      // Handle error
    }
  };

  return (
    <Card
      title="داشبورد بازار"
      subtitle={loading && symbols.length === 0 ? 'در حال دریافت داده‌ها...' : loading ? 'در حال به‌روزرسانی...' : 'بازار زنده'}
      footer={
        <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
          <div className="text-xs text-muted-foreground">
            آخرین به‌روزرسانی: {new Date().toLocaleTimeString('fa-IR')}
          </div>
          <div className="flex gap-2 w-full sm:w-auto">
            <Button 
              onClick={() => handleExport('csv')} 
              variant="outline" 
              size="sm" 
              className="flex-1"
              disabled={symbols.length === 0}
            >
              CSV
            </Button>
            <Button 
              onClick={() => handleExport('xlsx')} 
              variant="outline" 
              size="sm" 
              className="flex-1"
              disabled={symbols.length === 0}
            >
              Excel
            </Button>
            <Button 
              onClick={() => handleExport('json')} 
              variant="outline" 
              size="sm" 
              className="flex-1"
              disabled={symbols.length === 0}
            >
              JSON
            </Button>
          </div>
        </div>
      }
    >
      {error && (
        <div className="mb-4 p-4 rounded-xl border border-error/20 bg-error/5 text-error text-sm">
          خطا: {error}
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {loading && symbols.length === 0
          ? Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="rounded-xl border border-border p-4 space-y-4">
                <Spinner className="mx-auto" />
              </div>
            ))
          : symbols.map((symbol) => {
              const price = prices[symbol.symbol];
              const displayPrice = price ? price.price.toLocaleString("fa-IR") : '--';
              const changePct = price ? price.change_pct : 0;

              return (
                <Card key={symbol.symbol} title={symbol.symbol} className="hover:border-primary/20 transition-all duration-300">
                  <div className="mt-2">
                    <p className="text-2xl font-bold text-foreground">{displayPrice}</p>
                    <div className="mt-2 flex items-center justify-between">
                       <ChangeBadge value={changePct} />
                       <span className="text-xs text-muted-foreground">{symbol.market}</span>
                    </div>
                  </div>
                  <div className="mt-4 pt-3 border-t border-border/60 text-[10px] text-muted-foreground space-y-1">
                    <p>حجم: {price ? price.volume.toLocaleString("fa-IR") : 'نامشخص'}</p>
                    <p>نام: {symbol.name}</p>
                  </div>
                </Card>
              );
            })}
      </div>
    </Card>
  );
}
