"use client";

import { NewDashboardShell } from "@/components/layout/NewDashboardShell";
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
import { isNasdaqEquityLike } from "@/lib/dashboard-data";
import { cn } from "@/lib/cn";
import { t } from "@/lib/i18n";

interface Performer {
  symbol: string;
  name?: string;
  current_price?: number;
  change_percent?: number;
}

interface SymbolItem {
  symbol: string;
  name: string;
}

interface AnalysisData {
  fundamental?: Record<string, unknown>;
  technical?: unknown;
  sentiment?: {
    label?: string;
    confidence?: number;
    news_count?: number;
  };
  scoring?: {
    overall_score?: number;
    grade?: string;
    dimensions?: Record<string, unknown>;
  };
  symbol?: string;
}

export default function AnalysisPage() {
  
  const [activeTab, setActiveTab] = useState("technical");
  const [topMovers, setTopMovers] = useState<AssetRow[]>([]);
  const [analysisData, setAnalysisData] = useState<AnalysisData | null>(null);
  const [loading, setLoading] = useState(true);

  const analysisTabs = [
    { id: "technical", label: t("app.analysis.tabs.technical"), icon: "📈" },
    { id: "fundamental", label: t("app.analysis.tabs.fundamental"), icon: "🏦" },
    { id: "scoring", label: t("app.analysis.tabs.scoring"), icon: "💯" },
    { id: "sentiment", label: t("app.analysis.tabs.sentiment"), icon: "🎭" },
  ];

  useEffect(() => {
    let active = true;

    async function loadAnalysisData() {
      setLoading(true);
      try {
        const performersRes = await apiClient.get<{ data: Performer[] }>("/analysis/top-performers?limit=10&timeframe=1d&market=NASDAQ");
        const symbolsRes = await apiClient.get<{ data: SymbolItem[] }>("/market/symbols?market=NASDAQ&limit=50");

        if (!active) return;

        const symbolMap = new Map(symbolsRes.data.data.map((s) => [s.symbol, s.name]));
        const movers: AssetRow[] = (performersRes.data.data ?? [])
          .filter((p) => isNasdaqEquityLike({ symbol: p.symbol }))
          .map((p) => ({
            symbol: p.symbol,
            name: symbolMap.get(p.symbol) || p.name || "",
            market: "NASDAQ",
            price: p.current_price ?? 0,
            changePct: p.change_percent ?? 0,
          }));
        setTopMovers(movers.slice(0, 5));

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
      <NewDashboardShell title={t("app.analysis.title")}>
        <div className="flex min-h-[40vh] items-center justify-center text-muted-foreground">
          {t("app.analysis.loading")}
        </div>
      </NewDashboardShell>
    );
  }

  return (
    <NewDashboardShell title={t("app.analysis.title")}>
      <div className="flex flex-col gap-6 animate-in fade-in duration-500">
        {/* Analysis Tabs */}
        <div className="flex gap-2 overflow-x-auto pb-2">
          {analysisTabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                "inline-flex items-center gap-2 rounded-xl border px-4 py-2.5 text-sm font-semibold transition-all whitespace-nowrap",
                activeTab === tab.id
                  ? "border-[var(--color-primary)] bg-[var(--color-primary)] text-white shadow-lg shadow-[var(--color-primary)]/20"
                  : "border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text-secondary)] hover:border-[var(--color-primary)]/30 hover:text-[var(--color-text-primary)]"
              )}
            >
              <span>{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>

        {/* Top Movers */}
        <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
          <div className="flex items-center gap-3 mb-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--color-primary-soft)] text-[var(--color-primary)]">
              <span className="text-lg">🚀</span>
            </div>
            <div>
              <h3 className="font-semibold text-[var(--color-text-primary)]">{t("app.analysis.top_movers")}</h3>
              <p className="text-xs text-[var(--color-text-muted)]">Top performing stocks today</p>
            </div>
          </div>
          {topMovers.length > 0 ? (
            <AssetTable rows={topMovers} />
          ) : (
            <p className="text-[var(--color-text-muted)] py-8 text-center text-sm">{t("app.analysis.no_data")}</p>
          )}
        </div>

        {/* Technical Analysis Panel */}
        {activeTab === "technical" && (
          <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
            <div className="flex items-center gap-3 mb-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--color-primary-soft)] text-[var(--color-primary)]">
                <span className="text-lg">📈</span>
              </div>
              <div>
                <h3 className="font-semibold text-[var(--color-text-primary)]">{t("app.analysis.technical_charts")}</h3>
                <p className="text-xs text-[var(--color-text-muted)]">Technical indicators for top movers</p>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {topMovers.slice(0, 3).map((mover, i) => (
                <div key={i} className="group rounded-xl border border-[var(--color-border)] bg-[var(--color-background)]/50 p-5 transition-all hover:border-[var(--color-primary)]/30 hover:shadow-md">
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <div className="font-bold text-lg text-[var(--color-text-primary)]">{mover.symbol}</div>
                      <div className="text-xs text-[var(--color-text-muted)]">{mover.name}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-bold text-[var(--color-text-primary)]">
                        {mover.price.toLocaleString("en-US")}
                      </div>
                      <div className={`text-sm font-semibold ${mover.changePct >= 0 ? "text-[var(--color-success)]" : "text-[var(--color-error)]"}`}>
                        {mover.changePct >= 0 ? "+" : ""}{mover.changePct.toFixed(2)}%
                      </div>
                    </div>
                  </div>
                  <div className="h-16 rounded-lg bg-[var(--color-border)]/30 flex items-end gap-1 p-2">
                    {Array.from({ length: 12 }).map((_, j) => (
                      <div key={j} className="flex-1 rounded bg-[var(--color-primary)]/60 hover:bg-[var(--color-primary)] transition-colors" style={{ height: `${30 + Math.random() * 70}%` }} />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Fundamental Analysis Panel */}
        {activeTab === "fundamental" && (
          <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
            <div className="flex items-center gap-3 mb-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--color-primary-soft)] text-[var(--color-primary)]">
                <span className="text-lg">🏦</span>
              </div>
              <div>
                <h3 className="font-semibold text-[var(--color-text-primary)]">{t("app.analysis.fundamental_indicators").replace("{symbol}", analysisData?.symbol || "")}</h3>
                <p className="text-xs text-[var(--color-text-muted)]">Key fundamental metrics</p>
              </div>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {Object.entries(analysisData?.fundamental || {}).slice(0, 8).map(([key, value]: [string, unknown], i) => (
                <div key={i} className="rounded-xl border border-[var(--color-border)] bg-[var(--color-background)]/50 p-4 text-center">
                  <div className="text-xs text-[var(--color-text-muted)] uppercase tracking-wider">{key.replace(/_/g, " ")}</div>
                  <div className="text-sm font-bold mt-1 text-[var(--color-text-primary)]">
                     {typeof value === "number" ? value.toLocaleString("en-US") : typeof value === "string" ? value : "—"}
                  </div>
                </div>
              ))}
              {(!analysisData?.fundamental || Object.keys(analysisData.fundamental).length === 0) && (
                <div className="col-span-full py-8 text-center text-[var(--color-text-muted)] text-sm">
                  {t("app.analysis.fundamental_not_found")}
                </div>
              )}
            </div>
          </div>
        )}

        {/* 6D Scoring Panel */}
        {activeTab === "scoring" && (
          <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
            <div className="flex items-center gap-3 mb-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--color-primary-soft)] text-[var(--color-primary)]">
                <span className="text-lg">💯</span>
              </div>
              <div>
                <h3 className="font-semibold text-[var(--color-text-primary)]">{`${t("app.nav.scoring")} (${analysisData?.symbol || ""})`}</h3>
                <p className="text-xs text-[var(--color-text-muted)]">AI-powered stock scoring</p>
              </div>
            </div>
            {analysisData?.scoring ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between rounded-xl border border-[var(--color-border)] bg-[var(--color-background)]/50 p-5">
                  <div>
                    <div className="text-xs text-[var(--color-text-muted)]">{t("app.analysis.overall_score")}</div>
                    <div className="text-3xl font-bold bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-accent)] bg-clip-text text-transparent">
                      {analysisData.scoring.overall_score?.toLocaleString("en-US")}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs text-[var(--color-text-muted)]">{t("app.analysis.grade")}</div>
                    <div className="text-2xl font-bold text-[var(--color-text-primary)]">{analysisData.scoring.grade}</div>
                  </div>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {Object.entries(analysisData.scoring.dimensions || {}).map(([dim, score]: [string, unknown], i) => (
                    <div key={i} className="rounded-xl border border-[var(--color-border)] bg-[var(--color-background)]/30 p-3">
                      <div className="text-xs text-[var(--color-text-muted)] capitalize">{t(`app.scoring.dimensions.${dim.toLowerCase()}`)}</div>
                      <div className="text-sm font-bold mt-1 text-[var(--color-text-primary)]">{typeof score === "number" ? score.toLocaleString("en-US") : String(score ?? "—")}</div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <p className="text-[var(--color-text-muted)] py-8 text-center text-sm">{t("app.analysis.scoring_not_found")}</p>
            )}
          </div>
        )}

        {/* Sentiment Analysis Panel */}
        {activeTab === "sentiment" && (
          <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
            <div className="flex items-center gap-3 mb-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--color-primary-soft)] text-[var(--color-primary)]">
                <span className="text-lg">🎭</span>
              </div>
              <div>
                <h3 className="font-semibold text-[var(--color-text-primary)]">{t("app.analysis.sentiment_title").replace("{symbol}", analysisData?.symbol || "")}</h3>
                <p className="text-xs text-[var(--color-text-muted)]">Market sentiment analysis</p>
              </div>
            </div>
            {analysisData?.sentiment ? (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {[
                  {
                    label: t("app.analysis.sentiment_labels.overall"),
                    value: t(`app.analysis.sentiment_values.${analysisData.sentiment.label?.toLowerCase()}`),
                    score: analysisData.sentiment.confidence,
                    color: analysisData.sentiment.label === "positive" ? "text-[var(--color-success)]" : analysisData.sentiment.label === "negative" ? "text-[var(--color-error)]" : "text-[var(--color-text-muted)]"
                  },
                  {
                    label: t("app.analysis.sentiment_labels.news_count"),
                    value: t("app.analysis.sentiment_values.news_items").replace("{count}", analysisData.sentiment.news_count?.toLocaleString("en-US") || "0"),
                    score: null,
                    color: "text-[var(--color-text-primary)]"
                  },
                  {
                    label: t("app.analysis.sentiment_labels.confidence"),
                     value: `${((analysisData.sentiment.confidence ?? 0) * 100).toLocaleString("en-US", { maximumFractionDigits: 0 })}%`,
                    score: null,
                    color: "text-[var(--color-primary)]"
                  },
                ].map((sentiment, i) => (
                  <div key={i} className="rounded-xl border border-[var(--color-border)] bg-[var(--color-background)]/50 p-6 text-center">
                    <div className="text-xs text-[var(--color-text-muted)]">{sentiment.label}</div>
                    <div className={`text-lg font-bold mt-2 ${sentiment.color}`}>{sentiment.value}</div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-[var(--color-text-muted)] py-8 text-center text-sm">{t("app.analysis.sentiment_not_found")}</p>
            )}
          </div>
        )}
      </div>
    </NewDashboardShell>
  );
}
