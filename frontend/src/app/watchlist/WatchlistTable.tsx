"use client";

import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/cn";
import { t } from "@/lib/i18n";
import type { EnrichedWatchlistRow } from "./types";

interface WatchlistTableProps {
  items: EnrichedWatchlistRow[];
  removingItemId: string | null;
  onRemove: (itemId: string) => void;
}

export function WatchlistTable({ items, removingItemId, onRemove }: WatchlistTableProps) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-[var(--color-border)]">
            <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-[var(--color-text-secondary)]">Symbol</th>
            <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-[var(--color-text-secondary)]">Name</th>
            <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-[var(--color-text-secondary)]">Market</th>
            <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-[var(--color-text-secondary)]">Price</th>
            <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-[var(--color-text-secondary)]">Change</th>
            <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-[var(--color-text-secondary)]">Actions</th>
          </tr>
        </thead>
        <tbody>
          {items.map((row) => (
            <tr
              key={row.watchlistItemId}
              className="border-b border-[var(--color-border)] last:border-0 hover:bg-[var(--color-background)] transition-colors"
            >
              <td className="px-4 py-3 font-medium text-[var(--color-text-primary)]">{row.symbol}</td>
              <td className="px-4 py-3 text-[var(--color-text-secondary)]">{row.name}</td>
              <td className="px-4 py-3 text-[var(--color-text-secondary)]">{row.market}</td>
              <td className="px-4 py-3 text-right tabular-nums text-[var(--color-text-primary)]">
                {row.price > 0 ? `$${row.price.toFixed(2)}` : "—"}
              </td>
              <td className={cn("px-4 py-3 text-right tabular-nums font-medium", row.changePct >= 0 ? "text-[var(--color-success)]" : "text-[var(--color-error)]")}>
                {row.changePct !== 0 ? `${row.changePct >= 0 ? "+" : ""}${row.changePct.toFixed(2)}%` : "—"}
              </td>
              <td className="px-4 py-3 text-right">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => onRemove(row.watchlistItemId)}
                  disabled={removingItemId === row.watchlistItemId}
                  className="text-[var(--color-error)] hover:text-[var(--color-error)]"
                >
                  {removingItemId === row.watchlistItemId ? "..." : t("app.watchlist.remove")}
                </Button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
