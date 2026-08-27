"use client";

import { DashboardShell } from "@/components/layout/DashboardShell";
import { TarotCard } from "@/components/ui/TarotCard";
import { SignalList } from "@/components/dashboard/SignalList";
import { AssetTable } from "@/components/dashboard/AssetTable";
import { AreaChart } from "@/components/charts/AreaChart";
import { SpiderChart } from "@/components/charts/SpiderChart";
import { BarChart } from "@/components/charts/BarChart";
import { StatCard } from "@/components/dashboard/StatCard";
import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api";
import type { AssetRow, SignalRow } from "@/lib/dashboard-data";

const analysisTabs = [
  { id: "technical", label: "تحلیل تکنیکال", icon: "" },
  { id: "fundamental", label: "تحلیل بنیادی", icon: "" },
  { id: "scoring", label: "بررسی ۶ بعدی", icon: "" },
  { id: "sentiment", label: "احساسات بازار", icon: "️‍️" },
];

export default function AnalysisPage() {
  const [activeTab, setActiveTab] = useState("technical");
  const [topSignals, setTopSignals] = useState<SignalRow[]>([]);
  const [topMovers, setTopMovers] = useState<AssetRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [fundamentalData, setFundamentalData] = useState<Record<string, number> | null>(null);
  const [scoringData, setScoringData] = useState<any>(null);
  const [sentimentData, setSentimentData] = useState<{ news: number; social: number; crypto: number } | null>(null);
  const [marketStats, setMarketStats] = useState<Array<{ label: string; value: string; changePct?: number }>>([]);

  useEffect(() => {
    let active = true;

    async function loadAnalysisData() {
      setLoading(true);
      setError(null);
      setTopSignals([]);
      setTopMovers([]);

      try {
        const [summaryRes, performersRes, symbolsRes, statsRes] = await Promise.all([
          apiClient.get<{ status: string; data: any; summary: Record<string, number> }>("/analysis/signals-summary?min_confidence=0.6").catch(() => ({ data: { status: "error" } })),
          apiClient.get<{ status: string; data: any[] }>("/analysis/top-performers?limit=10&timeframe=1d&market=NASDAQ").catch(() => ({ data: { status: "error", data: [] } })),
          apiClient.get<{ symbol: string; name: string; market: string }[]>("/market/symbols?market=NASDAQ&limit=50").catch(() => ({ data: [] })),
          apiClient.get<any>("/market/market-overview?market=NASDAQ").catch(() => ({ data: null })),
        ]);

        if (!active) return;

        // Build signal list from top performers
        if (performersRes.data?.status === "success") {
          const topPerformerSymbols = (performersRes.data.data ?? [])
            .sort((a: any, b: any) => Math.abs(b.change_percent) - Math.abs(a.change_percent))
            .slice(0, 5);

          const signals: SignalRow[] = [];
          for (const performer of topPerformerSymbols) {
            try {
              const signalRes = await apiClient.get<{ status: string; data: any }>(
                `/analysis/signals/${encodeURIComponent(performer.symbol)}`
              );
              if (signalRes.data?.status === "success") {
                signals.push({
                  symbol: performer.symbol,
                  type: signalRes.data.data.signal_type || "HOLD",
                  confidence: signalRes.data.data.confidence ?? 50,
                  model: signalRes.data.data.model_name || "ML",
                });
              }
            } catch {}
          }
          setTopSignals(signals);
        }

        // Build top movers
        if (performersRes.data?.status === "success" && symbolsRes.data.length > 0) {
          const symbolMap = new Map(symbolsRes.data.map((s) => [s.symbol, s.name]));
          const movers: AssetRow[] = (performersRes.data.data ?? [])
            .map((p: any) => ({
              symbol: p.symbol,
              name: symbolMap.get(p.symbol) || p.name || "",
              market: (p.market === "NASDAQ" || p.market === "NYSE" ? "NASDAQ" :
                      p.market === "BINANCE" || p.market === "KRAKEN" ? "BINANCE" : "TSE") as AssetRow["market"],
              price: p.current_price ?? p.price ?? 0,
              changePct: p.change_percent ?? p.change_pct ?? 0,
            }))
            .sort((a: AssetRow, b: AssetRow) => Math.abs(b.changePct) - Math.abs(a.changePct));

          setTopMovers(movers.slice(0, 5));

          // Fetch fundamental data for top mover
          if (movers.length > 0) {
            try {
              const fundamentalRes = await apiClient.get<any>(`/analysis/fundamental/${encodeURIComponent(movers[0].symbol)}`);
              if (fundamentalRes.data?.status === "success") {
                setFundamentalData(fundamentalRes.data.fundamental?.metrics || null);
              }
            } catch {}
          }

          // Fetch scoring data
          try {
            const scoringRes = await apiClient.post<any>("/analysis/scoring", {
              ticker: movers[0]?.symbol || "AAPL",
              market: "NASDAQ"
            });
            if (scoringRes.data?.status === "success") {
              setScoringData(scoringRes.data.scoring);
            }
          } catch {}
        }

        // Fetch sentiment data from news
        try {
          const newsRes = await apiClient.get<any>("/news/market?limit=50");
          if (newsRes.data?.status === "success") {
            const newsItems = newsRes.data.data || [];
            const positiveCount = newsItems.filter((n: any) => n.sentiment === "positive").length;
            const negativeCount = newsItems.filter((n: any) => n.sentiment === "negative").length;
            const neutralCount = newsItems.length - positiveCount - negativeCount;
            const positivePct = newsItems.length > 0 ? (positiveCount / newsItems.length) * 100 : 33;
            const negativePct = newsItems.length > 0 ? (negativeCount / newsItems.length) * 100 : 33;
            const neutralPct = 100 - positivePct - negativePct;
            setSentimentData({
              news: Math.round(positivePct),
              social: Math.round(neutralPct),
              crypto: Math.round(negativePct)
            });
          }
        } catch {}

        // Market stats
        if (statsRes.data) {
          const stats: Array<{ label: string; value: string; changePct?: number }> = [];
          if (statsRes.data.total_assets) {
            stats.push({ label: "نمادهای فعال", value: statsRes.data.total_assets.toLocaleString("fa-IR"), changePct: 0 });
          }
          if (statsRes.data.sectors && Object.keys(statsRes.data.sectors).length > 0) {
            const topSector = Object.entries(statsRes.data.sectors).sort((a, b) => (b[1] as number) - (a[1] as number))[0];
            stats.push({ label: "بازده برتر صنعت", value: topSector ? topSector[0] : "—", changePct: topSector ? Number(topSector[1]) : 0 });
          }
          setMarketStats(stats.length > 0 ? stats : [{ label: "نمادهای فعال", value: "—", changePct: 0 }]);
        }
      } catch (error) {
        if (active) setError("خطا در بارگذاری داده‌های تحلیل. لطفاً دوباره تلاش کنید.");
      } finally {
        if (active) setLoading(false);
      }
    }

    loadAnalysisData();
    return () => { active = false; };
  }, []);

  if (loading) {
    return (
      <DashboardShell title="تحلیل">
        <div className="flex min-h-[40vh] items-center justify-center text-muted-foreground">
          در حال بارگذاری تحلیل...
        </div>
      </DashboardShell>
    );
  }

  if (error) {
    return (
      <DashboardShell title="تحلیل">
        <TarotCard title="خطا" className="max-w-md mx-auto">
          <p className="text-sm text-muted-foreground">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 rounded-xl bg-secondary text-secondary-foreground hover:bg-secondary/80 transition"
          >
            تلاش مجدد
          </button>
        </TarotCard>
      </DashboardShell>
    );
  }

  return (
    <DashboardShell title="تحلیل">
      <div className="flex flex-col gap-6">
        {/* Market Stats */}
        {marketStats.length > 0 && (
          <section className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            {marketStats.map((s, i) => (
              <StatCard key={i} stat={s} />
            ))}
          </section>
        )}

        {/* Analysis Tabs */}
        <div className="flex gap-2 overflow-x-auto pb-2">
          {analysisTabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-colors whitespace-nowrap ${
                activeTab === tab.id
                  ? "bg-secondary text-secondary-foreground"
                  : "bg-muted text-muted-foreground hover:bg-muted/80"
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>

        {/* Signal Analysis */}
        <TarotCard title="سیگنال‌های برتر">
          {topSignals.length > 0 ? (
            <SignalList signals={topSignals} />
          ) : (
            <p className="text-muted-foreground py-4">سیگنالی در دسترس نیست</p>
          )}
        </TarotCard>

        {/* Top Movers */}
        <TarotCard title="نمادهای پرتغول">
          {topMovers.length > 0 ? (
            <AssetTable rows={topMovers} />
          ) : (
            <p className="text-muted-foreground py-4">داده‌ای در دسترس نیست</p>
          )}
        </TarotCard>

        {/* Active Analysis Tab Content */}
        <TarotCard title={analysisTabs.find((t) => t.id === activeTab)?.label || "تحلیل"}>
          {activeTab === "technical" && (
            <div className="space-y-4">
              <AreaChart
                data={topMovers.length > 0 ? topMovers.slice(0, 5).map((mover, i) => ({
                  time: mover.symbol,
                  value: mover.price,
                })) : [
                  { time: "1", value: 120 },
                  { time: "2", value: 135 },
                  { time: "3", value: 128 },
                  { time: "4", value: 142 },
                  { time: "5", value: 138 },
                ]}
                height={280}
              />
            </div>
          )}

          {activeTab === "fundamental" && (
            <div>
              {fundamentalData ? (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {Object.entries(fundamentalData).slice(0, 8).map(([key, value]) => {
                    const displayValue = typeof value === 'number' ? (value as number).toFixed(2) : String(value);
                    return (
                      <div key={key} className="text-center p-3 rounded-lg bg-muted/50">
                        <div className="text-xs text-muted-foreground">{key}</div>
                        <div className="text-sm font-bold mt-1">{displayValue}</div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {["P/E", "P/B", "ROE", "Debt/Eq", "EPS", "Dividend Yield", "Market Cap", "Revenue Growth"].map((metric, i) => (
                    <div key={i} className="text-center p-3 rounded-lg bg-muted/50">
                      <div className="text-xs text-muted-foreground">{metric}</div>
                      <div className="text-sm font-bold mt-1">—</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === "scoring" && (
            <div className="space-y-4">
              {scoringData ? (
                <div className="text-center">
                  <div className="text-3xl font-bold">{scoringData.overall_score?.toFixed(1) || "—"}</div>
                  <div className="text-sm text-muted-foreground">امتیاز کلی</div>
                </div>
              ) : (
                <div className="text-center">
                  <div className="text-3xl font-bold">—</div>
                  <div className="text-sm text-muted-foreground">امتیاز کلی</div>
                </div>
              )}
              <SpiderChart
                labels={["بنیادی", "تکنیکال", "احساسات", "ریسک", "ماکرو", "هوش مصنوعی"]}
                values={
                  scoringData?.dimensions
                    ? Object.values(scoringData.dimensions).map((v: any) => Number(v) * 10)
                    : [65, 75, 50, 80, 60, 70]
                }
                max={100}
                height={320}
              />
            </div>
          )}

          {activeTab === "sentiment" && (
            <BarChart
              data={[
                { time: "1", value: sentimentData ? sentimentData.news : 50, color: "#22C55E" },
                { time: "2", value: sentimentData ? sentimentData.social : 50, color: "#64748B" },
                { time: "3", value: sentimentData ? sentimentData.crypto : 50, color: "#DC2626" },
              ]}
              height={280}
            />
          )}
        </TarotCard>
      </div>
    </DashboardShell>
  );
}
