"use client";

import { Card } from "@/components/ui/Card";
import { cn } from "@/lib/cn";
import { t } from "@/lib/i18n";
import type { WatchlistType } from "./types";

interface WatchlistSidebarProps {
  watchlists: WatchlistType[];
  selectedWatchlistId: string | null;
  onSelect: (id: string) => void;
}

export function WatchlistSidebar({ watchlists, selectedWatchlistId, onSelect }: WatchlistSidebarProps) {
  return (
    <div className="lg:col-span-1 space-y-3">
      <Card>
        <div className="px-5 py-4 border-b border-[var(--color-border)]">
          <h3 className="text-sm font-semibold text-[var(--color-text-primary)]">
            {t("app.watchlist.your_watchlists")}
          </h3>
        </div>
        <div className="p-2">
          {watchlists.map((w) => (
            <button
              key={w.id}
              onClick={() => onSelect(w.id)}
              className={cn(
                "w-full rounded-lg px-3 py-2 text-left text-sm transition-colors",
                selectedWatchlistId === w.id
                  ? "bg-[var(--color-primary-soft)] text-[var(--color-primary)]"
                  : "text-[var(--color-text-secondary)] hover:bg-[var(--color-muted)] hover:text-[var(--color-text-primary)]",
              )}
            >
              <div className="flex items-center justify-between">
                <span className="font-medium truncate">{w.name}</span>
                {w.is_default && (
                  <span className="text-[10px] uppercase tracking-wider text-[var(--color-text-muted)]">
                    {t("app.watchlist.default")}
                  </span>
                )}
              </div>
              {w.description && (
                <p className="mt-0.5 text-xs text-[var(--color-text-muted)] truncate">
                  {w.description}
                </p>
              )}
              <p className="mt-1 text-xs text-[var(--color-text-muted)]">
                {t("app.watchlist.items").replace("{count}", String(w.items.length))}
              </p>
            </button>
          ))}
        </div>
      </Card>
    </div>
  );
}
