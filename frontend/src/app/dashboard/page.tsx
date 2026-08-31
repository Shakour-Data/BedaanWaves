"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { apiClient, getApiErrorMessage } from "@/lib/api";
import { cn } from "@/lib/cn";
import { fetchDashboardData, fetchGeneralDashboard, fetchTechnicalDashboard, fetchFundamentalDashboard, fetchNewsDashboard, fetchRiskDashboard, fetchBoardDashboard, fetchAiDashboard } from "@/lib/api/dashboard";
import type { AssetRow, MarketStat, SignalRow, NewsItem } from "@/lib/dashboard-data";
import type { GeneralDashboardResponse, DimensionDashboardResponse, NewsDashboardResponse, BoardDashboardResponse, AiDashboardResponse } from "@/lib/api/dashboard";
import { StockDetailSkeleton } from "@/components/ux/SkeletonLoaders";
import { useUXStore } from "@/store/useUXStore";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { SpiderChart } from "@/components/charts/SpiderChart";
import { DimensionDashboard } from "@/components/dashboard/DimensionDashboard";
import { NewsDashboard } from "@/components/dashboard/NewsDashboard";
import { BoardDashboard } from "@/components/dashboard/BoardDashboard";
import { AiDashboard } from "@/components/dashboard/AiDashboard";

type Tab = "general" | "technical" | "fundamental" | "news" | "risk" | "board" | "ai";

const tabs: { id: Tab; label: string; shortcut: string }[] = [
  { id: "general", label: "General", shortcut: "G" },
  { id: "technical", label: "Technical", shortcut: "T" },
  { id: "fundamental", label: "Fundamental", shortcut: "F" },
  { id: "news", label: "News", shortcut: "N" },
  { id: "risk", label: "Risk", shortcut: "R" },
  { id: "board", label: "Board", shortcut: "B" },
  { id: "ai", label: "AI", shortcut: "A" },
];

