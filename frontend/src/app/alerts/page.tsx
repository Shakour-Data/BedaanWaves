"use client";

import { useState, useEffect } from "react";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { TarotCard } from "@/components/ui/TarotCard";
import { SignalList } from "@/components/dashboard/SignalList";
import { AssetTable } from "@/components/dashboard/AssetTable";
import { apiClient } from "@/lib/api";
import type { AssetRow, SignalRow } from "@/lib/dashboard-data";

import { t } from "@/lib/i18n";
import { useAuthStore } from "@/store/useAuthStore";

export default function AlertsPage() {
  
  const [alertType, setAlertType] = useState("all");
  const [activeAlerts, setActiveAlerts] = useState<SignalRow[]>([]);
  const [watchlistAlerts, setWatchlistAlerts] = useState<AssetRow[]>([]);
  const [alertHistory, setAlertHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;

    async function loadAlerts() {
      setLoading(true);
      setActiveAlerts([]);
      setWatchlistAlerts([]);
      setAlertHistory([]);

      try {
        // Fetch all active signals as alerts
        const summaryRes = await apiClient.get<{
          status: string;
          data: any;
          summary: Record<string, number>;
          average_confidence: Record<string, number>;
        }>("/analysis/signals-summary?min_confidence=0.7");

        const watchlistsRes = await apiClient.get<any[]>("/watchlists/watchlists");
        const notificationsRes = await apiClient.get<any[]>("/notifications/notifications?limit=20");

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
                model: "ML" });
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
                market: item.asset.market as "NASDAQ",
                price: prices[item.asset.symbol].price,
                changePct: prices[item.asset.symbol].change_pct }));
            setWatchlistAlerts(watchAssets);
          }
        }

        // Build notification history
        const notifications = notificationsRes.data || [];
        const history = notifications
          .filter((n: any) => n.type === "ALERT" || n.type === "SIGNAL" || n.title?.includes("هشدار") || n.title?.includes("Alert"))
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

  const filteredAlerts = alertType === "all"
    ? activeAlerts
    : activeAlerts.filter(a => a.type === alertType);

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
      <DashboardShell title={t("app.alerts.title", "en")}>
        <div className="flex min-h-[40vh] items-center justify-center text-muted-foreground">
          {t("app.alerts.loading", "en")}
        </div>
      </DashboardShell>
    );
  }

  return (
    <DashboardShell title={t("app.alerts.title", "en")}>
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        {/* Alert Controls */}
        <div className="lg:col-span-1 space-y-4">
          <TarotCard icon="Search" title={t("app.alerts.filters", "en")}>
            <div className="space-y-2">
              {[
                { id: "all", label: t("app.alerts.types.all", "en") },
                { id: "BUY", label: t("app.alerts.types.buy", "en") },
                { id: "SELL", label: t("app.alerts.types.sell", "en") },
                { id: "HOLD", label: t("app.alerts.types.hold", "en") },
              ].map((type) => (
                <button
                  key={type.id}
                  onClick={() => setAlertType(type.id)}
                  className={`w-full text-right px-3 py-2 rounded-lg text-sm transition-colors ${alertType === type.id ? "bg-secondary text-[var(--color-text-primary)] font-bold shadow-sm" : "hover:bg-neutral/50 text-muted-foreground"}`}
                >
                  {type.label}
                </button>
              ))}
            </div>
          </TarotCard>

          <TarotCard icon="[Chart]" title={t("app.alerts.stats", "en")}>
            <div className="space-y-3">
              {[
                { label: t("app.alerts.stats_labels.active", "en"), value: filteredAlerts.length },
                { label: t("app.alerts.stats_labels.buy", "en"), value: activeAlerts.filter(a => a.type === "BUY").length },
                { label: t("app.alerts.stats_labels.sell", "en"), value: activeAlerts.filter(a => a.type === "SELL").length },
                { label: t("app.alerts.stats_labels.hold", "en"), value: activeAlerts.filter(a => a.type === "HOLD").length },
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
          <TarotCard icon="Alerts" title={`${t("app.alerts.active_alerts", "en")} (${filteredAlerts.length})`}>
            {filteredAlerts.length > 0 ? (
              <SignalList signals={filteredAlerts} />
            ) : (
              <p className="text-muted-foreground py-4">{t("app.alerts.empty", "en")}</p>
            )}
          </TarotCard>

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
                      <span className={`px-2 py-1 rounded text-xs font-bold ${alert.type === "BUY" ? "bg-success/20 text-success" : alert.type === "SELL" ? "bg-primary/20 text-primary" : "bg-accent/20 text-accent-foreground"}`}>
                        {t(`app.alerts.types.${alert.type.toLowerCase()}`, "en")}
                      </span>
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
    </DashboardShell>
  );
}
