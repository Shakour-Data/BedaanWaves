"use client";

import { useEffect, useState } from "react";
import { TarotCard } from "@/components/ui/TarotCard";
import { StatCard } from "@/components/dashboard/StatCard";
import { AssetTable } from "@/components/dashboard/AssetTable";
import { SignalList } from "@/components/dashboard/SignalList";
import { NewsList } from "@/components/dashboard/NewsList";
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
      <div className="flex min-h-[40vh] items-center justify-center text-muted-foreground">
        در حال بارگذاری داشبورد…
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      {data.live ? (
        <p className="rounded-xl bg-success/10 px-3 py-2 text-sm text-success">
          ● داده‌های زنده از بک‌اند دریافت شد
        </p>
      ) : (
        <p className="rounded-xl bg-accent/30 px-3 py-2 text-sm text-accent-foreground">
          ● نمایش داده‌های نمایشی (بک‌اند در دسترس نیست)
        </p>
      )}

      {/* آمار بازار */}
      <section className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {data.marketStats.map((s) => (
          <StatCard key={s.label} stat={s} />
        ))}
      </section>

      {/* برترین حرکات + واچ‌لیست */}
      <section className="grid grid-cols-1 gap-3 lg:grid-cols-3">
        <TarotCard icon="📈" title="برترین حرکات بازار" className="lg:col-span-2">
          <AssetTable rows={data.topMovers} />
        </TarotCard>
        <TarotCard icon="⭐" title="واچ‌لیست">
          <AssetTable rows={data.watchlist} />
        </TarotCard>
      </section>

      {/* سیگنال‌های ML + اخبار */}
      <section className="grid grid-cols-1 gap-3 lg:grid-cols-3">
        <TarotCard icon="🔮" title="سیگنال‌های هوشمند" className="lg:col-span-2">
          <SignalList signals={data.signals} />
        </TarotCard>
        <TarotCard icon="📰" title="آخرین اخبار">
          <NewsList items={data.news} />
        </TarotCard>
      </section>
    </div>
  );
}
