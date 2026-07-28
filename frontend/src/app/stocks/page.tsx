"use client";

/**
 * صفحه‌ی فهرست سهام: نمادها را از `GET /market/symbols` می‌گیرد و آخرین
 * قیمت/تغییر را از `GET /market/latest-prices`. هر ردیف به صفحه‌ی جزئیاتِ
 * `/stocks/[symbol]` لینک می‌شود.
 */

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
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

type MarketFilter = "ALL" | "TSE" | "OTC" | "CRYPTO";

const FILTERS: { key: MarketFilter; label: string }[] = [
  { key: "ALL", label: "همه" },
  { key: "TSE", label: "بورس" },
  { key: "OTC", label: "فرابورس" },
  { key: "CRYPTO", label: "کریپتو" },
];

function matchesFilter(asset: Asset, filter: MarketFilter): boolean {
  if (filter === "ALL") return true;
  if (filter === "CRYPTO") return asset.asset_class === "CRYPTO";
  return asset.market === filter;
}

export default function StocksPage() {
  const [assets, setAssets] = useState<Asset[] | null>(null);
  const [prices, setPrices] = useState<Record<string, LatestPrice>>({});
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<MarketFilter>("ALL");
  const [search, setSearch] = useState("");

  useEffect(() => {
    let active = true;

    async function load() {
      setLoading(true);
      try {
        const list = await fetchSymbols({ limit: 1000 });
        if (!active) return;
        setAssets(list);
        setError(null);
        const map = await fetchLatestPrices(list.map((a) => a.symbol)).catch(() => ({}));
        if (active) setPrices(map);
      } catch (e: unknown) {
        if (active) setError(e instanceof Error ? e.message : "خطا در دریافت نمادها");
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
      <div className="flex min-h-[40vh] items-center justify-center text-muted-foreground">
        در حال بارگذاری نمادها…
      </div>
    );
  }

  if (error || !assets) {
    return (
      <TarotCard icon="⚠️" title="خطا در ارتباط با بک‌اند">
        <p className="text-sm text-muted-foreground">
          دریافت فهرست نمادها ممکن نشد. مطمئن شوید سرویس بک‌اند در حال اجراست.
        </p>
        {error ? <p className="mt-2 text-xs text-primary">{error}</p> : null}
      </TarotCard>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      {/* فیلترها + جست‌وجو */}
      <section className="flex flex-wrap items-center gap-2">
        <div className="flex gap-1">
          {FILTERS.map((f) => (
            <button
              key={f.key}
              type="button"
              onClick={() => setFilter(f.key)}
              className={
                "rounded-full px-3 py-1.5 text-sm transition duration-fast ease-flow " +
                (filter === f.key
                  ? "bg-secondary/10 font-semibold text-secondary"
                  : "text-muted-foreground hover:bg-black/5")
              }
            >
              {f.label}
            </button>
          ))}
        </div>
        <label className="ms-auto flex items-center gap-2 rounded-xl bg-neutral/60 px-3 py-2 text-sm text-muted-foreground">
          <span aria-hidden="true">🔍</span>
          <input
            type="search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="جست‌وجوی نماد یا نام…"
            className="bg-transparent text-foreground outline-none placeholder:text-muted-foreground/70"
          />
        </label>
      </section>

      <TarotCard icon="🏢" title={`نمادها (${filtered.length.toLocaleString("fa-IR")})`}>
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-border text-muted-foreground">
                <th className="px-2 py-2 text-right font-medium">نماد</th>
                <th className="px-2 py-2 text-right font-medium">نام</th>
                <th className="px-2 py-2 text-center font-medium">بازار</th>
                <th className="px-2 py-2 text-right font-medium">صنعت</th>
                <th className="px-2 py-2 text-left font-medium">قیمت</th>
                <th className="px-2 py-2 text-left font-medium">تغییر</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((a) => {
                const p = prices[a.symbol];
                return (
                  <tr
                    key={a.id}
                    className="border-b border-border/60 transition duration-fast ease-flow hover:bg-black/5"
                  >
                    <td className="px-2 py-2 font-semibold">
                      <Link
                        href={`/stocks/${encodeURIComponent(a.symbol)}`}
                        className="text-secondary hover:underline"
                      >
                        {a.symbol}
                      </Link>
                    </td>
                    <td className="px-2 py-2 text-muted-foreground">{a.name}</td>
                    <td className="px-2 py-2 text-center">
                      <span className="rounded-full bg-neutral/70 px-2 py-0.5 text-xs">
                        {MARKET_LABEL[a.market]}
                      </span>
                    </td>
                    <td className="px-2 py-2 text-muted-foreground">{a.sector ?? "—"}</td>
                    <td className="px-2 py-2 text-left">
                      {p ? p.price.toLocaleString("fa-IR") : "—"}
                    </td>
                    <td className="px-2 py-2 text-left">
                      {p ? <ChangeBadge value={p.change_pct} /> : "—"}
                    </td>
                  </tr>
                );
              })}
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-2 py-6 text-center text-muted-foreground">
                    نمادی یافت نشد.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </TarotCard>
    </div>
  );
}
