"use client";

import { DashboardShell } from "@/components/layout/DashboardShell";
import { TarotCard } from "@/components/ui/TarotCard";
import { AssetTable } from "@/components/dashboard/AssetTable";
import type { AssetRow } from "@/lib/dashboard-data";

// Mock data for portfolio page
const portfolioHoldings: AssetRow[] = [
  { symbol: "شپنا", name: "پالایش نفت اصفهان", market: "TSE", price: 4120, changePct: 1.12 },
  { symbol: "فارس", name: "صنایع پتروشیمی خلیج فارس", market: "TSE", price: 9980, changePct: 0.64 },
  { symbol: "ETH", name: "Ethereum", market: "BINANCE", price: 3580, changePct: -2.21 },
  { symbol: "ونوک", name: "ونوک", market: "OTC", price: 1540, changePct: 5.04 },
];

const portfolioStats = [
  { label: "سود و زیان", value: "۱٬۲۳۴٬۵۶۰ رال", changePct: 12.5 },
  { label: "بازگردانده‌شده", value: "۸٬۹۱۰ میلیارد", changePct: 8.3 },
  { label: "دارایی‌های نقدی", value: "۲٬۱۲۰ میلیارد", changePct: -1.2 },
  { label: "نوی‌شر profitability", value: "۱۵.۷٪", changePct: 0 },
];

export default function PortfolioPage() {
  return (
    <DashboardShell title="پورتفولیو">
      <div className="flex flex-col gap-6">
        {/* Portfolio Summary */}
        <section className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {portfolioStats.map((stat, i) => (
            <TarotCard key={i} className="text-center">
              <span className="text-xs font-medium text-muted-foreground">{stat.label}</span>
              <span className="text-lg font-bold mt-1 block">{stat.value}</span>
              {stat.changePct !== undefined && (
                <span className={`text-xs mt-1 block ${stat.changePct >= 0 ? "text-success" : "text-primary"}`">
                  {stat.changePct >= 0 ? "▲" : "▼"} {Math.abs(stat.changePct)}%
                </span>
              )}
            </TarotCard>
          ))}
        </section>

        {/* Holdings */}
        <TarotCard icon="💼" title="دارایی‌های فعلی">
          <AssetTable rows={portfolioHoldings} />
        </TarotCard>

        {/* Performance Chart Placeholder */}
        <TarotCard icon="📈" title="عملکرد پورتفولیو">
          <div className="h-64 flex items-center justify-center text-muted-foreground">
            <p>نمودار عملکرد پورتفولیو (به‌زودی)</p>
          </div>
        </TarotCard>

        {/* Asset Allocation */}
        <TarotCard icon="🥧" title="توزیع دارایی‌ها">
          <div className="h-64 flex items-center justify-center text-muted-foreground">
            <p>نمودار پن‌دول توزیع دارایی‌ها (به‌زودی)</p>
          </div>
        </TarotCard>
      </div>
    </DashboardShell>
  );
}