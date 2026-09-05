"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { NewDashboardShell } from "@/components/layout/NewDashboardShell";
import { TarotCard } from "@/components/ui/TarotCard";
import { AssetTable } from "@/components/dashboard/AssetTable";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { PageLoading } from "@/components/ui/PageLoading";
import { apiClient } from "@/lib/api";
import { useAuthStore } from "@/store/useAuthStore";
import type { AssetRow } from "@/lib/dashboard-data";
import { isNasdaqEquityLike } from "@/lib/dashboard-data";

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

export default function PortfolioPage() {
  const router = useRouter();
  const { user } = useAuthStore();
  const [holdings, setHoldings] = useState<AssetRow[]>([]);
  const [stats, setStats] = useState<Array<{ label: string; value: string; changePct?: number }>>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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
          
          const totalValue = enrichedHoldings.reduce((sum, h) => sum + (h.price * (h.quantity ?? 0)), 0);
          const totalCost = enrichedHoldings.reduce((sum, h) => sum + ((h.avg_price ?? 0) * (h.quantity ?? 0)), 0);
          const totalPnL = totalValue - totalCost;
          const totalReturnPct = totalCost > 0 ? (totalPnL / totalCost) * 100 : 0;
          
          setStats([
            { label: t("app.portfolio.total_value", "en"), value: `$${totalValue.toLocaleString("en-US")}`, changePct: totalReturnPct },
            { label: t("app.portfolio.total_pnl", "en"), value: `$${totalPnL.toLocaleString("en-US")}`, changePct: totalReturnPct },
            { label: t("app.portfolio.symbols_count", "en"), value: String(enrichedHoldings.length), changePct: 0 },
            { label: t("app.portfolio.daily_return", "en"), value: `${(totalReturnPct / 30).toFixed(2)}%`, changePct: totalReturnPct / 30 },
          ]);
        } else {
          setHoldings([]);
          setStats([
            { label: t("app.portfolio.total_value", "en"), value: "$0", changePct: 0 },
            { label: t("app.portfolio.total_pnl", "en"), value: "$0", changePct: 0 },
            { label: t("app.portfolio.symbols_count", "en"), value: "0", changePct: 0 },
            { label: t("app.portfolio.daily_return", "en"), value: "0%", changePct: 0 },
          ]);
        }
      } else {
        setHoldings([]);
        setStats([]);
      }
    } catch {
      setError(t("app.portfolio.error_loading", "en"));
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
      setError(t("app.portfolio.login_required", "en"));
    }
  }, [user, loadPortfolio]);

  if (loading) {
    return (
      <NewDashboardShell title={t("app.portfolio.title", "en")}>
        <PageLoading />
      </NewDashboardShell>
    );
  }

  if (error) {
    return (
      <NewDashboardShell title={t("app.portfolio.title", "en")}>
        <TarotCard icon="⚠️" title={t("app.portfolio.error_loading", "en")} className="max-w-md mx-auto border-error/20 bg-error/5">
          <div className="py-4 text-center">
            <p className="text-sm text-error font-medium mb-4">{error}</p>
            <PrimaryButton onClick={() => { setError(null); loadPortfolio(); }} variant="outline" size="sm">
              {t("app.auth.submit", "en")}
            </PrimaryButton>
          </div>
        </TarotCard>
      </NewDashboardShell>
    );
  }

  return (
    <NewDashboardShell title={t("app.portfolio.title", "en")}>
      <div className="flex flex-col gap-6 animate-in fade-in duration-500">
        {/* Portfolio Summary */}
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

        {/* Holdings */}
        <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-sm">
          <div className="flex items-center gap-3 p-6 border-b border-[var(--color-border)]">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--color-primary-soft)] text-[var(--color-primary)]">
              <span className="text-lg">💼</span>
            </div>
            <div>
              <h3 className="font-semibold text-[var(--color-text-primary)]">{t("app.portfolio.current_holdings", "en")}</h3>
              <p className="text-xs text-[var(--color-text-muted)]">Your current portfolio holdings</p>
            </div>
          </div>
          <div className="p-6">
            {holdings.length > 0 ? (
              <AssetTable rows={holdings} />
            ) : (
              <div className="flex flex-col items-center justify-center py-12 text-[var(--color-text-muted)]">
                <div className="text-4xl mb-4">📭</div>
                <p className="text-lg font-bold text-[var(--color-text-primary)] mb-2">{t("app.portfolio.empty_title", "en")}</p>
                <p className="text-sm mb-6 max-w-xs text-center">{t("app.portfolio.empty_desc", "en")}</p>
                <button onClick={() => router.push("/stocks")} className="rounded-xl bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-primary-hover)] px-6 py-2.5 text-sm font-semibold text-white shadow-lg shadow-[var(--color-primary)]/25 transition-all hover:shadow-xl hover:-translate-y-0.5">
                  {t("app.portfolio.view_stocks", "en")}
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Performance & Distribution */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
            <div className="flex items-center gap-3 mb-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--color-primary-soft)] text-[var(--color-primary)]">
                <span className="text-lg">📈</span>
              </div>
              <div>
                <h3 className="font-semibold text-[var(--color-text-primary)]">{t("app.portfolio.performance", "en")}</h3>
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
                <h3 className="font-semibold text-[var(--color-text-primary)]">{t("app.portfolio.distribution", "en")}</h3>
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
