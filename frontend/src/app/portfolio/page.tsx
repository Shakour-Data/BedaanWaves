"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { TarotCard } from "@/components/ui/TarotCard";
import { AssetTable } from "@/components/dashboard/AssetTable";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { apiClient } from "@/lib/api";
import { useAuthStore } from "@/store/useAuthStore";
import type { AssetRow } from "@/lib/dashboard-data";

export default function PortfolioPage() {
  const router = useRouter();
  const { user } = useAuthStore();
  const [holdings, setHoldings] = useState<AssetRow[]>([]);
  const [stats, setStats] = useState<Array<{ label: string; value: string; changePct?: number }>>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function loadPortfolio() {
      setLoading(true);
      setError(null);
      try {
        // Fetch user's portfolios
        const portfoliosRes = await apiClient.get<any>("/portfolio/");
        
        if (!active) return;
        
        const portfolios = Array.isArray(portfoliosRes.data) ? portfoliosRes.data : [];
        
        if (portfolios.length === 0) {
          setHoldings([]);
          setStats([
            { label: "مجموع ارزش پورتفولیو", value: "۰ رال", changePct: 0 },
            { label: "سود/زیان کلی", value: "۰ رال", changePct: 0 },
            { label: "تعداد نمادها", value: "۰", changePct: 0 },
            { label: "بازگشت روزانه", value: "۰٪", changePct: 0 },
          ]);
          return;
        }
        
        // Get holdings from first portfolio
        const firstPortfolio = portfolios[0];
        const holdingsRes = await apiClient.get<any>(`/portfolio/${firstPortfolio.id}/holdings`);
        const holdingsData = Array.isArray(holdingsRes.data) ? holdingsRes.data : [];
        
        if (holdingsData.length > 0) {
          const symbols = holdingsData.map((h: any) => h.asset?.symbol || h.symbol).filter(Boolean);
          const pricesRes = await apiClient.get<any>(
            `/market/latest-prices?${symbols.map((s: string) => `symbols=${encodeURIComponent(s)}`).join("&")}`
          );
          
          const prices = pricesRes.data?.data || {};
          
          const enrichedHoldings: AssetRow[] = holdingsData.map((h: any) => ({
            symbol: h.asset?.symbol || h.symbol,
            name: h.asset?.name || h.name || "",
            market: (h.asset?.market || h.market || "NASDAQ") as AssetRow["market"],
            price: prices[h.asset?.symbol || h.symbol]?.price ?? h.entry_price ?? 0,
            changePct: prices[h.asset?.symbol || h.symbol]?.change_pct ?? 0,
          }));
          
          setHoldings(enrichedHoldings);
          
          const totalValue = enrichedHoldings.reduce((sum: number, h: AssetRow) => sum + (h.price * ((h as any).quantity ?? 1)), 0);
          const totalPnL = enrichedHoldings.reduce((sum: number, h: AssetRow) => {
            const quantity = ((h as any).quantity ?? 1);
            const entryPrice = ((h as any).entry_price ?? h.price);
            return sum + ((h.price - entryPrice) * quantity);
          }, 0);
          const totalReturnPct = totalValue > 0 ? (totalPnL / (totalValue - totalPnL || 1)) * 100 : 0;
          
          setStats([
            { label: "مجموع ارزش پورتفولیو", value: `${totalValue.toLocaleString("fa-IR")} $`, changePct: totalReturnPct },
            { label: "سود/زیان کلی", value: `${totalPnL.toLocaleString("fa-IR")} $`, changePct: totalReturnPct },
            { label: "تعداد نمادها", value: String(enrichedHoldings.length), changePct: 0 },
            { label: "بازگشت روزانه", value: `${(totalReturnPct / 30).toFixed(2)}٪`, changePct: totalReturnPct / 30 },
          ]);
        } else {
          setHoldings([]);
          setStats([
            { label: "مجموع ارزش پورتفولیو", value: "۰ $", changePct: 0 },
            { label: "سود/زیان کلی", value: "۰ $", changePct: 0 },
            { label: "تعداد نمادها", value: "۰", changePct: 0 },
            { label: "بازگشت روزانه", value: "۰٪", changePct: 0 },
          ]);
        }
      } catch (err) {
        if (active) setError("خطا در بارگذاری پورتفولیو. مطمئن شوید بک‌اند در دسترس است و لاگین کرده‌ید.");
      } finally {
        if (active) setLoading(false);
      }
    }

    if (user) {
      loadPortfolio();
    } else {
      setLoading(false);
      setError("لطفاً ابتدا وارد شوید");
    }

    return () => { active = false; };
  }, [user]);

  if (loading) {
    return (
      <DashboardShell title="پورتفولیو">
        <div className="flex min-h-[40vh] items-center justify-center text-muted-foreground">
          در حال بارگذاری پورتفولیو...
        </div>
      </DashboardShell>
    );
  }

  if (error) {
    return (
      <DashboardShell title="پورتفولیو">
        <TarotCard icon="️" title="خطا" className="max-w-md mx-auto">
          <p className="text-sm text-muted-foreground">{error}</p>
        </TarotCard>
      </DashboardShell>
    );
  }

  return (
    <DashboardShell title="پورتفولیو">
      <div className="flex flex-col gap-6">
        {/* Portfolio Summary */}
        <section className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {stats.map((stat, i) => (
            <TarotCard key={i} className="text-center">
              <span className="text-xs font-medium text-muted-foreground">{stat.label}</span>
              <span className="text-lg font-bold mt-1 block">{stat.value}</span>
              {stat.changePct !== undefined && (
                <span className={`text-xs mt-1 block ${stat.changePct >= 0 ? "text-success" : "text-primary"}`}>
                  {stat.changePct >= 0 ? "▲" : "▼"} {Math.abs(stat.changePct).toFixed(2)}%
                </span>
              )}
            </TarotCard>
          ))}
        </section>

        {/* Holdings */}
        <TarotCard icon="" title="دارایی‌های فعلی">
          {holdings.length > 0 ? (
            <AssetTable rows={holdings} />
          ) : (
            <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
              <p className="text-lg mb-2">پورتفولیو شما خالی است</p>
              <PrimaryButton onClick={() => router.push("/stocks")}>
                افزودن نماد به پورتفولیو
              </PrimaryButton>
            </div>
          )}
        </TarotCard>

        {/* Performance Chart Placeholder */}
        <TarotCard icon="" title="عملکرد پورتفولیو">
          <div className="h-64 flex items-center justify-center text-muted-foreground">
            <p>نمودار عملکرد پورتفولیو به‌زودی اضافه می‌شود</p>
          </div>
        </TarotCard>

        {/* Asset Allocation */}
        <TarotCard icon="" title="توزیع دارایی‌ها">
          <div className="h-64 flex items-center justify-center text-muted-foreground">
            <p>نمودار توزیع دارایی‌ها به‌زودی اضافه می‌شود</p>
          </div>
        </TarotCard>
      </div>
    </DashboardShell>
  );
}
