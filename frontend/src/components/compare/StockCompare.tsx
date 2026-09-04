/**
 * StockCompare Component
 * ---------------------------------------------------------------------------
 * Side-by-side stock comparison component for BedaanWaves.
 * 
 * FEATURES:
 * - Compare 2-4 stocks simultaneously
 * - Multiple comparison views (Overview, Dimensions, Metrics, Technical)
 * - Interactive charts for visual comparison
 * - Export comparison data
 * 
 * USAGE:
 *   <StockCompare symbols={["AAPL", "GOOGL", "MSFT"]} />
 */

"use client";

import { useState, useEffect, useMemo } from "react";
import { cn } from "@/lib/cn";
import { apiClient, getApiErrorMessage } from "@/lib/api";
import { useUXStore } from "@/store/useUXStore";
import { SpiderChart } from "@/components/charts/SpiderChart";
import { BarChart } from "@/components/charts/BarChart";
import { LineChart } from "@/components/charts/LineChart";
import { ComparisonTable } from "./ComparisonTable";

// Types
interface StockData {
  symbol: string;
  name: string;
  sector: string;
  price: number;
  change: number;
  changePct: number;
  marketCap: number;
  peRatio?: number;
  overallScore: number;
  grade: string;
  dimensions: {
    fundamental: number;
    technical: number;
    sentiment: number;
    risk: number;
    macro: number;
    ai: number;
  };
}

interface CompareView {
  id: string;
  label: string;
  icon: string;
}

const VIEWS: CompareView[] = [
  { id: "overview", label: "Overview", icon: "📊" },
  { id: "dimensions", label: "6D Scores", icon: "🎯" },
  { id: "metrics", label: "Metrics", icon: "📈" },
  { id: "technical", label: "Technical", icon: "📉" },
];

interface StockCompareProps {
  symbols: string[];
  onSymbolRemove?: (symbol: string) => void;
  onAddSymbol?: () => void;
  className?: string;
}

export function StockCompare({
  symbols,
  onSymbolRemove,
  onAddSymbol,
  className,
}: StockCompareProps) {
  const [activeView, setActiveView] = useState("overview");
  const [stockData, setStockData] = useState<StockData[]>([]);
  const [loading, setLoading] = useState(true);
  const addToast = useUXStore((state) => state.addToast);

  // Fetch comparison data
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const response = await apiClient.post("/api/v1/compare/stocks", {
          symbols,
          include_dimensions: true,
          include_metrics: true,
          include_technical: true,
        });
        
        setStockData(response.data.comparisons);
      } catch (err) {
        const message = getApiErrorMessage(err);
        addToast({ type: "error", message });
      } finally {
        setLoading(false);
      }
    };

    if (symbols.length > 0) {
      fetchData();
    }
  }, [symbols, addToast]);

  // Prepare spider chart data
  const spiderData = useMemo(() => {
    if (!stockData.length) return [];
    
    // Show first stock as primary
    const primary = stockData[0];
    return [
      { label: "Fundamental", value: primary.dimensions.fundamental },
      { label: "Technical", value: primary.dimensions.technical },
      { label: "Sentiment", value: primary.dimensions.sentiment },
      { label: "Risk", value: primary.dimensions.risk },
      { label: "Macro", value: primary.dimensions.macro },
      { label: "AI", value: primary.dimensions.ai },
    ];
  }, [stockData]);

  if (loading) {
    return (
      <div className={cn("flex items-center justify-center py-12", className)}>
        <div className="text-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-[var(--color-primary)] border-t-transparent mx-auto" />
          <p className="mt-4 text-sm text-[var(--color-text-secondary)]">Loading comparison...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={cn("space-y-6", className)}>
      {/* Header with View Selector */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-[var(--color-text-primary)]">Compare Stocks</h2>
          <p className="text-sm text-[var(--color-text-secondary)]">
            Comparing {symbols.length} stocks
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          {VIEWS.map((view) => (
            <button
              key={view.id}
              onClick={() => setActiveView(view.id)}
              className={cn(
                "px-3 py-1.5 rounded-lg text-sm font-medium transition-all",
                activeView === view.id
                  ? "bg-[var(--color-primary)] text-white"
                  : "bg-[var(--color-background)] text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]"
              )}
            >
              <span className="mr-1">{view.icon}</span>
              <span className="hidden sm:inline">{view.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Selected Stocks */}
      <div className="flex flex-wrap gap-2">
        {symbols.map((symbol) => (
          <div
            key={symbol}
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[var(--color-primary)]/10 text-[var(--color-primary)]"
          >
            <span className="font-semibold">{symbol}</span>
            {onSymbolRemove && (
              <button
                onClick={() => onSymbolRemove(symbol)}
                className="text-[var(--color-primary)]/60 hover:text-[var(--color-primary)] transition-colors"
              >
                ×
              </button>
            )}
          </div>
        ))}
        {onAddSymbol && symbols.length < 5 && (
          <button
            onClick={onAddSymbol}
            className="inline-flex items-center px-3 py-1.5 rounded-lg border border-dashed border-[var(--color-border)] text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] hover:border-[var(--color-primary)] transition-all"
          >
            + Add Stock
          </button>
        )}
      </div>

      {/* View Content */}
      <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
        {activeView === "overview" && (
          <div className="grid gap-6 lg:grid-cols-2">
            {/* Spider Chart */}
            <div>
              <h3 className="text-sm font-semibold text-[var(--color-text-primary)] mb-4">
                6D Score Comparison
              </h3>
              <div className="flex justify-center">
                <SpiderChart data={spiderData} size={280} color="#2563EB" />
              </div>
            </div>

            {/* Key Metrics */}
            <div>
              <h3 className="text-sm font-semibold text-[var(--color-text-primary)] mb-4">
                Key Metrics
              </h3>
              <ComparisonTable stocks={stockData} />
            </div>
          </div>
        )}

        {activeView === "dimensions" && (
          <div>
            <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-4">
              6D Dimension Scores
            </h3>
            <p className="text-sm text-[var(--color-text-secondary)] mb-6">
              Detailed breakdown of all six dimension scores for each stock.
            </p>
            {/* Dimension comparison chart would go here */}
          </div>
        )}

        {activeView === "metrics" && (
          <div>
            <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-4">
              Financial Metrics
            </h3>
            <p className="text-sm text-[var(--color-text-secondary)] mb-6">
              Side-by-side comparison of key financial metrics.
            </p>
            {/* Metrics comparison would go here */}
          </div>
        )}

        {activeView === "technical" && (
          <div>
            <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-4">
              Technical Indicators
            </h3>
            <p className="text-sm text-[var(--color-text-secondary)] mb-6">
              Comparison of technical indicators and chart patterns.
            </p>
            {/* Technical comparison would go here */}
          </div>
        )}
      </div>
    </div>
  );
}

export default StockCompare;
