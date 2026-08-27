"use client";

import { useState, useEffect } from "react";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { TarotCard } from "@/components/ui/TarotCard";
import { SignalList } from "@/components/dashboard/SignalList";
import { AssetTable } from "@/components/dashboard/AssetTable";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { apiClient } from "@/lib/api";
import type { AssetRow, SignalRow } from "@/lib/dashboard-data";

export default function AlertsPage() {
  const [alertType, setAlertType] = useState("all");
  const [activeAlerts, setActiveAlerts] = useState<SignalRow[]>([]);
  const [watchlistAlerts, setWatchlistAlerts] = useState<AssetRow[]>([]);
  const [alertHistory, setAlertHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [alertStats, setAlertStats] = useState({ active: 0, buy: 0, sell: 0, hold: 0 });

  useEffect(() => {
    let active = true;

    async function loadAlerts() {
      setLoading(true);
      setError(null);
      setActiveAlerts([]);
      setWatchlistAlerts([]);
      setAlertHistory([]);

      try {
        const [summaryRes, watchlistsRes, notificationsRes] = await Promise.all([
          apiClient.get<{ status: string; data: any; summary: Record<string, number>; average_confidence: Record<string, number> }>("/analysis/signals-summary?min_confidence=0.7").catch(() => ({ data: { status: "error" } })),
          apiClient.get<any[]>("/watchlists").catch(() => ({ data: [] })),
          apiClient.get<any[]>("/notifications?limit=20").catch(() => ({ data: [] })),
        ]);

        if (!active) return;

        // Build alerts from signals
        const alerts: SignalRow[] = [];
        if (summaryRes.data?.status === "success") {
          const signalTypes = Object.entries(summaryRes.data?.summary ?? {})
            .filter(([, count]) => Number(count) > 0)
            .sort(([, a], [, b]) => Number(b) - Number(a));

          for (const [type, count] of signalTypes) {
            const typeSymbols = ((summaryRes.data as any)?.sample_symbols || {} as Record<string, string[]>)[type] || [];
            for (const symbol of typeSymbols.slice(0, 3)) {
              alerts.push({
                symbol,
                type: type as SignalRow["type"],
                confidence: summaryRes.data.average_confidence?.[type] ?? 50,
                model: "ML",
              });
            }
          }
        }
        setActiveAlerts(alerts.slice(0, 15));

        // Build watchlist alerts from default watchlist
        const watchlists = watchlistsRes.data || [];
        const defaultWatchlist = watchlists.find((w: any) => w.is_default);
        if (defaultWatchlist?.items?.length) {
          const symbols = defaultWatchlist.items.map((item: any) => item.asset?.symbol).filter(Boolean);
          if (symbols.length) {
            const pricesRes = await apiClient.get<any>(
              `/market/latest-prices?${symbols.map((s: string) => `symbols=${encodeURIComponent(s)}`).join("&")}`
            );
            const prices = pricesRes.data?.data || pricesRes.data || {};

            const watchAssets = defaultWatchlist.items
              .filter((item: any) => prices[item.asset?.symbol])
              .map((item: any) => ({
                symbol: item.asset.symbol,
                name: item.asset.name,
                market: item.asset.market as "TSE" | "OTC" | "BINANCE",
                price: prices[item.asset.symbol].price,
                changePct: prices[item.asset.symbol].change_pct,
              }));
            setWatchlistAlerts(watchAssets);
          }
        }

        // Build notification history
        const notifications = notificationsRes.data || [];
        const history = notifications
          .filter((n: any) => n.type === "ALERT" || n.type === "SIGNAL" || n.title?.includes("هشدار"))
          .slice(0, 10)
          .map((n: any) => ({
            time: formatTimeAgo(n.created_at),
            alert: n.title,
            type: n.extra?.signal_type || "INFO",
            status: n.read ? "اجرا شده" : "فعال",
          }));
        setAlertHistory(history);

        // Calculate stats
        const buyCount = alerts.filter(a => a.type === "BUY").length;
        const sellCount = alerts.filter(a => a.type === "SELL").length;
        const holdCount = alerts.filter(a => a.type === "HOLD").length;
        setAlertStats({
          active: alerts.length,
          buy: buyCount,
          sell: sellCount,
          hold: holdCount,
        });

      } catch (error) {
        if (active) setError("خطا در بارگذاری هشدارها. لطفاً دوباره تلاش کنید.");
      } finally {
        if (active) setLoading(false);
      }
    }

    loadAlerts();
    return () => { active = false; };
  }, []);

  const filteredAlerts = alertType === "all"
    ? activeAlerts
    : activeAlerts.filter(a => a.type === alertType);

  const formatTimeAgo = (dateStr: string): string => {
    const diff = Date.now() - new Date(dateStr).getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    if (minutes < 1) return "همین الان";
    if (minutes < 60) return `${minutes} دقیقه پیش`;
    if (hours < 24) return `${hours} ساعت پیش`;
    return `${days} روز پیش`;
  };

  if (loading) {
    return (
      <DashboardShell title="هشدارها">
        <div className="flex min-h-[40vh] items-center justify-center text-muted-foreground">
          در حال بارگذاری هشدارها...
        </div>
      </DashboardShell>
    );
  }

  if (error) {
    return (
      <DashboardShell title="هشدارها">
        <TarotCard title="خطا" className="max-w-md mx-auto">
          <p className="text-sm text-muted-foreground">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 rounded-xl bg-secondary text-secondary-foreground hover:bg-secondary/80 transition"
          >
            تلاش مجدد
          </button>
        </TarotCard>
      </DashboardShell>
    );
  }

  return (
    <DashboardShell title="هشدارها">
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        {/* Alert Controls */}
        <div className="lg:col-span-1 space-y-4">
          <TarotCard title="فیلتر هشدارها">
            <div className="space-y-2">
              {[
                { id: "all", label: "همه" },
                { id: "BUY", label: "خرید" },
                { id: "SELL", label: "فروش" },
                { id: "HOLD", label: "نگهداری" },
              ].map((type) => (
                <button
                  key={type.id}
                  onClick={() => setAlertType(type.id)}
                  className={`w-full text-right px-3 py-2 rounded-lg text-sm transition-colors ${alertType === type.id ? "bg-success text-success-foreground" : "hover:bg-muted/50"}`}
                >
                  {type.label}
                </button>
              ))}
            </div>
          </TarotCard>

          <TarotCard title="آمار هشدارها">
            <div className="space-y-3">
              {[
                { label: "هشدارهای فعال", value: alertStats.active },
                { label: "هشدار خرید", value: alertStats.buy },
                { label: "هشدار فروش", value: alertStats.sell },
                { label: "هشدار نگهداری", value: alertStats.hold },
              ].map((stat, i) => (
                <div key={i} className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">{stat.label}</span>
                  <span className="font-semibold">{stat.value}</span>
                </div>
              ))}
            </div>
          </TarotCard>
        </div>

        {/* Active Alerts */}
        <div className="lg:col-span-3 space-y-4">
          <TarotCard title={`هشدارهای فعال (${filteredAlerts.length})`}>
            {filteredAlerts.length > 0 ? (
              <SignalList signals={filteredAlerts} />
            ) : (
              <p className="text-muted-foreground py-4">هشدار فعالی وجود ندارد</p>
            )}
          </TarotCard>

          <TarotCard title="نمادهای واچ‌لیست">
            {watchlistAlerts.length > 0 ? (
              <AssetTable rows={watchlistAlerts} />
            ) : (
              <p className="text-muted-foreground py-4">واچ‌لیست خالی است</p>
            )}
          </TarotCard>

          <TarotCard title="تاریخچه هشدارها">
            {alertHistory.length > 0 ? (
              <div className="space-y-3">
                {alertHistory.map((alert, i) => (
                  <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                    <div className="flex items-center gap-3">
                      <span className="text-xs text-muted-foreground">{alert.time}</span>
                      <span className={`px-2 py-1 rounded text-xs font-medium ${alert.type === "BUY" ? "bg-success/20 text-success" : alert.type === "SELL" ? "bg-primary/20 text-primary" : "bg-accent/20 text-accent-foreground"}`}>
                        {alert.type}
                      </span>
                      <span className="font-medium">{alert.alert}</span>
                    </div>
                    <span className={`text-xs ${alert.status === "اجرا شده" ? "text-success" : "text-secondary"}`}>
                      {alert.status}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-muted-foreground py-4">تاریخچه هشدار خالی است</p>
            )}
          </TarotCard>
        </div>
      </div>
    </DashboardShell>
  );
}
