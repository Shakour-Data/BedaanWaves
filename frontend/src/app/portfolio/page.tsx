"use client";

import { useEffect, useState, useCallback, useMemo, useRef } from "react";
import { useRouter } from "next/navigation";
import { NewDashboardShell } from "@/components/layout/NewDashboardShell";
import { TarotCard } from "@/components/ui/TarotCard";
import { AssetTable } from "@/components/shared/AssetTable";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { PageLoading } from "@/components/ui/PageLoading";
import { apiClient } from "@/lib/api";
import { useAuthStore } from "@/store/useAuthStore";
import type { AssetRow } from "@/lib/dashboard-data";
import { isNasdaqEquityLike } from "@/lib/dashboard-data";
import {
  useLiveData,
  LiveConnectionIndicator,
} from "@/hooks/useLiveData";

import { t } from "@/lib/i18n";

interface PortfolioSummary {
  id: string;
}

interface Holding {
  asset_id: string;
  quantity: number;
  entry_price: number;
}

interface SymbolItem {
  id: string;
  symbol: string;
  name: string;
  market: string;
}

interface PriceItem {
  price?: number;
  change_pct?: number;
}

interface MarketStreamPayload {
  top_movers?: Array<{
    symbol: string;
    price?: number;
    change_pct?: number;
  }>;
  quotes?: Record<string, { price?: number; change_pct?: number }>;
}

type LiveQuotesMap = Record<string, { price: number; changePct: number; ts: number }>;

