"use client";

import { useEffect, useState } from "react";
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
      <div className="flex min-h-[40vh] items-center justify-center text-muted-foreground">
        Loading dashboard...
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      {data.live ? (
        <p className="rounded-xl bg-success/10 px-3 py-2 text-sm text-success">
          ● Live data received from backend
        </p>
      ) : (
        <p className="rounded-xl bg-accent/30 px-3 py-2 text-sm text-accent-foreground">
          ● Showing sample data (backend unavailable)
        </p>
      )}

      {/* Market Stats */}
      <section className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {data.marketStats.map((s) => (
          <StatCard key={s.label} stat={s} />
        ))}
      </section>

      {/* Market Trend */}
      <TarotCard icon="" title="روند بازار">
        <LineChart
          data={[
            { time: "09:00", value: 12500 },
            { time: "10:00", value: 12580 },
            { time: "11:00", value: 12620 },
            { time: "12:00", value: 12590 },
            { time: "13:00", value: 12750 },
            { time: "14:00", value: 12880 },
            { time: "15:00", value: 12840 },
            { time: "16:00", value: 12950 },
          ]}
          height={280}
        />
      </TarotCard>

      {/* Top Movers + Watchlist */}
      <section className="grid grid-cols-1 gap-3 lg:grid-cols-3">
        <TarotCard icon="" title="Top Movers" className="lg:col-span-2">
          <AssetTable rows={data.topMovers} />
        </TarotCard>
        <TarotCard icon="⭐" title="Watchlist">
          <AssetTable rows={data.watchlist} />
        </TarotCard>
      </section>

      {/* ML Signals + News */}
      <section className="grid grid-cols-1 gap-3 lg:grid-cols-3">
        <TarotCard icon="" title="AI Signals" className="lg:col-span-2">
          <SignalList signals={data.signals} />
        </TarotCard>
        <TarotCard icon="" title="Latest News">
          <NewsList items={data.news} />
        </TarotCard>
      </section>
    </div>
  );
}

