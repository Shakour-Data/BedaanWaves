"use client";

import { useEffect, useMemo, useState, useCallback } from "react";
import { NewDashboardShell } from "@/components/layout/NewDashboardShell";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { InputField } from "@/components/ui/InputField";
import { Modal } from "@/components/ui/Modal";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { PageLoading } from "@/components/ui/PageLoading";
import { TarotCard } from "@/components/ui/TarotCard";
import { StockPicker } from "@/components/search/StockPicker";
import { fetchSymbols } from "@/lib/api/stocks";
import {
  fetchWatchlists,
  createWatchlist,
  updateWatchlist,
  deleteWatchlist,
  addWatchlistItem,
  removeWatchlistItem,
  type Watchlist as WatchlistType,
  type CreateWatchlistPayload,
  type UpdateWatchlistPayload,
} from "@/lib/api/watchlist";
import { t } from "@/lib/i18n";
import { getApiErrorMessage } from "@/lib/api";
import { cn } from "@/lib/cn";
import { useAuthStore } from "@/store/useAuthStore";
import { useUXStore } from "@/store/useUXStore";
import { isNasdaqEquityLike } from "@/lib/dashboard-data";

export default function WatchlistPage() {
  const addToast = useUXStore((state) => state.addToast);
  const { user } = useAuthStore();

  const [watchlists, setWatchlists] = useState<WatchlistType[]>([]);
  const [selectedWatchlistId, setSelectedWatchlistId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [assetMap, setAssetMap] = useState<Map<string, string>>(new Map());

  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isRenameModalOpen, setIsRenameModalOpen] = useState(false);
  const [isAddItemModalOpen, setIsAddItemModalOpen] = useState(false);
  const [isDeleteConfirmOpen, setIsDeleteConfirmOpen] = useState(false);

  const [newName, setNewName] = useState("");
  const [newDescription, setIsNewDescription] = useState("");
  const [renameName, setRenameName] = useState("");
  const [selectedAsset, setSelectedAsset] = useState<{ symbol: string; name: string } | null>(null);
  const [itemNote, setItemNote] = useState("");
  const [itemThreshold, setItemThreshold] = useState<string>("");
  const [removingItemId, setRemovingItemId] = useState<string | null>(null);

  const selectedWatchlist = useMemo(
    () => watchlists.find((w) => w.id === selectedWatchlistId) ?? null,
    [watchlists, selectedWatchlistId]
  );

  const loadWatchlists = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchWatchlists();
      setWatchlists(data);
      if (!selectedWatchlistId && data.length > 0) {
        setSelectedWatchlistId(data[0].id);
      } else if (data.length === 0) {
        setSelectedWatchlistId(null);
      }
    } catch (err) {
      const message = getApiErrorMessage(err);
      setError(message || t("app.watchlist.error_loading"));
    } finally {
      setLoading(false);
    }
  }, [selectedWatchlistId]);

  useEffect(() => {
    if (user) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      loadWatchlists();
      fetchSymbols({ limit: 1000 }).then((assets) => {
        const map = new Map(assets.map((a) => [a.symbol.toUpperCase(), a.id]));
        setAssetMap(map);
      });
    } else {
      setLoading(false);
      setError(t("app.watchlist.login_required"));
    }
  }, [user, loadWatchlists]);

  async function handleCreateWatchlist(e: React.FormEvent) {
    e.preventDefault();
    if (!newName.trim()) return;
    setSaving(true);
    try {
      const payload: CreateWatchlistPayload = {
        name: newName.trim(),
        description: newDescription.trim() || null,
      };
      const created = await createWatchlist(payload);
      setWatchlists((prev) => [created, ...prev]);
      setSelectedWatchlistId(created.id);
      setIsCreateModalOpen(false);
      setNewName("");
      setIsNewDescription("");
      addToast({ type: "success", message: t("app.watchlist.created") });
    } catch (err) {
      const message = getApiErrorMessage(err);
      addToast({ type: "error", message: message || t("app.watchlist.error_creating") });
    } finally {
      setSaving(false);
    }
  }

  async function handleRenameWatchlist(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedWatchlist || !renameName.trim()) return;
    setSaving(true);
    try {
      const payload: UpdateWatchlistPayload = { name: renameName.trim() };
      const updated = await updateWatchlist(selectedWatchlist.id, payload);
      setWatchlists((prev) =>
        prev.map((w) => (w.id === updated.id ? updated : w))
      );
      setIsRenameModalOpen(false);
      addToast({ type: "success", message: t("app.watchlist.renamed") });
    } catch (err) {
      const message = getApiErrorMessage(err);
      addToast({ type: "error", message: message || t("app.watchlist.error_updating") });
    } finally {
      setSaving(false);
    }
  }

  async function handleDeleteWatchlist() {
    if (!selectedWatchlist) return;
    setSaving(true);
    try {
      await deleteWatchlist(selectedWatchlist.id);
      setWatchlists((prev) => prev.filter((w) => w.id !== selectedWatchlist.id));
      setSelectedWatchlistId((prev) => (prev === selectedWatchlist.id ? null : prev));
      setIsDeleteConfirmOpen(false);
      addToast({ type: "success", message: t("app.watchlist.deleted") });
    } catch (err) {
      const message = getApiErrorMessage(err);
      addToast({ type: "error", message: message || t("app.watchlist.error_deleting") });
    } finally {
      setSaving(false);
    }
  }

  async function handleAddItem(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedWatchlist || !selectedAsset) return;
    const assetId = assetMap.get(selectedAsset.symbol.toUpperCase());
    if (!assetId) {
      addToast({ type: "error", message: t("app.watchlist.asset_not_found") });
      return;
    }
    setSaving(true);
    try {
      const payload = {
        asset_id: assetId,
        note: itemNote.trim() || null,
        alert_threshold_pct: itemThreshold ? Number(itemThreshold) : null,
      };
      const item = await addWatchlistItem(selectedWatchlist.id, payload);
      setWatchlists((prev) =>
        prev.map((w) =>
          w.id === selectedWatchlist.id
            ? { ...w, items: [...w.items, item] }
            : w
        )
      );
      setIsAddItemModalOpen(false);
      setSelectedAsset(null);
      setItemNote("");
      setItemThreshold("");
      addToast({ type: "success", message: t("app.watchlist.item_added") });
    } catch (err) {
      const message = getApiErrorMessage(err);
      addToast({ type: "error", message: message || t("app.watchlist.error_adding_item") });
    } finally {
      setSaving(false);
    }
  }

  async function handleRemoveItem(itemId: string) {
    if (!selectedWatchlist) return;
    setRemovingItemId(itemId);
    try {
      await removeWatchlistItem(selectedWatchlist.id, itemId);
      setWatchlists((prev) =>
        prev.map((w) =>
          w.id === selectedWatchlist.id
            ? { ...w, items: w.items.filter((i) => i.id !== itemId) }
            : w
        )
      );
      addToast({ type: "success", message: t("app.watchlist.item_removed") });
    } catch (err) {
      const message = getApiErrorMessage(err);
      addToast({ type: "error", message: message || t("app.watchlist.error_removing_item") });
    } finally {
      setRemovingItemId(null);
    }
  }

  function openRenameModal() {
    if (!selectedWatchlist) return;
    setRenameName(selectedWatchlist.name);
    setIsRenameModalOpen(true);
  }

  function openDeleteConfirm() {
    if (!selectedWatchlist) return;
    setIsDeleteConfirmOpen(true);
  }

  const enrichedItems = useMemo(() => {
    if (!selectedWatchlist) return [];
    return selectedWatchlist.items
      .filter((item) => item.asset && isNasdaqEquityLike(item.asset))
      .map((item) => {
        const asset = item.asset!;
        return {
          symbol: asset.symbol,
          name: asset.name,
          market: "NASDAQ" as const,
          price: 0,
          changePct: 0,
          watchlistItemId: item.id,
        };
      });
  }, [selectedWatchlist]);

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
            <PrimaryButton onClick={loadWatchlists} variant="outline" size="sm">
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
          <PrimaryButton onClick={() => setIsCreateModalOpen(true)}>
            {t("app.watchlist.create_button")}
          </PrimaryButton>
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
              <PrimaryButton
                onClick={() => setIsCreateModalOpen(true)}
                className="mt-6"
              >
                {t("app.watchlist.create_button")}
              </PrimaryButton>
            </div>
          </Card>
        ) : (
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
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
                      onClick={() => setSelectedWatchlistId(w.id)}
                      className={cn(
                        "w-full rounded-lg px-3 py-2 text-left text-sm transition-colors",
                        selectedWatchlistId === w.id
                          ? "bg-[var(--color-primary-soft)] text-[var(--color-primary)]"
                          : "text-[var(--color-text-secondary)] hover:bg-[var(--color-muted)] hover:text-[var(--color-text-primary)]"
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

            <div className="lg:col-span-2 space-y-4">
              {selectedWatchlist ? (
                <>
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
                          onClick={openDeleteConfirm}
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
                              {enrichedItems.map((row) => (
                                <tr key={row.watchlistItemId} className="border-b border-[var(--color-border)] last:border-0 hover:bg-[var(--color-background)]">
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
                                      onClick={() => handleRemoveItem(row.watchlistItemId)}
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
                      )}
                    </div>
                  </Card>
                </>
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

      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title={t("app.watchlist.create_title")}
        description={t("app.watchlist.create_desc")}
        footer={
          <>
            <Button variant="outline" onClick={() => setIsCreateModalOpen(false)} disabled={saving}>
              {t("app.auth.cancel")}
            </Button>
            <PrimaryButton onClick={handleCreateWatchlist} disabled={saving || !newName.trim()}>
              {saving ? "..." : t("app.watchlist.create_button")}
            </PrimaryButton>
          </>
        }
      >
        <form onSubmit={handleCreateWatchlist} className="space-y-4">
          <InputField
            label={t("app.watchlist.name_label")}
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder={t("app.watchlist.name_placeholder")}
            required
          />
          <InputField
            label={t("app.watchlist.description_label")}
            value={newDescription}
            onChange={(e) => setIsNewDescription(e.target.value)}
            placeholder={t("app.watchlist.description_placeholder")}
          />
        </form>
      </Modal>

      <Modal
        isOpen={isRenameModalOpen}
        onClose={() => setIsRenameModalOpen(false)}
        title={t("app.watchlist.rename_title")}
        description={t("app.watchlist.rename_desc")}
        footer={
          <>
            <Button variant="outline" onClick={() => setIsRenameModalOpen(false)} disabled={saving}>
              {t("app.auth.cancel")}
            </Button>
            <PrimaryButton onClick={handleRenameWatchlist} disabled={saving || !renameName.trim()}>
              {saving ? "..." : t("app.watchlist.save")}
            </PrimaryButton>
          </>
        }
      >
        <form onSubmit={handleRenameWatchlist} className="space-y-4">
          <InputField
            label={t("app.watchlist.name_label")}
            value={renameName}
            onChange={(e) => setRenameName(e.target.value)}
            placeholder={t("app.watchlist.name_placeholder")}
            required
          />
        </form>
      </Modal>

      <Modal
        isOpen={isAddItemModalOpen}
        onClose={() => {
          setIsAddItemModalOpen(false);
          setSelectedAsset(null);
          setItemNote("");
          setItemThreshold("");
        }}
        title={t("app.watchlist.add_item_title")}
        description={selectedWatchlist ? `${t("app.watchlist.add_item_desc")}: ${selectedWatchlist.name}` : ""}
        footer={
          <>
            <Button
              variant="outline"
              onClick={() => {
                setIsAddItemModalOpen(false);
                setSelectedAsset(null);
                setItemNote("");
                setItemThreshold("");
              }}
              disabled={saving}
            >
              {t("app.auth.cancel")}
            </Button>
            <PrimaryButton onClick={handleAddItem} disabled={saving || !selectedAsset}>
              {saving ? "..." : t("app.watchlist.add")}
            </PrimaryButton>
          </>
        }
      >
        <form onSubmit={handleAddItem} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-[var(--color-text-primary)]">
              {t("app.watchlist.asset_label")}
            </label>
            <StockPicker
              onSelect={(stock) => setSelectedAsset(stock)}
              placeholder={t("app.watchlist.asset_placeholder")}
            />
            {selectedAsset && (
              <p className="mt-2 text-xs text-[var(--color-text-secondary)]">
                {selectedAsset.symbol} - {selectedAsset.name}
              </p>
            )}
          </div>
          <InputField
            label={t("app.watchlist.note_label")}
            value={itemNote}
            onChange={(e) => setItemNote(e.target.value)}
            placeholder={t("app.watchlist.note_placeholder")}
          />
          <InputField
            label={t("app.watchlist.threshold_label")}
            type="number"
            value={itemThreshold}
            onChange={(e) => setItemThreshold(e.target.value)}
            placeholder={t("app.watchlist.threshold_placeholder")}
          />
        </form>
      </Modal>

      <Modal
        isOpen={isDeleteConfirmOpen}
        onClose={() => setIsDeleteConfirmOpen(false)}
        title={t("app.watchlist.delete_title")}
        description={t("app.watchlist.delete_desc").replace("{name}", selectedWatchlist?.name ?? "")}
        footer={
          <>
            <Button variant="outline" onClick={() => setIsDeleteConfirmOpen(false)} disabled={saving}>
              {t("app.auth.cancel")}
            </Button>
            <Button onClick={handleDeleteWatchlist} disabled={saving} className="bg-[var(--color-error)] hover:bg-[var(--color-error)]/90 text-white">
              {saving ? "..." : t("app.watchlist.delete")}
            </Button>
          </>
        }
      >
        <p className="text-sm text-[var(--color-text-secondary)]">
          {t("app.watchlist.delete_warning")}
        </p>
      </Modal>
    </NewDashboardShell>
  );
}
