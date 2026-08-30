"use client";

import { useEffect, useState, useCallback } from "react";
import { NewDashboardShell } from "@/components/layout/NewDashboardShell";
import { TarotCard } from "@/components/ui/TarotCard";
import { AssetTable } from "@/components/dashboard/AssetTable";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { PageLoading } from "@/components/ui/PageLoading";
import { StatCard } from "@/components/dashboard/StatCard";
import { apiClient } from "@/lib/api";
import { useAuthStore } from "@/store/useAuthStore";
import type { AssetRow } from "@/lib/dashboard-data";

import { t } from "@/lib/i18n";

export default function PortfolioPage() {
  const { user } = useAuthStore();
  const [holdings, setHoldings] = useState<AssetRow[]>([]);
  const [stats, setStats] = useState<Array<{ label: string; value: string; changePct?: number }>>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadPortfolio = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const portfoliosRes = await apiClient.get<any[]>("/portfolio/");
      const portfolios = portfoliosRes.data;
      
      if (portfolios && portfolios.length > 0) {
        const portfolioId = portfolios[0].id;
        
        const holdingsRes = await apiClient.get<any[]>(`/portfolio/${portfolioId}/holdings`);
        const holdingsData = holdingsRes.data;
        
        const symbolsRes = await apiClient.get<any[]>("/market/symbols");
        const allAssets = symbolsRes.data;
        const assetMap = new Map(allAssets.map((a: any) => [a.id, a]));
        
        if (holdingsData.length > 0) {
          const symbols = holdingsData.map((h: any) => assetMap.get(h.asset_id)?.symbol).filter(Boolean);
          const pricesRes = await apiClient.get<any>(
            `/market/latest-prices?${symbols.map((s: string) => `symbols=${encodeURIComponent(s)}`).join("&")}`
          );
          
          const prices = pricesRes.data?.data || {};
          
          const enrichedHoldings: AssetRow[] = holdingsData.map((h: any) => {
            const asset = assetMap.get(h.asset_id);
            return {
              symbol: asset?.symbol || "Unknown",
              name: asset?.name || "Unknown",
              market: asset?.market || "NASDAQ",
              price: prices[asset?.symbol]?.price ?? h.entry_price ?? 0,
              changePct: prices[asset?.symbol]?.change_pct ?? 0,
              quantity: Number(h.quantity),
              avg_price: Number(h.entry_price) };
          });
          
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
    } catch (err) {
      setError(t("app.portfolio.error_loading", "en"));
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    if (user) {
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
            <StatCard key={i} stat={{ label: stat.label, value: stat.value, changePct: stat.changePct }} />
          ))}
        </section>

        {/* Holdings */}
        <TarotCard icon="💼" title={t("app.portfolio.current_holdings", "en")}>
          {holdings.length > 0 ? (
            <AssetTable rows={holdings} />
          ) : (
            <div className="flex flex-col items-center justify-center py-12 text-muted-foreground border-2 border-dashed border-border rounded-xl">
              <div className="text-4xl mb-4">📭</div>
              <p className="text-lg font-bold text-foreground mb-2">{t("app.portfolio.empty_title", "en")}</p>
              <p className="text-sm mb-6 max-w-xs text-center">{t("app.portfolio.empty_desc", "en")}</p>
              <PrimaryButton onClick={() => window.location.href = "/stocks"} size="lg">
                {t("app.portfolio.view_stocks", "en")}
              </PrimaryButton>
            </div>
          )}
        </TarotCard>

        {/* Performance & Distribution - Improved UI instead of Coming Soon */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <TarotCard icon="📈" title={t("app.portfolio.performance", "en")}>
            <div className="h-64 flex flex-col items-center justify-center text-muted-foreground bg-neutral/20 rounded-xl border border-border/40 relative overflow-hidden group">
              <div className="text-4xl mb-4 opacity-20 group-hover:scale-110 transition-transform duration-500">[Chart]</div>
              <p className="text-sm font-medium z-10">{t("app.portfolio.coming_soon", "en")}</p>
              <div className="absolute inset-0 bg-gradient-to-t from-background/80 to-transparent flex items-end justify-center pb-4 opacity-0 group-hover:opacity-100 transition-opacity">
                <span className="text-xs px-3 py-1 bg-secondary/10 text-secondary rounded-full border border-secondary/20">
                  {false ? "در حال توسعه..." : "Under Development..."}
                </span>
              </div>
            </div>
          </TarotCard>

          <TarotCard icon="🥧" title={t("app.portfolio.distribution", "en")}>
            <div className="h-64 flex flex-col items-center justify-center text-muted-foreground bg-neutral/20 rounded-xl border border-border/40 relative overflow-hidden group">
              <div className="text-4xl mb-4 opacity-20 group-hover:scale-110 transition-transform duration-500">💹</div>
              <p className="text-sm font-medium z-10">{t("app.portfolio.coming_soon", "en")}</p>
              <div className="absolute inset-0 bg-gradient-to-t from-background/80 to-transparent flex items-end justify-center pb-4 opacity-0 group-hover:opacity-100 transition-opacity">
                <span className="text-xs px-3 py-1 bg-secondary/10 text-secondary rounded-full border border-secondary/20">
                  {false ? "در حال توسعه..." : "Under Development..."}
                </span>
              </div>
            </div>
          </TarotCard>
        </div>
      </div>
    </NewDashboardShell>
  );
}
