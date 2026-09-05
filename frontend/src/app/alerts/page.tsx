"use client";

import { useState, useEffect } from "react";
import { NewDashboardShell } from "@/components/layout/NewDashboardShell";
import { AssetTable } from "@/components/dashboard/AssetTable";
import { apiClient } from "@/lib/api";
import type { AssetRow } from "@/lib/dashboard-data";

import { t } from "@/lib/i18n";
import { formatTimeAgo } from "@/lib/utils";

interface WatchlistItem {
  asset?: {
    symbol?: string;
    name?: string;
    market?: string;
  };
}

interface Watchlist {
  is_default?: boolean;
  items?: WatchlistItem[];
}

interface Notification {
  type?: string;
  title?: string;
  created_at?: string;
  extra?: { signal_type?: string };
  read?: boolean;
}

interface PriceMap {
  [symbol: string]: {
    price?: number;
    change_pct?: number;
  };
}

export default function AlertsPage() {
  
  const [watchlistAlerts, setWatchlistAlerts] = useState<AssetRow[]>([]);
  const [alertHistory, setAlertHistory] = useState<Array<{
    time: string;
    alert: string;
    type: string;
    status: string;
    statusKey: string;
  }>>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;

    async function loadAlerts() {
      setLoading(true);
      setWatchlistAlerts([]);
      setAlertHistory([]);

      try {
        const watchlistsRes = await apiClient.get<Watchlist[]>("/watchlists/watchlists");
        const notificationsRes = await apiClient.get<Notification[]>("/notifications/notifications?limit=20");

        if (!active) return;

        const watchlists = watchlistsRes.data || [];
        const defaultWatchlist = watchlists.find((w) => w.is_default);
        if (defaultWatchlist?.items?.length) {
          const symbols = defaultWatchlist.items
            .map((item) => item.asset?.symbol)
            .filter((symbol): symbol is string => Boolean(symbol));
          if (symbols.length) {
            const pricesRes = await apiClient.get<{ data: PriceMap }>(
              `/market/latest-prices?${symbols.map((s) => `symbols=${encodeURIComponent(s)}`).join("&")}`
            );
            const prices = pricesRes.data?.data || {};

            const watchAssets: AssetRow[] = defaultWatchlist.items
              .filter((item): item is WatchlistItem & { asset: NonNullable<WatchlistItem["asset"]> } => {
                const sym = item.asset?.symbol;
                return Boolean(sym && prices[sym]);
              })
              .map((item) => {
                const sym = item.asset.symbol;
                const priceData = prices[sym];
                return {
                  symbol: sym,
                  name: item.asset.name,
                  market: item.asset.market as "NASDAQ",
                  price: priceData.price ?? 0,
                  changePct: priceData.change_pct ?? 0,
                };
              });
            setWatchlistAlerts(watchAssets);
          }
        }

        const notifications = notificationsRes.data || [];
        const history = notifications
          .filter((n) => n.type === "ALERT" || n.title?.includes("Alert"))
          .slice(0, 10)
          .map((n) => ({
            time: formatTimeAgo(n.created_at as string),
            alert: n.title as string,
            type: n.extra?.signal_type || "INFO",
            status: n.read ? t("app.alerts.status.executed", "en") : t("app.alerts.status.active", "en"),
            statusKey: n.read ? "executed" : "active",
          }));
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
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 animate-in fade-in duration-500">
        {/* Alert Controls */}
        <div className="lg:col-span-1 space-y-4">
          <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5 shadow-sm">
            <div className="flex items-center gap-3 mb-4">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--color-primary-soft)] text-[var(--color-primary)]">
                <span className="text-sm font-bold">S</span>
              </div>
              <h3 className="font-semibold text-[var(--color-text-primary)] text-sm">{t("app.alerts.stats", "en")}</h3>
            </div>
            <div className="space-y-3">
              {[
                { label: t("app.alerts.stats_labels.active", "en"), value: watchlistAlerts.length },
              ].map((stat, i) => (
                <div key={i} className="flex justify-between items-center">
                  <span className="text-sm text-[var(--color-text-secondary)]">{stat.label}</span>
                  <span className="font-semibold text-[var(--color-text-primary)]">{stat.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Active Alerts */}
        <div className="lg:col-span-3 space-y-4">
          <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-sm">
            <div className="flex items-center gap-3 p-6 border-b border-[var(--color-border)]">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--color-primary-soft)] text-[var(--color-primary)]">
                <span className="text-sm">⭐</span>
              </div>
              <div>
                <h3 className="font-semibold text-[var(--color-text-primary)] text-sm">{t("app.alerts.watchlist_symbols", "en")}</h3>
                <p className="text-xs text-[var(--color-text-muted)]">Stocks in your watchlist with active alerts</p>
              </div>
            </div>
            <div className="p-6">
              {watchlistAlerts.length > 0 ? (
                <AssetTable rows={watchlistAlerts} />
              ) : (
                <p className="text-[var(--color-text-muted)] py-8 text-center text-sm">{t("app.alerts.watchlist_empty", "en")}</p>
              )}
            </div>
          </div>

          <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-sm">
            <div className="flex items-center gap-3 p-6 border-b border-[var(--color-border)]">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--color-primary-soft)] text-[var(--color-primary)]">
                <span className="text-sm">📜</span>
              </div>
              <div>
                <h3 className="font-semibold text-[var(--color-text-primary)] text-sm">{t("app.alerts.history", "en")}</h3>
                <p className="text-xs text-[var(--color-text-muted)]">Recent alert history</p>
              </div>
            </div>
            <div className="p-6">
              {alertHistory.length > 0 ? (
                <div className="space-y-3">
                  {alertHistory.map((alert, i) => (
                    <div key={i} className="flex items-center justify-between p-3 rounded-xl bg-[var(--color-background)]/50 border border-[var(--color-border)]/50">
                      <div className="flex items-center gap-3">
                        <span className="text-xs text-[var(--color-text-muted)]">{alert.time}</span>
                        <span className="font-medium text-sm text-[var(--color-text-primary)]">{alert.alert}</span>
                      </div>
                      <span className={`text-xs font-medium px-2.5 py-1 rounded-full ${alert.statusKey === "executed" ? "bg-[var(--color-success-light)] text-[var(--color-success)]" : "bg-[var(--color-primary-soft)] text-[var(--color-primary)]"}`}>
                        {alert.status}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-[var(--color-text-muted)] py-8 text-center text-sm">{t("app.alerts.history_empty", "en")}</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </NewDashboardShell>
  );
}
