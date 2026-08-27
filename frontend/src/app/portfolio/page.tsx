"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { TarotCard } from "@/components/ui/TarotCard";
import { AssetTable } from "@/components/dashboard/AssetTable";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { LineChart } from "@/components/charts/LineChart";
import { SpiderChart } from "@/components/charts/SpiderChart";
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
  const [performanceData, setPerformanceData] = useState<{ time: string; value: number }[]>([]);
  const [allocationData, setAllocationData] = useState<{ labels: string[]; values: number[] }>({ labels: [], values: [] });

  useEffect(() => {
    let active = true;

    async function loadPortfolio() {
      setLoading(true);
      setError(null);
      try {
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
          setPerformanceData([]);
          setAllocationData({ labels: [], values: [] });
          return;
        }

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

          const totalValue = enrichedHoldings.reduce((sum: number, h: AssetRow) => sum + (h.price * (((h as any).quantity ?? 1))), 0);
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

          // Performance data from holdings
          const perfData = enrichedHoldings.map((h, i) => ({
            time: h.symbol,
            value: h.price,
          }));
          setPerformanceData(perfData.length > 0 ? perfData : []);

          // Allocation data
          const labels = enrichedHoldings.map((h) => h.symbol);
          const values = enrichedHoldings.map((h) => h.price);
          setAllocationData({ labels, values });
        } else {
          setHoldings([]);
          setStats([
            { label: "مجموع ارزش پورتفولیو", value: "۰ $", changePct: 0 },
            { label: "سود/زیان کلی", value: "۰ $", changePct: 0 },
            { label: "تعداد نمادها", value: "۰", changePct: 0 },
            { label: "بازگشت روزانه", value: "۰٪", changePct: 0 },
          ]);
          setPerformanceData([]);
          setAllocationData({ labels: [], values: [] });
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
        <TarotCard title="خطا" className="max-w-md mx-auto">
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
                <span className={`text-xs mt-1 block ${stat.changePct >= 0 ? "text-success" : "text-error"}`}>
                  {stat.changePct >= 0 ? "▲" : "▼"} {Math.abs(stat.changePct).toFixed(2)}%
                </span>
              )}
            </TarotCard>
          ))}
        </section>

        {/* Holdings */}
        <TarotCard title="دارایی‌های فعلی">
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

        {/* Performance Chart */}
        <TarotCard title="عملکرد پورتفولیو">
          {performanceData.length > 0 ? (
            <LineChart data={performanceData} height={320} />
          ) : (
            <div className="flex min-h-[200px] items-center justify-center text-muted-foreground">
              داده‌ای برای نمایش عملکرد موجود نیست
            </div>
          )}
        </TarotCard>

        {/* Asset Allocation */}
        <TarotCard title="توزیع دارایی‌ها">
          {allocationData.labels.length > 0 ? (
            <SpiderChart
              labels={allocationData.labels}
              values={allocationData.values}
              max={Math.max(...allocationData.values, 100)}
              height={320}
            />
          ) : (
            <div className="flex min-h-[200px] items-center justify-center text-muted-foreground">
              داده‌ای برای نمایش توزیع موجود نیست
            </div>
          )}
        </TarotCard>
      </div>
    </DashboardShell>
  );
}
