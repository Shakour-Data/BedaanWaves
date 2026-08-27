"use client";

/**
 * Stock listing page: Fetches symbols from `GET /market/symbols` and latest
 * prices from `GET /market/latest-prices`. Each row links to `/stocks/[symbol]`.
 */

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { PageLoading } from "@/components/ui/PageLoading";
import { Input } from "@/components/ui/input";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { cn } from "@/lib/cn";
import { t } from "@/lib/i18n";
import { useAuthStore } from "@/store/useAuthStore";

import { TarotCard } from "@/components/ui/TarotCard";
import { ChangeBadge } from "@/components/dashboard/StatCard";
import {
  fetchSymbols,
  fetchLatestPrices,
  type Asset,
  type LatestPrice,
  type Market,
} from "@/lib/api/stocks";

const MARKET_LABEL: Record<Market, string> = {
  TSE: "بورس",
  OTC: "فرابورس",
  BINANCE: "کریپتو",
  KRAKEN: "کریپتو",
  COINBASE: "کریپتو",
  NYSE: "NYSE",
  NASDAQ: "NASDAQ",
};

type MarketFilter = "ALL" | "NASDAQ";

const FILTERS: { key: MarketFilter; label: string }[] = [
  { key: "ALL", label: "همه" },
  { key: "NASDAQ", label: "Nasdaq" },
];

function matchesFilter(asset: Asset, filter: MarketFilter): boolean {
  if (filter === "ALL") return true;
  return asset.market === filter;
}

