"use client";

import { useEffect, useState } from "react";
import { TarotCard } from "@/components/ui/TarotCard";
import { StatCard } from "@/components/dashboard/StatCard";
import { AssetTable } from "@/components/dashboard/AssetTable";
import { SignalList } from "@/components/dashboard/SignalList";
import { NewsList } from "@/components/dashboard/NewsList";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { PageLoading } from "@/components/ui/PageLoading";
import { fetchDashboardData, type DashboardData } from "@/lib/api/dashboard";
import { cn } from "@/lib/cn";

import { t } from "@/lib/i18n";
import { useAuthStore } from "@/store/useAuthStore";

export default function DashboardPage() {
  const { currentLang } = useAuthStore();
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
      <DashboardShell title={t("app.dashboard.title", currentLang)}>
        <PageLoading />
      </DashboardShell>
    );
  }

  return (
    <DashboardShell title={t("app.dashboard.title", currentLang)}>
      <div className="flex flex-col gap-6 animate-in fade-in duration-500">
        <div className={cn(
          "rounded-xl px-4 py-3 text-sm flex items-center gap-2 border",
          data.live 
            ? "bg-success/10 text-success border-success/20" 
            : "bg-accent/10 text-accent-foreground border-accent/20"
        )}>
          <span className={cn("h-2 w-2 rounded-full", data.live ? "bg-success" : "bg-accent")} />
          {data.live ? t("app.dashboard.live_connected", currentLang) : t("app.dashboard.live_disconnected", currentLang)}
        </div>

        {/* Market Stats */}
        <section className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {data.marketStats.map((s) => (
            <StatCard key={s.label} stat={s} />
          ))}
        </section>

        {/* Top Movers + Watchlist */}
        <section className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          <TarotCard icon="📈" title={t("app.dashboard.top_movers", currentLang)} className="lg:col-span-2">
            <AssetTable rows={data.topMovers} />
          </TarotCard>
          <TarotCard icon="⭐" title={t("app.dashboard.watchlist", currentLang)}>
            <AssetTable rows={data.watchlist} />
          </TarotCard>
        </section>

        {/* ML Signals + News */}
        <section className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          <TarotCard icon="🤖" title={t("app.dashboard.ai_signals", currentLang)} className="lg:col-span-2">
            <SignalList signals={data.signals} />
          </TarotCard>
          <TarotCard icon="📰" title={t("app.dashboard.latest_news", currentLang)}>
            <NewsList items={data.news} />
          </TarotCard>
        </section>
      </div>
    </DashboardShell>
  );
}

