"use client";

import { useMemo, useState, useEffect, useRef, useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import { NewDashboardShell } from "@/components/layout/NewDashboardShell";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { PageLoading } from "@/components/ui/PageLoading";
import { TarotCard } from "@/components/ui/TarotCard";
import { fetchSymbols } from "@/lib/api/stocks";
import { fetchWatchlists } from "@/lib/api/watchlist";
import { QK } from "@/lib/query-keys";
import { t } from "@/lib/i18n";
import { useAuthStore } from "@/store/useAuthStore";
import { isNasdaqEquityLike } from "@/lib/dashboard-data";
import {
  useLiveData,
  LiveConnectionIndicator,
  type SSEEvent,
} from "@/hooks/useLiveData";
import { useWatchlistActions } from "./useWatchlistActions";
import {
  CreateWatchlistModal,
  RenameWatchlistModal,
  AddItemModal,
  DeleteConfirmModal,
} from "./WatchlistModals";
import { WatchlistSidebar } from "./WatchlistSidebar";
import { WatchlistTable } from "./WatchlistTable";
import type {
  QuotePayload,
  MarketStreamPayload,
  EnrichedWatchlistRow,
  LiveQuotesMap,
} from "./types";

export default function WatchlistPage() {
  const { user } = useAuthStore();
  const isLoggedIn = !!user;

  const [selectedWatchlistId, setSelectedWatchlistId] = useState<string | null>(null);
  const [liveQuotes, setLiveQuotes] = useState<LiveQuotesMap>({});
  const lastQuoteEventRef = useRef<number | null>(null);

  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isRenameModalOpen, setIsRenameModalOpen] = useState(false);
  const [isAddItemModalOpen, setIsAddItemModalOpen] = useState(false);
  const [isDeleteConfirmOpen, setIsDeleteConfirmOpen] = useState(false);

  const [newName, setNewName] = useState("");
  const [newDescription, setNewDescription] = useState("");
  const [renameName, setRenameName] = useState("");
  const [selectedAsset, setSelectedAsset] = useState<{ symbol: string; name: string } | null>(null);
  const [itemNote, setItemNote] = useState("");
  const [itemThreshold, setItemThreshold] = useState("");
  const [removingItemId, setRemovingItemId] = useState<string | null>(null);

  const { data: watchlists = [], isLoading: wlLoading, error: wlError, refetch: refetchWatchlists } = useQuery({
    queryKey: QK.watchlists(),
    queryFn: fetchWatchlists,
    enabled: isLoggedIn,
  });

  const { data: assetMapData } = useQuery({
    queryKey: QK.symbols({ limit: 1000 }),
    queryFn: () => fetchSymbols({ limit: 1000 }),
    enabled: isLoggedIn,
    select: (assets) => new Map(assets.map((a) => [a.symbol.toUpperCase(), a.id])),
  });

  const assetMap = assetMapData ?? new Map<string, string>();
  const loading = wlLoading;
  const error = !isLoggedIn ? t("app.watchlist.login_required") : (wlError ? t("app.watchlist.error_loading") : null);

  // Auto-select first watchlist when data loads
  useEffect(() => {
    if (watchlists.length > 0 && !selectedWatchlistId) {
      setSelectedWatchlistId(watchlists[0].id);
    } else if (watchlists.length === 0) {
      setSelectedWatchlistId(null);
    }
  }, [watchlists, selectedWatchlistId]);

  const {
    saving,
    selectedWatchlist,
    handleCreate,
    handleRename,
    handleDelete,
    handleAddItem: addItemAction,
    handleRemoveItem: removeItemAction,
  } = useWatchlistActions(watchlists, selectedWatchlistId);

  const applyQuotePatch = useCallback((symbol: string, price?: number, changePct?: number) => {
    const sym = symbol.toUpperCase();
    const now = Date.now();
    setLiveQuotes((prev) => {
      const existing = prev[sym];
      const nextPrice = typeof price === "number" ? price : existing?.price ?? 0;
      const nextChange = typeof changePct === "number" ? changePct : existing?.changePct ?? 0;
      if (existing && existing.price === nextPrice && existing.changePct === nextChange) {
        return prev;
      }
      return { ...prev, [sym]: { price: nextPrice, changePct: nextChange, ts: now } };
    });
    lastQuoteEventRef.current = now;
  }, []);

  const handleMarketData = useCallback(
    (payload: MarketStreamPayload, _event: SSEEvent<MarketStreamPayload>) => {
      if (payload?.top_movers && Array.isArray(payload.top_movers)) {
        for (const m of payload.top_movers) {
          applyQuotePatch(m.symbol, m.price, m.change_pct);
        }
      }
      if (payload?.quotes && typeof payload.quotes === "object") {
        for (const [sym, q] of Object.entries(payload.quotes)) {
          applyQuotePatch(sym, q?.price, q?.change_pct);
        }
      }
    },
    [applyQuotePatch],
  );

  const enrichedSymbols = useMemo(() => {
    if (!selectedWatchlist) return [] as string[];
    return selectedWatchlist.items
      .filter((item) => item.asset && isNasdaqEquityLike(item.asset))
      .map((item) => item.asset!.symbol.toUpperCase());
  }, [selectedWatchlist]);

  const _handleQuoteDataFactory = useCallback(
    (symbol: string) =>
      (payload: QuotePayload, _event: SSEEvent<QuotePayload>) => {
        applyQuotePatch(payload?.symbol || symbol, payload?.price, payload?.change_pct);
      },
    [applyQuotePatch],
  );

  const marketLive = useLiveData<MarketStreamPayload>("market", {
    enabled: enrichedSymbols.length > 0,
    onData: handleMarketData,
  });

  const enrichedItems = useMemo<EnrichedWatchlistRow[]>(() => {
    if (!selectedWatchlist) return [];
    return selectedWatchlist.items
      .filter((item) => item.asset && isNasdaqEquityLike(item.asset))
      .map((item) => {
        const asset = item.asset!;
        const sym = asset.symbol.toUpperCase();
        const live = liveQuotes[sym];
        return {
          symbol: sym,
          name: asset.name,
          market: "NASDAQ" as const,
          price: live?.price ?? 0,
          changePct: live?.changePct ?? 0,
          watchlistItemId: item.id,
        };
      });
  }, [selectedWatchlist, liveQuotes]);

  async function onCreateSubmit(name: string, description: string) {
    await handleCreate(name, description);
    setIsCreateModalOpen(false);
    setNewName("");
    setNewDescription("");
  }

  async function onRenameSubmit(newName: string) {
    await handleRename(newName);
    setIsRenameModalOpen(false);
  }

  async function onAddItemSubmit() {
    if (!selectedAsset) return;
    const assetId = assetMap.get(selectedAsset.symbol.toUpperCase());
    if (!assetId) return;
    await addItemAction(
      assetId,
      itemNote.trim() || null,
      itemThreshold ? Number(itemThreshold) : null,
    );
    setIsAddItemModalOpen(false);
    setSelectedAsset(null);
    setItemNote("");
    setItemThreshold("");
  }

  async function onDeleteConfirm() {
    await handleDelete();
    setIsDeleteConfirmOpen(false);
  }

  async function onRemoveItem(itemId: string) {
    setRemovingItemId(itemId);
    await removeItemAction(itemId);
    setRemovingItemId(null);
  }

  function openRenameModal() {
    if (!selectedWatchlist) return;
    setRenameName(selectedWatchlist.name);
    setIsRenameModalOpen(true);
  }

  if (loading) {
    return (
      <NewDashboardShell title={t("app.watchlist.title")}>
        <PageLoading />
      </NewDashboardShell>
    );
  }

  if (error) {
    return (
      <NewDashboardShell title={t("app.watchlist.title")}>
        <TarotCard icon="⚠️" title={t("app.watchlist.error_loading")} className="max-w-md mx-auto border-error/20 bg-error/5">
          <div className="py-4 text-center">
            <p className="text-sm text-error font-medium mb-4">{error}</p>
            <PrimaryButton onClick={() => refetchWatchlists()} variant="outline" size="sm">
              {t("app.portfolio.retry")}
            </PrimaryButton>
          </div>
        </TarotCard>
      </NewDashboardShell>
    );
  }

  return (
    <NewDashboardShell title={t("app.watchlist.title")}>
      <div className="space-y-6 animate-in fade-in duration-500">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">
              {t("app.watchlist.title")}
            </h1>
            <p className="text-sm text-[var(--color-text-muted)]">
              {t("app.watchlist.subtitle")}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <LiveConnectionIndicator
              health={marketLive.connectionHealth}
              dataAgeMs={marketLive.lastDataAgeMs}
              lastEventTs={lastQuoteEventRef.current}
              label="Quotes"
            />
            <PrimaryButton onClick={() => setIsCreateModalOpen(true)}>
              {t("app.watchlist.create_button")}
            </PrimaryButton>
          </div>
        </div>

        {watchlists.length === 0 ? (
          <Card>
            <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border bg-surface/30 py-16">
              <div className="text-4xl mb-4">📋</div>
              <h3 className="text-lg font-medium text-foreground">
                {t("app.watchlist.empty_title")}
              </h3>
              <p className="text-sm text-muted-foreground mt-2 max-w-sm text-center">
                {t("app.watchlist.empty_desc")}
              </p>
              <PrimaryButton onClick={() => setIsCreateModalOpen(true)} className="mt-6">
                {t("app.watchlist.create_button")}
              </PrimaryButton>
            </div>
          </Card>
        ) : (
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            <WatchlistSidebar
              watchlists={watchlists}
              selectedWatchlistId={selectedWatchlistId}
              onSelect={setSelectedWatchlistId}
            />

            <div className="lg:col-span-2 space-y-4">
              {selectedWatchlist ? (
                <Card>
                  <div className="flex flex-col gap-3 p-5 border-b border-[var(--color-border)] sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <h3 className="font-semibold text-[var(--color-text-primary)]">
                        {selectedWatchlist.name}
                      </h3>
                      {selectedWatchlist.description && (
                        <p className="text-xs text-[var(--color-text-muted)] mt-0.5">
                          {selectedWatchlist.description}
                        </p>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <Button size="sm" variant="outline" onClick={openRenameModal}>
                        {t("app.watchlist.rename")}
                      </Button>
                      <Button size="sm" variant="outline" onClick={() => setIsAddItemModalOpen(true)}>
                        {t("app.watchlist.add_item")}
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setIsDeleteConfirmOpen(true)}
                        className="text-[var(--color-error)] hover:text-[var(--color-error)]"
                      >
                        {t("app.watchlist.delete")}
                      </Button>
                    </div>
                  </div>
                  <div className="p-5">
                    {enrichedItems.length === 0 ? (
                      <div className="flex flex-col items-center justify-center py-12 text-[var(--color-text-muted)]">
                        <div className="text-4xl mb-4">📭</div>
                        <p className="text-lg font-bold text-[var(--color-text-primary)] mb-2">
                          {t("app.watchlist.no_items_title")}
                        </p>
                        <p className="text-sm mb-6 max-w-xs text-center">
                          {t("app.watchlist.no_items_desc")}
                        </p>
                        <Button onClick={() => setIsAddItemModalOpen(true)} variant="outline" size="sm">
                          {t("app.watchlist.add_item")}
                        </Button>
                      </div>
                    ) : (
                      <WatchlistTable
                        items={enrichedItems}
                        removingItemId={removingItemId}
                        onRemove={onRemoveItem}
                      />
                    )}
                  </div>
                </Card>
              ) : (
                <Card>
                  <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border bg-surface/30 py-16">
                    <div className="text-4xl mb-4">👈</div>
                    <h3 className="text-lg font-medium text-foreground">
                      {t("app.watchlist.select_title")}
                    </h3>
                    <p className="text-sm text-muted-foreground mt-2 max-w-sm text-center">
                      {t("app.watchlist.select_desc")}
                    </p>
                  </div>
                </Card>
              )}
            </div>
          </div>
        )}
      </div>

      <CreateWatchlistModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSubmit={onCreateSubmit}
        saving={saving}
        name={newName}
        onNameChange={setNewName}
        description={newDescription}
        onDescriptionChange={setNewDescription}
      />

      <RenameWatchlistModal
        isOpen={isRenameModalOpen}
        onClose={() => setIsRenameModalOpen(false)}
        onSubmit={onRenameSubmit}
        saving={saving}
        name={renameName}
        onNameChange={setRenameName}
      />

      <AddItemModal
        isOpen={isAddItemModalOpen}
        onClose={() => {
          setIsAddItemModalOpen(false);
          setSelectedAsset(null);
          setItemNote("");
          setItemThreshold("");
        }}
        onSubmit={onAddItemSubmit}
        saving={saving}
        selectedWatchlist={selectedWatchlist}
        selectedAsset={selectedAsset}
        onAssetSelect={setSelectedAsset}
        note={itemNote}
        onNoteChange={setItemNote}
        threshold={itemThreshold}
        onThresholdChange={setItemThreshold}
      />

      <DeleteConfirmModal
        isOpen={isDeleteConfirmOpen}
        onClose={() => setIsDeleteConfirmOpen(false)}
        onConfirm={onDeleteConfirm}
        saving={saving}
        watchlistName={selectedWatchlist?.name ?? ""}
      />
    </NewDashboardShell>
  );
}
