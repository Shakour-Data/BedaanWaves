"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { BarChart3 } from "lucide-react";
import { GeneralDashboardTab } from "@/components/dashboard/GeneralDashboardTab";
import { NewDashboardShell } from "@/components/layout/NewDashboardShell";
import { PageLoading } from "@/components/ui/PageLoading";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { t } from "@/lib/i18n";

/**
 * Per-symbol analytical dashboard.
 *
 * Renders the full 20-view chart model scoped to a single symbol:
 *
 *   Level 1 (Dimensions)          Level 2 (Sub-Dimensions)
 *   1.  Dimension score spider      2.  Sub-dimension score spider
 *   3.  Dimension score trend        4.  Sub-dimension score trend
 *   5.  Dimension score change       6.  Sub-dimension score change
 *   7.  Dimension coefficient        8.  Sub-dimension coefficient
 *   9.  Dimension coefficient change 10. Sub-dimension coefficient change
 *
 *   Level 3 (Aspects)              Level 4 (Sub-Aspects)
 *   11. Aspect score spider          12. Sub-aspect score spider
 *   13. Aspect score trend           14. Sub-aspect score trend
 *   15. Aspect score change          16. Sub-aspect score change
 *   17. Aspect coefficient           18. Sub-aspect coefficient
 *   19. Aspect coefficient change    20. Sub-aspect coefficient change
 *
 * All 20 views are derived from a single unified temporal snapshot
 * (`/analysis/dashboard/snapshot?symbol=…`), guaranteeing data parity
 * between the spider chart and the last point of every trend line.
 */
export default function StockDashboardPage() {
  const params = useParams<{ symbol: string }>();
  const symbol = decodeURIComponent(
    Array.isArray(params.symbol) ? params.symbol[0] : params.symbol ?? "",
  );

  const [assetName, setAssetName] = useState<string | null>(null);
  const [assetLoading, setAssetLoading] = useState(true);
  const [assetError, setAssetError] = useState<string | null>(null);

  // Fetch the asset's display name so the page header can show "SYMBOL · Name".
  // State is only ever mutated from inside the async callbacks below (never
  // synchronously within the effect body), so there are no cascading renders.
  useEffect(() => {
    if (!symbol) return;
    let active = true;
    import("@/lib/api/stocks")
      .then(async (mod) => {
        const asset = await mod.fetchAsset(symbol);
        if (active) setAssetName(asset?.name ?? null);
      })
      .catch((e: unknown) => {
        if (active)
          setAssetError(
            e instanceof Error ? e.message : t("app.stocks.detail.error_title"),
          );
      })
      .finally(() => {
        if (active) setAssetLoading(false);
      });
    return () => {
      active = false;
    };
  }, [symbol]);

  const title =
    assetName || assetLoading ? `${symbol}${assetName ? ` · ${assetName}` : ""}` : symbol;

  if (assetLoading && !assetName) {
    return (
      <NewDashboardShell title={t("app.dashboard.title")}>
        <PageLoading />
      </NewDashboardShell>
    );
  }

  if (assetError && !assetName) {
    return (
      <NewDashboardShell title={symbol}>
        <div className="flex min-h-[40vh] items-center justify-center">
          <ErrorMessage
            message={assetError}
            actions={[
              {
                label: "Retry",
                onAction: () => window.location.reload(),
              },
            ]}
          />
        </div>
      </NewDashboardShell>
    );
  }

  return (
    <NewDashboardShell title={title}>
      <div className="flex flex-col gap-6 animate-in fade-in duration-500">
        {/* Breadcrumb */}
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Link href="/stocks" className="hover:text-foreground">
            {t("app.nav.stocks")}
          </Link>
          <span>/</span>
          <Link href={`/stocks/${symbol}`} className="hover:text-foreground">
            {symbol}
          </Link>
          <span>/</span>
          <span className="text-foreground">
            <BarChart3 className="mr-1 inline-block h-3.5 w-3.5" />
            {t("app.dashboard.title")}
          </span>
        </div>

        <GeneralDashboardTab symbol={symbol} />
      </div>
    </NewDashboardShell>
  );
}