export default function StocksPage() {
  const { currentLang } = useAuthStore();
  const [assets, setAssets] = useState<Asset[] | null>(null);
  const [prices, setPrices] = useState<Record<string, LatestPrice>>({});
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<MarketFilter>("NASDAQ");
  const [search, setSearch] = useState("");

  const FILTERS: { key: MarketFilter; label: string }[] = [
    { key: "ALL", label: currentLang === "fa" ? "همه" : "All" },
    { key: "NASDAQ", label: "Nasdaq" },
  ];

  const MARKET_LABEL: Record<Market, string> = {
    TSE: t("app.stocks.markets.tse", currentLang),
    OTC: t("app.stocks.markets.otc", currentLang),
    BINANCE: t("app.stocks.markets.binance", currentLang),
    KRAKEN: t("app.stocks.markets.kraken", currentLang),
    COINBASE: t("app.stocks.markets.coinbase", currentLang),
    NYSE: t("app.stocks.markets.nyse", currentLang),
    NASDAQ: t("app.stocks.markets.nasdaq", currentLang),
  };

  useEffect(() => {
    let active = true;

    async function load() {
      setLoading(true);
      try {
        const list = await fetchSymbols({ market: "NASDAQ", limit: 1000 });
        if (!active) return;
        setAssets(list);
        setError(null);
        const map = await fetchLatestPrices(list.map((a) => a.symbol)).catch(() => ({}));
        if (active) setPrices(map);
      } catch (e: unknown) {
        if (active) setError(e instanceof Error ? e.message : "Error fetching symbols");
      } finally {
        if (active) setLoading(false);
      }
    }

    load();

    return () => {
      active = false;
    };
  }, []);

  const filtered = useMemo(() => {
    if (!assets) return [];
    const q = search.trim().toLowerCase();
    return assets
      .filter((a) => matchesFilter(a, filter))
      .filter(
        (a) =>
          !q ||
          a.symbol.toLowerCase().includes(q) ||
          a.name.toLowerCase().includes(q),
      );
  }, [assets, filter, search]);

  if (loading) {
    return (
      <DashboardShell title={t("app.stocks.title", currentLang)}>
        <PageLoading />
      </DashboardShell>
    );
  }

  if (error || !assets) {
    return (
      <DashboardShell title={t("app.stocks.title", currentLang)}>
        <TarotCard icon="⚠️" title={t("app.stocks.error_title", currentLang)} className="max-w-md mx-auto border-error/20 bg-error/5">
          <div className="py-6 text-center">
            <p className="text-sm text-error font-medium mb-4">
              {t("app.stocks.error_desc", currentLang)}
            </p>
            <PrimaryButton onClick={() => window.location.reload()} variant="outline" size="sm">
              {t("app.stocks.retry", currentLang)}
            </PrimaryButton>
            {error ? <p className="mt-4 text-[10px] text-muted-foreground break-all">{error}</p> : null}
          </div>
        </TarotCard>
      </DashboardShell>
    );
  }

  return (
    <DashboardShell title={t("app.stocks.title", currentLang)}>
      <div className="flex flex-col gap-6 animate-in fade-in duration-500">
        {/* Filters + Search */}
        <section className="flex flex-col sm:flex-row items-center gap-4 bg-surface p-4 rounded-xl border border-border/60 shadow-sm">
          <div className="flex gap-2 p-1 bg-neutral/50 rounded-xl w-full sm:w-auto">
            {FILTERS.map((f) => (
              <button
                key={f.key}
                type="button"
                onClick={() => setFilter(f.key)}
                className={cn(
                  "flex-1 sm:flex-none rounded-lg px-4 py-1.5 text-xs font-semibold transition duration-fast ease-flow",
                  filter === f.key
                    ? "bg-red-600 text-white shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                {f.label}
              </button>
            ))}
          </div>
          <div className="relative w-full sm:w-64 sm:ms-auto">
            <span className={cn(
              "absolute inset-y-0 flex items-center text-muted-foreground pointer-events-none",
              currentLang === "fa" ? "right-3" : "left-3"
            )} aria-hidden="true">
              🔍
            </span>
            <Input
              type="search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder={t("app.stocks.search_placeholder", currentLang)}
              className={cn("h-9", currentLang === "fa" ? "pr-10" : "pl-10")}
            />
          </div>
        </section>

        <TarotCard icon="📈" title={`${t("app.stocks.list_title", currentLang)} (${currentLang === "fa" ? filtered.length.toLocaleString("fa-IR") : filtered.length})`}>
          <div className="overflow-x-auto -mx-4 px-4 sm:mx-0 sm:px-0">
            <table className="w-full border-collapse text-sm">
              <thead>
                <tr className="border-b border-border text-muted-foreground">
                  <th className="px-3 py-3 text-right font-bold text-xs uppercase tracking-wider">{t("app.stocks.symbol", currentLang)}</th>
                  <th className="px-3 py-3 text-right font-bold text-xs uppercase tracking-wider">{t("app.stocks.name", currentLang)}</th>
                  <th className="px-3 py-3 text-center font-bold text-xs uppercase tracking-wider">{t("app.stocks.market", currentLang)}</th>
                  <th className="px-3 py-3 text-right font-bold text-xs uppercase tracking-wider">{t("app.stocks.sector", currentLang)}</th>
                  <th className="px-3 py-3 text-left font-bold text-xs uppercase tracking-wider">{t("app.stocks.price", currentLang)}</th>
                  <th className="px-3 py-3 text-left font-bold text-xs uppercase tracking-wider">{t("app.stocks.change", currentLang)}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/40">
                {filtered.map((a) => {
                  const p = prices[a.symbol];
                  return (
                    <tr
                      key={a.id}
                      className="transition duration-fast ease-flow hover:bg-neutral/50 group"
                    >
                      <td className="px-3 py-4 font-bold">
                        <Link
                          href={`/stocks/${encodeURIComponent(a.symbol)}`}
                          className="text-red-600 hover:text-red-700 transition-colors"
                        >
                          {a.symbol}
                        </Link>
                      </td>
                      <td className="px-3 py-4 text-muted-foreground group-hover:text-foreground transition-colors">{a.name}</td>
                      <td className="px-3 py-4 text-center">
                        <span className="inline-flex items-center rounded-full bg-neutral/70 px-2.5 py-0.5 text-[10px] font-bold text-muted-foreground">
                          {MARKET_LABEL[a.market]}
                        </span>
                      </td>
                      <td className="px-3 py-4 text-muted-foreground text-xs">{a.sector ?? "—"}</td>
                      <td className="px-3 py-4 text-left font-mono text-xs">
                        {p ? (currentLang === "fa" ? p.price.toLocaleString("fa-IR") : p.price.toLocaleString()) : "—"}
                      </td>
                      <td className="px-3 py-4 text-left">
                        {p ? <ChangeBadge value={p.change_pct} /> : "—"}
                      </td>
                    </tr>
                  );
                })}
                {filtered.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-3 py-12 text-center text-muted-foreground">
                      <div className="flex flex-col items-center">
                        <div className="text-4xl mb-2">📁</div>
                        <p>{t("app.stocks.no_results", currentLang)}</p>
                      </div>
                    </td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>
        </TarotCard>
      </div>
    </DashboardShell>
  );
}

