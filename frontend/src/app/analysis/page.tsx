"use client";

import { NewDashboardShell } from "@/components/layout/NewDashboardShell";
import { TarotCard } from "@/components/ui/TarotCard";
import { AssetTable } from "@/components/dashboard/AssetTable";
import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api";
import { 
  fetchFundamental, 
  fetchTechnical, 
  fetchSentiment, 
  fetchScoring 
} from "@/lib/api/stocks";
import type { AssetRow } from "@/lib/dashboard-data";
import { cn } from "@/lib/cn";
import { t } from "@/lib/i18n";
import { useAuthStore } from "@/store/useAuthStore";

export default function AnalysisPage() {
  
  const [activeTab, setActiveTab] = useState("technical");
  const [topMovers, setTopMovers] = useState<AssetRow[]>([]);
  const [analysisData, setAnalysisData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const analysisTabs = [
    { id: "technical", label: t("app.analysis.tabs.technical", "en"), icon: "📈" },
    { id: "fundamental", label: t("app.analysis.tabs.fundamental", "en"), icon: "🏦" },
    { id: "scoring", label: t("app.analysis.tabs.scoring", "en"), icon: "💯" },
    { id: "sentiment", label: t("app.analysis.tabs.sentiment", "en"), icon: "🎭" },
  ];

  useEffect(() => {
    let active = true;

    async function loadAnalysisData() {
      setLoading(true);
      try {
        const performersRes = await apiClient.get<any>("/analysis/top-performers?limit=10&timeframe=1d&market=NASDAQ");
        const symbolsRes = await apiClient.get<any[]>("/market/symbols?market=NASDAQ&limit=50");

        if (!active) return;

        const symbolMap = new Map(symbolsRes.data.map((s: any) => [s.symbol, s.name]));
        const movers: AssetRow[] = (performersRes.data.data ?? []).map((p: any) => ({
          symbol: p.symbol,
          name: symbolMap.get(p.symbol) || p.name || "",
          market: "NASDAQ",
          price: p.current_price,
          changePct: p.change_percent }));
        setTopMovers(movers.slice(0, 5));

        // Fetch detailed analysis for the top symbol if available
        if (movers.length > 0) {
          const topSymbol = movers[0].symbol;
          const [fundamental, technical, sentiment, scoring] = await Promise.all([
            fetchFundamental(topSymbol),
            fetchTechnical(topSymbol),
            fetchSentiment(topSymbol),
            fetchScoring(topSymbol)
          ]);
          setAnalysisData({ fundamental, technical, sentiment, scoring, symbol: topSymbol });
        }
      } catch (error) {
        console.error("Error loading analysis data:", error);
      } finally {
        if (active) setLoading(false);
      }
    }

    loadAnalysisData();
    return () => { active = false; };
  }, []);

  if (loading) {
    return (
      <NewDashboardShell title={t("app.analysis.title", "en")}>
        <div className="flex min-h-[40vh] items-center justify-center text-muted-foreground">
          {t("app.analysis.loading", "en")}
        </div>
      </NewDashboardShell>
    );
  }

  return (
    <NewDashboardShell title={t("app.analysis.title", "en")}>
      <div className="flex flex-col gap-6">
        {/* Analysis Tabs */}
        <div className="flex gap-2 mb-4 overflow-x-auto pb-2 scrollbar-hide">
          {analysisTabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                "px-4 py-2 rounded-full text-sm font-semibold transition duration-fast ease-flow whitespace-nowrap flex items-center gap-2",
                activeTab === tab.id
                  ? "bg-secondary text-[var(--color-text-primary)] shadow-sm"
                  : "bg-neutral text-muted-foreground hover:bg-neutral/80"
              )}
            >
              <span>{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>

        {/* Top Movers */}
        <TarotCard icon="🚀" title={t("app.analysis.top_movers", "en")}>
          {topMovers.length > 0 ? (
            <AssetTable rows={topMovers} />
          ) : (
            <p className="text-muted-foreground py-4 text-center">{t("app.analysis.no_data", "en")}</p>
          )}
        </TarotCard>

        {/* Technical Analysis Panel */}
        {activeTab === "technical" && (
          <TarotCard icon="[Chart]" title={t("app.analysis.technical_charts", "en")}>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {topMovers.slice(0, 3).map((mover, i) => (
                <div key={i} className="p-4 rounded-xl bg-neutral/50 border border-border/40 transition duration-fast ease-flow hover:bg-neutral">
                  <div className="font-bold text-lg text-foreground">{mover.symbol}</div>
                  <div className="text-xs text-muted-foreground mt-1">{mover.name}</div>
                  <div className="text-xl font-bold mt-2 text-foreground">
                    {mover.price.toLocaleString(false ? "fa-IR" : "en-US")}
                  </div>
                  <div className={`text-sm mt-1 font-semibold ${mover.changePct >= 0 ? "text-success" : "text-primary"}`}>
                    {mover.changePct >= 0 ? "▲" : "▼"} {Math.abs(mover.changePct).toFixed(2)}%
                  </div>
                </div>
              ))}
            </div>
          </TarotCard>
        )}

        {/* Fundamental Analysis Panel */}
        {activeTab === "fundamental" && (
          <TarotCard icon="🏦" title={t("app.analysis.fundamental_indicators", "en").replace("{symbol}", analysisData?.symbol || "")}>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {Object.entries(analysisData?.fundamental || {}).slice(0, 8).map(([key, value]: [string, any], i) => (
                <div key={i} className="text-center p-3 rounded-xl bg-neutral/50 border border-border/40">
                  <div className="text-xs text-muted-foreground uppercase">{key.replace(/_/g, " ")}</div>
                  <div className="text-sm font-bold mt-1 text-foreground">
                    {typeof value === "number" ? value.toLocaleString(false ? "fa-IR" : "en-US") : value || "—"}
                  </div>
                </div>
              ))}
              {(!analysisData?.fundamental || Object.keys(analysisData.fundamental).length === 0) && (
                <div className="col-span-full py-4 text-center text-muted-foreground text-xs">
                  {t("app.analysis.fundamental_not_found", "en")}
                </div>
              )}
            </div>
          </TarotCard>
        )}

        {/* 6D Scoring Panel */}
        {activeTab === "scoring" && (
          <TarotCard icon="💯" title={`${t("app.nav.scoring", "en")} (${analysisData?.symbol || ""})`}>
            {analysisData?.scoring ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-secondary/10 rounded-xl">
                  <div>
                    <div className="text-xs text-muted-foreground">{t("app.analysis.overall_score", "en")}</div>
                    <div className="text-3xl font-bold text-secondary">
                      {analysisData.scoring.overall_score?.toLocaleString(false ? "fa-IR" : "en-US")}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs text-muted-foreground">{t("app.analysis.grade", "en")}</div>
                    <div className="text-2xl font-bold text-foreground">{analysisData.scoring.grade}</div>
                  </div>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {Object.entries(analysisData.scoring.dimensions || {}).map(([dim, score]: [string, any], i) => (
                    <div key={i} className="p-3 rounded-xl border border-border/40 bg-neutral/30">
                      <div className="text-xs text-muted-foreground capitalize">{t(`app.scoring.dimensions.${dim.toLowerCase()}`, "en")}</div>
                      <div className="text-lg font-bold mt-1">{score?.toLocaleString(false ? "fa-IR" : "en-US")}</div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="p-8 text-center text-muted-foreground">
                <p>{t("app.analysis.scoring_not_found", "en")}</p>
              </div>
            )}
          </TarotCard>
        )}

        {/* Sentiment Panel */}
        {activeTab === "sentiment" && (
          <TarotCard icon="🎭" title={t("app.analysis.sentiment_title", "en").replace("{symbol}", analysisData?.symbol || "")}>
            {analysisData?.sentiment ? (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {[
                  { 
                    label: t("app.analysis.sentiment_labels.overall", "en"), 
                    value: t(`app.analysis.sentiment_values.${analysisData.sentiment.label?.toLowerCase()}`, "en"), 
                    score: analysisData.sentiment.confidence, 
                    color: analysisData.sentiment.label === "positive" ? "text-success" : analysisData.sentiment.label === "negative" ? "text-primary" : "text-muted-foreground" 
                  },
                  { 
                    label: t("app.analysis.sentiment_labels.news_count", "en"), 
                    value: t("app.analysis.sentiment_values.news_items", "en").replace("{count}", analysisData.sentiment.news_count?.toLocaleString(false ? "fa-IR" : "en-US") || "0"), 
                    score: null, 
                    color: "text-foreground" 
                  },
                  { 
                    label: t("app.analysis.sentiment_labels.confidence", "en"), 
                    value: `${(analysisData.sentiment.confidence * 100).toLocaleString(false ? "fa-IR" : "en-US", { maximumFractionDigits: 0 })}٪`, 
                    score: null, 
                    color: "text-secondary" 
                  },
                ].map((sentiment, i) => (
                  <div key={i} className="text-center p-6 rounded-xl bg-neutral/50 border border-border/40">
                    <div className="text-xs text-muted-foreground">{sentiment.label}</div>
                    <div className={`text-lg font-bold mt-2 ${sentiment.color}`}>{sentiment.value}</div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-8 text-center text-muted-foreground">
                <p>{t("app.analysis.sentiment_not_found", "en")}</p>
              </div>
            )}
          </TarotCard>
        )}
      </div>
    </NewDashboardShell>
  );
}
