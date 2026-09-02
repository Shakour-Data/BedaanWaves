"use client";

import { useState, useEffect } from "react";
import { NewDashboardShell } from "@/components/layout/NewDashboardShell";
import { TarotCard } from "@/components/ui/TarotCard";
import { AssetTable } from "@/components/dashboard/AssetTable";
import { apiClient } from "@/lib/api";
import type { AssetRow } from "@/lib/dashboard-data";

import { t } from "@/lib/i18n";
import { useAuthStore } from "@/store/useAuthStore";

export default function AlertsPage() {
  
  const [watchlistAlerts, setWatchlistAlerts] = useState<AssetRow[]>([]);
  const [alertHistory, setAlertHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;

    async function loadAlerts() {
      setLoading(true);
      setWatchlistAlerts([]);
      setAlertHistory([]);

      try {
        const watchlistsRes = await apiClient.get<any[]>("/watchlists/watchlists");
        const notificationsRes = await apiClient.get<any[]>("/notifications/notifications?limit=20");

        if (!active) return;

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
                market: item.asset.market as "NASDAQ",
                price: prices[item.asset.symbol].price,
                changePct: prices[item.asset.symbol].change_pct }));
            setWatchlistAlerts(watchAssets);
          }
        }

        // Build notification history
        const notifications = notificationsRes.data || [];
        const history = notifications
          .filter((n: any) => n.type === "ALERT" || n.title?.includes("Alert"))
          .slice(0, 10)
          .map((n: any) => ({
            time: formatTimeAgo(n.created_at),
            alert: n.title,
            type: n.extra?.signal_type || "INFO",
            status: n.read ? t("app.alerts.status.executed", "en") : t("app.alerts.status.active", "en"),
            statusKey: n.read ? "executed" : "active" }));
        setAlertHistory(history);

      } catch (error) {
        // Handle error silently
      } finally {
        if (active) setLoading(false);
      }
    }

    loadAlerts();
    return () => { active = false; };
  }, ["en"]);

  const formatTimeAgo = (dateStr: string): string => {
    const diff = Date.now() - new Date(dateStr).getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    if (minutes < 1) return t("app.alerts.time.now", "en");
    if (minutes < 60) return `${minutes} ${t("app.alerts.time.minutes_ago", "en")}`;
    if (hours < 24) return `${hours} ${t("app.alerts.time.hours_ago", "en")}`;
    return `${days} ${t("app.alerts.time.days_ago", "en")}`;
  };

  if (loading) {
    return (
      <NewDashboardShell title={t("app.alerts.title", "en")}>
        <div className="flex min-h-[40vh] items-center justify-center text-muted-foreground">
          {t("app.alerts.loading", "en")}
        </div>
      </NewDashboardShell>
    );
  }

  return (
    <NewDashboardShell title={t("app.alerts.title", "en")}>
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        {/* Alert Controls */}
        <div className="lg:col-span-1 space-y-4">
          <TarotCard icon="Stats" title={t("app.alerts.stats", "en")}>
            <div className="space-y-3">
              {[
                { label: t("app.alerts.stats_labels.active", "en"), value: watchlistAlerts.length },
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
          <TarotCard icon="⭐" title={t("app.alerts.watchlist_symbols", "en")}>
            {watchlistAlerts.length > 0 ? (
              <AssetTable rows={watchlistAlerts} />
            ) : (
              <p className="text-muted-foreground py-4">{t("app.alerts.watchlist_empty", "en")}</p>
            )}
          </TarotCard>

          <TarotCard icon="📜" title={t("app.alerts.history", "en")}>
            {alertHistory.length > 0 ? (
              <div className="space-y-3">
                {alertHistory.map((alert, i) => (
                  <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                    <div className="flex items-center gap-3">
                      <span className="text-xs text-muted-foreground">{alert.time}</span>
                      <span className="font-medium">{alert.alert}</span>
                    </div>
                    <span className={`text-xs ${alert.statusKey === "executed" ? "text-success" : "text-secondary"}`}>
                      {alert.status}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-muted-foreground py-4">{t("app.alerts.history_empty", "en")}</p>
            )}
          </TarotCard>
        </div>
      </div>
    </NewDashboardShell>
  );
}
