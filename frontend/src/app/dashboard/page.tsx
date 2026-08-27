"use client";

import { useEffect, useState } from "react";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { TarotCard } from "@/components/ui/TarotCard";
import { StatCard } from "@/components/dashboard/StatCard";
import { AssetTable } from "@/components/dashboard/AssetTable";
import { SignalList } from "@/components/dashboard/SignalList";
import { NewsList } from "@/components/dashboard/NewsList";
import { LineChart } from "@/components/charts/LineChart";
import { fetchDashboardData, type DashboardData } from "@/lib/api/dashboard";

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    fetchDashboardData()
      .then((d) => {
        if (active) setData(d);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  if (loading || !data) {
    return (
      <DashboardShell title="داشبورد">
        <div className="flex min-h-[40vh] items-center justify-center text-muted-foreground">
          در حال بارگذاری داشبورد...
        </div>
      </DashboardShell>
    );
  }

  return (
    <DashboardShell title="داشبورد">
      <div className="flex flex-col gap-4">
        {data.live ? (
          <div className="rounded-xl bg-success/10 px-3 py-2 text-sm text-success">
            ● داده‌های زنده از بک‌اند دریافت شد
          </div>
        ) : (
          <div className="rounded-xl bg-accent/30 px-3 py-2 text-sm text-accent-foreground">
            ● داده‌های نمونه (بک‌اند در دسترس نیست)
          </div>
        )}

        {/* Market Stats */}
        <section className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          {data.marketStats.map((s) => (
            <StatCard key={s.label} stat={s} />
          ))}
        </section>

        {/* Market Trend */}
        <TarotCard title="روند بازار">
          {data.marketStats.length > 0 ? (
            <LineChart
              data={data.marketStats.map((s) => ({ time: s.label, value: Number(s.value.replace(/[^\d.-]/g, "")) || 0 }))}
              height={280}
            />
          ) : (
            <div className="flex min-h-[200px] items-center justify-center text-muted-foreground">
              داده‌ای برای نمایش موجود نیست
            </div>
          )}
        </TarotCard>

        {/* Top Movers + Watchlist */}
        <section className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          <TarotCard title="نمادهای پرتغول" className="lg:col-span-2">
            <AssetTable rows={data.topMovers} />
          </TarotCard>
          <TarotCard title="واچ‌لیست">
            <AssetTable rows={data.watchlist} />
          </TarotCard>
        </section>

        {/* ML Signals + News */}
        <section className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          <TarotCard title="سیگنال‌های هوش مصنوعی" className="lg:col-span-2">
            <SignalList signals={data.signals} />
          </TarotCard>
          <TarotCard title="آخرین اخبار">
            <NewsList items={data.news} />
          </TarotCard>
        </section>
      </div>
    </DashboardShell>
  );
}