export default function DashboardPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<Tab>("general");
  const [generalData, setGeneralData] = useState<GeneralDashboardResponse | null>(null);
  const [marketStats, setMarketStats] = useState<MarketStat[]>([]);
  const [topStocks, setTopStocks] = useState<AssetRow[]>([]);
  const [signals, setSignals] = useState<SignalRow[]>([]);
  const [news, setNews] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const addToast = useUXStore((state) => state.addToast);

  const loadDashboard = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const [dashboardData, general] = await Promise.all([
        fetchDashboardData(),
        fetchGeneralDashboard().catch(() => null),
      ]);

      setMarketStats(dashboardData.marketStats);
      const uniqueTop = dashboardData.topMovers.reduce<AssetRow[]>((acc, stock) => {
        if (!acc.some((s) => s.symbol === stock.symbol)) acc.push(stock);
        return acc;
      }, []);
      setTopStocks(uniqueTop.slice(0, 5));
      setSignals(dashboardData.signals);
      setNews(dashboardData.news);
      setGeneralData(general);
    } catch (err) {
      const message = getApiErrorMessage(err);
      setError(message);
      addToast({ type: "error", message });
    } finally {
      setLoading(false);
    }
  }, [addToast]);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) {
        return;
      }
      const key = event.key.toLowerCase();
      const tab = tabs.find((t) => t.shortcut.toLowerCase() === key);
      if (tab) {
        setActiveTab(tab.id);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const handleDimensionClick = (label: string) => {
    const map: Record<string, Tab> = {
      Fundamental: "fundamental",
      Technical: "technical",
      Sentiment: "news",
      Risk: "risk",
      "AI": "ai",
      Macro: "general",
    };
    const target = map[label];
    if (target) {
      setActiveTab(target);
    }
  };

  const spiderData = generalData ? [
    { label: "Fundamental", value: generalData.dimensions.fundamental?.avg_score || 0 },
    { label: "Technical", value: generalData.dimensions.technical?.avg_score || 0 },
    { label: "Sentiment", value: generalData.dimensions.sentiment?.avg_score || 0 },
    { label: "Risk", value: generalData.dimensions.risk?.avg_score || 0 },
    { label: "Macro", value: generalData.dimensions.macro?.avg_score || 0 },
    { label: "AI", value: generalData.dimensions.ai?.avg_score || 0 },
  ] : [];

  if (loading) {
    return (
      <StockDetailSkeleton />
    );
  }

  if (error) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <ErrorMessage
          message={error}
          actions={[{ label: "Retry", onAction: () => { setError(null); loadDashboard(); } }]}
          moreHelpSteps={["Check your internet connection", "Verify the API service is running"]}
          helpTitle="Troubleshooting steps"
        />
      </div>
    );
  }

  const renderTabContent = () => {
    switch (activeTab) {
      case "general":
        return (
          <div className="space-y-6 animate-in fade-in duration-300">
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-[var(--color-text-primary)]">Dashboard</h1>
              <p className="mt-1 text-[var(--color-text-secondary)]">Overview of NASDAQ market performance</p>
            </div>

            <div className="mb-8 grid gap-6 md:grid-cols-4">
              {marketStats.length > 0 ? (
                marketStats.map((stat, i) => (
                  <div key={i} className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
                    <p className="text-sm font-medium text-[var(--color-text-secondary)]">{stat.label}</p>
                    <p className="mt-2 text-3xl font-bold text-[var(--color-text-primary)]">{stat.value}</p>
                  </div>
                ))
              ) : (
                <>
                  <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
                    <p className="text-sm font-medium text-[var(--color-text-secondary)]">Nasdaq Composite</p>
                    <p className="mt-2 text-3xl font-bold text-[var(--color-text-primary)]">—</p>
                  </div>
                  <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
                    <p className="text-sm font-medium text-[var(--color-text-secondary)]">Active Symbols</p>
                    <p className="mt-2 text-3xl font-bold text-[var(--color-text-primary)]">—</p>
                  </div>
                  <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
                    <p className="text-sm font-medium text-[var(--color-text-secondary)]">Top Gainer</p>
                    <p className="mt-2 text-3xl font-bold text-[var(--color-text-primary)]">—</p>
                  </div>
                  <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
                    <p className="text-sm font-medium text-[var(--color-text-secondary)]">Top Loser</p>
                    <p className="mt-2 text-3xl font-bold text-[var(--color-text-primary)]">—</p>
                  </div>
                </>
              )}
            </div>

            {generalData && spiderData.length > 0 && (
              <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
                <h2 className="text-xl font-semibold text-[var(--color-text-primary)] mb-4">6D Score Overview</h2>
                <div className="flex flex-wrap items-center gap-8">
                  <SpiderChart data={spiderData} size={280} color="#2563EB" onLabelClick={handleDimensionClick} />
                  <div className="flex-1 min-w-[200px]">
                    <div className="space-y-3">
                      {Object.entries(generalData.dimensions).map(([key, val]) => (
                        <div key={key} className="flex items-center justify-between">
                          <span className="capitalize text-sm font-medium text-[var(--color-text-secondary)]">{key}</span>
                          <div className="flex items-center gap-3">
                            <div className="h-2 w-32 rounded-full bg-[var(--color-border)] overflow-hidden">
                              <div
                                className="h-full bg-[var(--color-primary)]"
                                style={{ width: `${Math.min(val.avg_score, 100)}%` }}
                              />
                            </div>
                            <span className="text-sm font-bold text-[var(--color-text-primary)] w-12 text-right">
                              {val.avg_score.toFixed(1)}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}

            <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-xl font-semibold text-[var(--color-text-primary)]">Top NASDAQ Stocks</h2>
                <Link href="/stocks" className="text-sm font-medium text-[var(--color-primary)] hover:underline">
                  View All
                </Link>
              </div>
              <div className="space-y-2">
                {topStocks.length > 0 ? (
                  topStocks.map((stock, index) => (
                    <Link
                      key={`${stock.symbol}-${index}`}
                      href={`/stocks/${stock.symbol}`}
                      className="flex items-center gap-4 rounded-lg border border-transparent p-4 transition-all hover:border-[var(--color-border)] hover:bg-[var(--color-background)]"
                    >
                      <div className={cn(
                        "flex h-8 w-8 shrink-0 items-center justify-center rounded text-sm font-bold",
                        index === 0 ? "bg-[var(--color-warning)] text-white" :
                        index === 1 ? "bg-gray-400 text-white" :
                        index === 2 ? "bg-amber-700 text-white" :
                        "bg-gray-200 text-gray-600 dark:bg-gray-800 dark:text-gray-400"
                      )}>
                        {index + 1}
                      </div>
                      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded bg-[var(--color-primary)]/10 text-sm font-bold text-[var(--color-primary)]">
                        {stock.symbol.slice(0, 2)}
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-[var(--color-text-primary)]">{stock.symbol}</span>
                          <span className="truncate text-xs text-[var(--color-text-secondary)]">{stock.name}</span>
                        </div>
                      </div>
                      <div className="shrink-0 text-right">
                        <p className="font-semibold text-[var(--color-text-primary)]">${stock.price.toFixed(2)}</p>
                        <p className={cn("text-xs", stock.changePct >= 0 ? "text-[var(--color-success)]" : "text-[var(--color-error)]")}>
                          {stock.changePct >= 0 ? "+" : ""}{stock.changePct.toFixed(2)}%
                        </p>
                      </div>
                    </Link>
                  ))
                ) : (
                  <p className="text-center text-[var(--color-text-secondary)] py-8">No stock data available</p>
                )}
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
                <h2 className="text-xl font-semibold text-[var(--color-text-primary)] mb-4">Trading Signals</h2>
                {signals.length > 0 ? (
                  <div className="space-y-3">
                    {signals.slice(0, 5).map((signal, i) => (
                      <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-[var(--color-background)]">
                        <div className="flex items-center gap-3">
                          <span className={cn(
                            "px-2 py-1 rounded text-xs font-bold",
                            signal.type === "BUY" || signal.type === "STRONG_BUY" ? "bg-[var(--color-success)]/20 text-[var(--color-success)]" :
                            signal.type === "SELL" || signal.type === "STRONG_SELL" ? "bg-[var(--color-error)]/20 text-[var(--color-error)]" :
                            "bg-[var(--color-warning)]/20 text-[var(--color-warning)]"
                          )}>
                            {signal.type}
                          </span>
                          <span className="font-medium text-[var(--color-text-primary)]">{signal.symbol}</span>
                        </div>
                        <span className="text-sm text-[var(--color-text-secondary)]">{signal.confidence}%</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-center text-[var(--color-text-secondary)] py-8">No active signals</p>
                )}
              </div>

              <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
                <h2 className="text-xl font-semibold text-[var(--color-text-primary)] mb-4">Market News</h2>
                {news.length > 0 ? (
                  <div className="space-y-3">
                    {news.slice(0, 5).map((item, i) => (
                      <div key={i} className="p-3 rounded-lg bg-[var(--color-background)]">
                        <p className="font-medium text-[var(--color-text-primary)] text-sm">{item.title}</p>
                        <div className="flex items-center gap-2 mt-1 text-xs text-[var(--color-text-secondary)]">
                          <span>{item.source}</span>
                          <span>•</span>
                          <span>{item.time}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-center text-[var(--color-text-secondary)] py-8">No news available</p>
                )}
              </div>
            </div>
          </div>
        );

      case "technical":
        return <DimensionDashboard dimension="technical" fetchFn={fetchTechnicalDashboard} color="#2563EB" />;

      case "fundamental":
        return <DimensionDashboard dimension="fundamental" fetchFn={fetchFundamentalDashboard} color="#10B981" />;

      case "news":
        return <NewsDashboard />;

      case "risk":
        return <DimensionDashboard dimension="risk" fetchFn={fetchRiskDashboard} color="#EF4444" />;

      case "board":
        return <BoardDashboard />;

      case "ai":
        return <AiDashboard />;

      default:
        return null;
    }
  };

  return (
    <div className="space-y-6">
      <div className="mb-6">
        <div className="flex items-center gap-1 rounded-xl border border-[var(--color-border)] bg-[var(--color-background)] p-1">
          {tabs.map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  "relative flex-1 rounded-lg px-3 py-2.5 text-center text-sm font-medium transition-all",
                  isActive
                    ? "bg-[var(--color-primary)] text-white shadow-sm"
                    : "text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-border)]"
                )}
              >
                {tab.label}
              </button>
            );
          })}
        </div>
        <p className="mt-2 text-xs text-[var(--color-text-secondary)]">
          Select a dashboard above to view detailed scores and analytics. Shortcuts: G T F N R B A
        </p>
      </div>

      {renderTabContent()}
    </div>
  );
}
