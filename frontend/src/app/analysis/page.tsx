"use client";

import { DashboardShell } from "@/components/layout/DashboardShell";
import { TarotCard } from "@/components/ui/TarotCard";
import { SignalList } from "@/components/dashboard/SignalList";
import { AssetTable } from "@/components/dashboard/AssetTable";
import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api";
import type { AssetRow, SignalRow } from "@/lib/dashboard-data";

const analysisTabs = [
  { id: "technical", label: "تحلیل تکنیکال", icon: "📊" },
  { id: "fundamental", label: "تحلیل بنیادی", icon: "💰" },
  { id: "scoring", label: "بررسی ۶ بعدی", icon: "🧮" },
  { id: "sentiment", label: "احساسات بازار", icon: "👁️‍🗨️" },
];

export default function AnalysisPage() {
  const [activeTab, setActiveTab] = useState("technical");
  const [topSignals, setTopSignals] = useState<SignalRow[]>([]);
  const [topMovers, setTopMovers] = useState<AssetRow[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;

    async function loadAnalysisData() {
      setLoading(true);
      setTopSignals([]);
      setTopMovers([]);

      try {
        // Fetch signal summary
        const summaryRes = await apiClient.get<{ status: string; data: any; summary: Record<string, number> }>(
          "/analysis/signals-summary?min_confidence=0.6"
        );

        // Fetch top performers (TSE)
        const performersRes = await apiClient.get<{ status: string; data: any[] }>(
          "/analysis/top-performers?limit=10&timeframe=1d&market=TSE"
        );

        // Fetch symbols to map performer data
        const symbolsRes = await apiClient.get<{ symbol: string; name: string; market: string }[]>(
          "/market/symbols?market=TSE&limit=50"
        );

        if (!active) return;

        // Build signal list from summary
        if (summaryRes.status === "success") {
          const signalTypes = Object.entries(summaryRes.data?.summary ?? {})
            .filter(([, count]) => Number(count) > 0)
            .sort(([, a], [, b]) => Number(b) - Number(a))
            .slice(0, 5);

          const signals: SignalRow[] = [];

          // Get signals for top performers instead of per-type
          const topPerformerSymbols = (performersRes.data ?? [])
            .sort((a: any, b: any) => Math.abs(b.change_percent) - Math.abs(a.change_percent))
            .slice(0, 5);

          for (const performer of topPerformerSymbols) {
            try {
              const signalRes = await apiClient.get<{ status: string; data: any }>(
                `/analysis/signals/${encodeURIComponent(performer.symbol)}`
              );
              if (signalRes.status === "success") {
                signals.push({
                  symbol: performer.symbol,
                  type: signalRes.data.signal_type || "HOLD",
                  confidence: signalRes.data.confidence ?? 50,
                  model: signalRes.data.model_name || "ML",
                });
              }
            } catch {}
          }

          setTopSignals(signals);
        }

        // Build top movers from performers data and symbols
        if (performersRes.status === "success" && symbolsRes.length > 0) {
          const symbolMap = new Map(symbolsRes.map((s) => [s.symbol, s.name]));
          const movers: AssetRow[] = (performersRes.data ?? [])
            .map((p: any) => ({
              symbol: p.symbol,
              name: symbolMap.get(p.symbol) || p.name || "",
              market: p.market === "NASDAQ" || p.market === "NYSE" ? "NASDAQ" :
                      p.market === "BINANCE" || p.market === "KRAKEN" ? "BINANCE" : "TSE",
              price: p.current_price ?? p.price ?? 0,
              changePct: p.change_percent ?? p.change_pct ?? 0,
            }))
            .sort((a: AssetRow, b: AssetRow) => Math.abs(b.changePct) - Math.abs(a.changePct));

          setTopMovers(movers.slice(0, 5));
        }
      } catch (error) {
        // Handle error silently
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

  return (
    <DashboardShell title="تحلیل">
      <div className="flex flex-col gap-6">
        {/* Analysis Tabs */}
        <div className="flex gap-2 mb-4 overflow-x-auto pb-2">
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
        <TarotCard icon="🎯" title="سیگنال‌های رتبه‌بندی شده">
          {topSignals.length > 0 ? (
            <SignalList signals={topSignals} />
          ) : (
            <p className="text-muted-foreground py-4">سیگنالی موجود نیست</p>
          )}
        </TarotCard>

        {/* Top Movers */}
        <TarotCard icon="🚀" title="پرنوسان‌ترین سهام">
          {topMovers.length > 0 ? (
            <AssetTable rows={topMovers} />
          ) : (
            <p className="text-muted-foreground py-4">داده‌ای موجود نیست</p>
          )}
        </TarotCard>

        {/* Active Analysis Tab Content */}
        <TarotCard icon="📊" title={analysisTabs.find((t) => t.id === activeTab)?.label}>
          <div className="h-64 flex items-center justify-center text-muted-foreground">
            <p>این بخش به‌زودی اضافه می‌شود</p>
          </div>
        </TarotCard>

        {/* Technical Analysis Panel */}
        {activeTab === "technical" && (
          <TarotCard icon="📈" title="نمودارهای تکنیکال">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {topMovers.slice(0, 3).map((mover, i) => (
                <div key={i} className="p-4 rounded-lg bg-muted/50">
                  <div className="font-bold text-lg">{mover.symbol}</div>
                  <div className="text-sm text-muted-foreground mt-1">{mover.name}</div>
                  <div className="text-xl font-bold mt-2">
                    {mover.price.toLocaleString("fa-IR")}
                  </div>
                  <div className={`text-sm mt-1 ${mover.changePct >= 0 ? "text-success" : "text-primary"}`}>
                    {mover.changePct >= 0 ? "▲" : "▼"} {Math.abs(mover.changePct).toFixed(2)}%
                  </div>
                </div>
              ))}
            </div>
          </TarotCard>
        )}

        {/* Fundamental Analysis Panel */}
        {activeTab === "fundamental" && (
          <TarotCard icon="💎" title="شاخص‌های بنیادی کلیدی">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {["P/E", "P/B", "ROE", "Debt/Eq", "EPS", "Dividend Yield", "Market Cap", "Revenue Growth"].map((metric, i) => (
                <div key={i} className="text-center p-3 rounded-lg bg-muted/50">
                  <div className="text-xs text-muted-foreground">{metric}</div>
                  <div className="text-sm font-bold mt-1">—</div>
                </div>
              ))}
            </div>
          </TarotCard>
        )}

        {/* 6D Scoring Panel */}
        {activeTab === "scoring" && (
          <TarotCard icon="🧮" title="بررسی ۶ بعدی">
            <div className="p-4 text-muted-foreground">
              سامانه ۶ بعدی تحلیل سرمایه‌گذاری در حال بارگذاری است...
            </div>
          </TarotCard>
        )}

        {/* Sentiment Panel */}
        {activeTab === "sentiment" && (
          <TarotCard icon="🗣️" title="احساس و ذهنیت بازار">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {[
                { label: "احساسات خبری", value: "محاسبه در حال اجراست", trend: "stable", color: "text-muted-foreground" },
                { label: "احساسات اجتماعی", value: "محاسبه در حال اجراست", trend: "stable", color: "text-muted-foreground" },
                { label: "احساسات کریپتو", value: "محاسبه در حال اجراست", trend: "stable", color: "text-muted-foreground" },
              ].map((sentiment, i) => (
                <div key={i} className="text-center p-4 rounded-lg bg-muted/50">
                  <div className="text-xs text-muted-foreground">{sentiment.label}</div>
                  <div className={`text-lg font-bold mt-2 ${sentiment.color}`}>{sentiment.value}</div>
                </div>
              ))}
            </div>
          </TarotCard>
        )}
      </div>
    </DashboardShell>
  );
}