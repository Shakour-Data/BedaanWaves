"use client";

import { useMemo } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  createWatchlist,
  updateWatchlist,
  deleteWatchlist,
  addWatchlistItem,
  removeWatchlistItem,
  type Watchlist as WatchlistType,
  type CreateWatchlistPayload,
  type UpdateWatchlistPayload,
} from "@/lib/api/watchlist";
import { QK } from "@/lib/query-keys";
import { t } from "@/lib/i18n";
import { getApiErrorMessage } from "@/lib/api";
import { useUXStore } from "@/store/useUXStore";

export function useWatchlistActions(
  watchlists: WatchlistType[],
  selectedWatchlistId: string | null,
) {
  const addToast = useUXStore((state) => state.addToast);
  const queryClient = useQueryClient();

  const selectedWatchlist = watchlists.find((w) => w.id === selectedWatchlistId) ?? null;

  const invalidate = () => queryClient.invalidateQueries({ queryKey: QK.watchlists() });

  const createMut = useMutation({
    mutationFn: ({ name, description }: { name: string; description: string }) => {
      const payload: CreateWatchlistPayload = { name: name.trim(), description: description.trim() || null };
      return createWatchlist(payload);
    },
    onSuccess: (created) => {
      invalidate();
      addToast({ type: "success", message: t("app.watchlist.created") });
      // The page effect will handle selecting the new watchlist
    },
    onError: (err) => {
      const message = getApiErrorMessage(err);
      addToast({ type: "error", message: message || t("app.watchlist.error_creating") });
    },
  });

  const renameMut = useMutation({
    mutationFn: ({ id, newName }: { id: string; newName: string }) => {
      const payload: UpdateWatchlistPayload = { name: newName.trim() };
      return updateWatchlist(id, payload);
    },
    onSuccess: () => {
      invalidate();
      addToast({ type: "success", message: t("app.watchlist.renamed") });
    },
    onError: (err) => {
      const message = getApiErrorMessage(err);
      addToast({ type: "error", message: message || t("app.watchlist.error_updating") });
    },
  });

  const deleteMut = useMutation({
    mutationFn: (id: string) => deleteWatchlist(id),
    onSuccess: () => {
      invalidate();
      addToast({ type: "success", message: t("app.watchlist.deleted") });
    },
    onError: (err) => {
      const message = getApiErrorMessage(err);
      addToast({ type: "error", message: message || t("app.watchlist.error_deleting") });
    },
  });

  const addItemMut = useMutation({
    mutationFn: ({ watchlistId, assetId, note, threshold }: {
      watchlistId: string; assetId: string; note: string | null; threshold: number | null;
    }) => addWatchlistItem(watchlistId, { asset_id: assetId, note, alert_threshold_pct: threshold }),
    onSuccess: () => {
      invalidate();
      addToast({ type: "success", message: t("app.watchlist.item_added") });
    },
    onError: (err) => {
      const message = getApiErrorMessage(err);
      addToast({ type: "error", message: message || t("app.watchlist.error_adding_item") });
    },
  });

  const removeItemMut = useMutation({
    mutationFn: ({ watchlistId, itemId }: { watchlistId: string; itemId: string }) =>
      removeWatchlistItem(watchlistId, itemId),
    onSuccess: () => {
      invalidate();
      addToast({ type: "success", message: t("app.watchlist.item_removed") });
    },
    onError: (err) => {
      const message = getApiErrorMessage(err);
      addToast({ type: "error", message: message || t("app.watchlist.error_removing_item") });
    },
  });

  const saving = createMut.isPending || renameMut.isPending || deleteMut.isPending
    || addItemMut.isPending || removeItemMut.isPending;

  const handleCreate = useMemo(() =>
    (name: string, description: string) => createMut.mutate({ name, description }),
    [createMut]);

  const handleRename = useMemo(() =>
    (newName: string) => {
      if (!selectedWatchlist) return;
      renameMut.mutate({ id: selectedWatchlist.id, newName });
    },
    [selectedWatchlist, renameMut]);

  const handleDelete = useMemo(() =>
    () => {
      if (!selectedWatchlist) return;
      deleteMut.mutate(selectedWatchlist.id);
    },
    [selectedWatchlist, deleteMut]);

  const handleAddItem = useMemo(() =>
    (assetId: string, note: string | null, threshold: number | null) => {
      if (!selectedWatchlist) return;
      addItemMut.mutate({ watchlistId: selectedWatchlist.id, assetId, note, threshold });
    },
    [selectedWatchlist, addItemMut]);

  const handleRemoveItem = useMemo(() =>
    (itemId: string) => {
      if (!selectedWatchlist) return;
      removeItemMut.mutate({ watchlistId: selectedWatchlist.id, itemId });
    },
    [selectedWatchlist, removeItemMut]);

  return {
    saving,
    selectedWatchlist,
    handleCreate,
    handleRename,
    handleDelete,
    handleAddItem,
    handleRemoveItem,
  };
}