export default function PortfolioPage() {
  const router = useRouter();
  const { user } = useAuthStore();
  const [holdings, setHoldings] = useState<AssetRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [liveQuotes, setLiveQuotes] = useState<LiveQuotesMap>({});
  const lastQuoteEventRef = useRef<number | null>(null);
  const [lastQuoteEventTs, setLastQuoteEventTs] = useState<number | null>(null);

  const applyQuotePatch = useCallback((symbol: string, price?: number, changePct?: number) => {
    const sym = symbol.toUpperCase();
    const now = Date.now();
    setLiveQuotes((prev) => {
      const existing = prev[sym];
      const nextPrice = typeof price === "number" ? price : existing?.price ?? 0;
      const nextChange = typeof changePct === "number" ? changePct : existing?.changePct ?? 0;
      if (
        existing &&
        existing.price === nextPrice &&
        existing.changePct === nextChange
      ) {
        return prev;
      }
      return {
        ...prev,
        [sym]: { price: nextPrice, changePct: nextChange, ts: now },
      };
    });
    lastQuoteEventRef.current = now;
    setLastQuoteEventTs(now);
  }, []);

  const handleMarketData = useCallback(
    (payload: MarketStreamPayload) => {
      if (payload?.top_movers && Array.isArray(payload.top_movers)) {
        for (const m of payload.top_movers) {
          applyQuotePatch(m.symbol, m.price, m.change_pct);
        }
      }
      if (payload?.quotes && typeof payload.quotes === "object") {
        for (const [sym, q] of Object.entries(payload.quotes)) {
          applyQuotePatch(sym, q?.price, q?.change_pct);
        }
      }
    },
    [applyQuotePatch]
  );

  const holdingSymbols = useMemo(
    () => holdings.map((h) => h.symbol.toUpperCase()),
    [holdings]
  );

  const marketLive = useLiveData<MarketStreamPayload>("market", {
    enabled: holdingSymbols.length > 0,
    onData: handleMarketData,
  });

  const liveHoldings = useMemo<AssetRow[]>(() => {
    if (holdings.length === 0) return holdings;
    let anyChange = false;
    const next = holdings.map((h) => {
      const live = liveQuotes[h.symbol.toUpperCase()];
      if (!live) return h;
      if (live.price === h.price && live.changePct === h.changePct) return h;
      anyChange = true;
      return { ...h, price: live.price ?? h.price, changePct: live.changePct ?? h.changePct };
    });
    return anyChange ? next : holdings;
  }, [holdings, liveQuotes]);

  const stats = useMemo(() => {
    if (liveHoldings.length === 0) return [];
    const totalValue = liveHoldings.reduce((sum, h) => sum + (h.price * (h.quantity ?? 0)), 0);
    const totalCost = liveHoldings.reduce((sum, h) => sum + ((h.avg_price ?? 0) * (h.quantity ?? 0)), 0);
    const totalPnL = totalValue - totalCost;
    const totalReturnPct = totalCost > 0 ? (totalPnL / totalCost) * 100 : 0;
    return [
      { label: t("app.portfolio.total_value"), value: `$${totalValue.toLocaleString("en-US")}`, changePct: totalReturnPct },
      { label: t("app.portfolio.total_pnl"), value: `$${totalPnL.toLocaleString("en-US")}`, changePct: totalReturnPct },
      { label: t("app.portfolio.symbols_count"), value: String(liveHoldings.length), changePct: 0 },
      { label: t("app.portfolio.daily_return"), value: `${(totalReturnPct / 30).toFixed(2)}%`, changePct: totalReturnPct / 30 },
    ];
  }, [liveHoldings]);

  const loadPortfolio = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const portfoliosRes = await apiClient.get<PortfolioSummary[]>("/portfolio/");
      const portfolios = portfoliosRes.data;
      
      if (portfolios && portfolios.length > 0) {
        const portfolioId = portfolios[0].id;
        
        const holdingsRes = await apiClient.get<Holding[]>(`/portfolio/${portfolioId}/holdings`);
        const holdingsData = holdingsRes.data;
        
        const symbolsRes = await apiClient.get<SymbolItem[]>("/market/symbols");
        const allAssets = symbolsRes.data;
        const assetMap = new Map(allAssets.map((a) => [a.id, a]));
        
        if (holdingsData.length > 0) {
          const symbols = holdingsData
            .map((h) => assetMap.get(h.asset_id)?.symbol)
            .filter((symbol): symbol is string => Boolean(symbol));
          const pricesRes = await apiClient.get<{ data: Record<string, PriceItem> }>(
            `/market/latest-prices?${symbols.map((s) => `symbols=${encodeURIComponent(s)}`).join("&")}`
          );
          
          const prices = pricesRes.data?.data || {};
          
          const enrichedHoldings: AssetRow[] = holdingsData
            .map((h) => {
              const asset = assetMap.get(h.asset_id);
              const symbol = asset?.symbol;
              if (!symbol) return null;
              const priceData = prices[symbol];
              const row: AssetRow = {
                symbol,
                name: asset?.name || "Unknown",
                market: "NASDAQ",
                price: priceData?.price ?? h.entry_price ?? 0,
                changePct: priceData?.change_pct ?? 0,
                quantity: Number(h.quantity),
                avg_price: Number(h.entry_price),
              };
              return isNasdaqEquityLike(row) ? row : null;
            })
            .filter((h): h is AssetRow => h !== null);
          
          setHoldings(enrichedHoldings);
        } else {
          setHoldings([]);
        }
      } else {
        setHoldings([]);
      }
    } catch {
      setError(t("app.portfolio.error_loading"));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (user) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      loadPortfolio();
    } else {
      setLoading(false);
      setError(t("app.portfolio.login_required"));
    }
  }, [user, loadPortfolio]);

  if (loading) {
    return (
      <NewDashboardShell title={t("app.portfolio.title")}>
        <PageLoading />
      </NewDashboardShell>
    );
  }

  if (error) {
    return (
      <NewDashboardShell title={t("app.portfolio.title")}>
        <TarotCard icon="⚠️" title={t("app.portfolio.error_loading")} className="max-w-md mx-auto border-error/20 bg-error/5">
          <div className="py-4 text-center">
            <p className="text-sm text-error font-medium mb-4">{error}</p>
            <PrimaryButton onClick={() => { setError(null); loadPortfolio(); }} variant="outline" size="sm">
              {t("app.auth.submit")}
            </PrimaryButton>
          </div>
        </TarotCard>
      </NewDashboardShell>
    );
  }

  return (
    <NewDashboardShell title={t("app.portfolio.title")}>
      <div className="flex flex-col gap-6 animate-in fade-in duration-500">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">
              {t("app.portfolio.title")}
            </h1>
          </div>
          <LiveConnectionIndicator
            health={marketLive.connectionHealth}
            dataAgeMs={marketLive.lastDataAgeMs}
            lastEventTs={lastQuoteEventTs}
            label="Quotes"
          />
        </div>

        <section className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {stats.map((stat, i) => (
            <div key={i} className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5 shadow-sm transition-all hover:shadow-md">
              <p className="text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider">{stat.label}</p>
              <p className="text-xl font-bold text-[var(--color-text-primary)] mt-1">{stat.value}</p>
              {stat.changePct !== undefined && (
                <p className={`text-xs font-medium mt-1 ${stat.changePct >= 0 ? "text-[var(--color-success)]" : "text-[var(--color-error)]"}`}>
                  {stat.changePct >= 0 ? "+" : ""}{stat.changePct.toFixed(2)}%
                </p>
              )}
            </div>
          ))}
        </section>

        <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-sm">
          <div className="flex items-center gap-3 p-6 border-b border-[var(--color-border)]">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--color-primary-soft)] text-[var(--color-primary)]">
              <span className="text-lg">💼</span>
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-[var(--color-text-primary)]">{t("app.portfolio.current_holdings")}</h3>
              <p className="text-xs text-[var(--color-text-muted)]">Your current portfolio holdings</p>
            </div>
          </div>
          <div className="p-6">
            {liveHoldings.length > 0 ? (
              <AssetTable rows={liveHoldings} />
            ) : (
              <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
                <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-muted text-muted-foreground mb-4">
                  <svg className="h-8 w-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M3 3h7v7H3zM14 3h7v7h-7zM14 14h7v7h-7zM3 14h7v7H3z"/></svg>
                </div>
                <p className="text-lg font-bold text-foreground mb-2">{t("app.portfolio.empty_title")}</p>
                <p className="text-sm mb-6 max-w-xs text-center text-muted-foreground">{t("app.portfolio.empty_desc")}</p>
                <button onClick={() => router.push("/stocks")} className="rounded-xl bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-primary-hover)] px-6 py-2.5 text-sm font-semibold text-white shadow-lg shadow-[var(--color-primary)]/25 transition-all hover:shadow-xl hover:-translate-y-0.5">
                  {t("app.portfolio.view_stocks")}
                </button>
              </div>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
            <div className="flex items-center gap-3 mb-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--color-primary-soft)] text-[var(--color-primary)]">
                <span className="text-lg">📈</span>
              </div>
              <div>
                <h3 className="font-semibold text-[var(--color-text-primary)]">{t("app.portfolio.performance")}</h3>
                <p className="text-xs text-[var(--color-text-muted)]">Portfolio performance over time</p>
              </div>
            </div>
            <div className="h-64 flex flex-col items-center justify-center text-[var(--color-text-muted)] bg-[var(--color-background)]/50 rounded-xl border border-dashed border-[var(--color-border)]">
              <p className="text-sm font-medium">Coming Soon</p>
              <p className="text-xs mt-1">Performance chart under development</p>
            </div>
          </div>

          <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
            <div className="flex items-center gap-3 mb-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--color-primary-soft)] text-[var(--color-primary)]">
                <span className="text-lg">🥧</span>
              </div>
              <div>
                <h3 className="font-semibold text-[var(--color-text-primary)]">{t("app.portfolio.distribution")}</h3>
                <p className="text-xs text-[var(--color-text-muted)]">Asset allocation breakdown</p>
              </div>
            </div>
            <div className="h-64 flex flex-col items-center justify-center text-[var(--color-text-muted)] bg-[var(--color-background)]/50 rounded-xl border border-dashed border-[var(--color-border)]">
              <p className="text-sm font-medium">Coming Soon</p>
              <p className="text-xs mt-1">Distribution chart under development</p>
            </div>
          </div>
        </div>
      </div>
    </NewDashboardShell>
  );
}
