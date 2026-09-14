"use client";

import { Button } from "@/components/ui/Button";
import { InputField } from "@/components/ui/InputField";
import { Modal } from "@/components/ui/Modal";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { StockPicker } from "@/components/search/StockPicker";
import { t } from "@/lib/i18n";
import type { WatchlistType } from "./types";

interface CreateWatchlistModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (name: string, description: string) => void;
  saving: boolean;
  name: string;
  onNameChange: (v: string) => void;
  description: string;
  onDescriptionChange: (v: string) => void;
}

export function CreateWatchlistModal({
  isOpen,
  onClose,
  onSubmit,
  saving,
  name,
  onNameChange,
  description,
  onDescriptionChange,
}: CreateWatchlistModalProps) {
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={t("app.watchlist.create_title")}
      description={t("app.watchlist.create_desc")}
      footer={
        <>
          <Button variant="outline" onClick={onClose} disabled={saving}>
            {t("app.auth.cancel")}
          </Button>
          <PrimaryButton onClick={() => onSubmit(name, description)} disabled={saving || !name.trim()}>
            {saving ? "..." : t("app.watchlist.create_button")}
          </PrimaryButton>
        </>
      }
    >
      <form onSubmit={(e) => { e.preventDefault(); onSubmit(name, description); }} className="space-y-4">
        <InputField
          label={t("app.watchlist.name_label")}
          value={name}
          onChange={(e) => onNameChange(e.target.value)}
          placeholder={t("app.watchlist.name_placeholder")}
          required
        />
        <InputField
          label={t("app.watchlist.description_label")}
          value={description}
          onChange={(e) => onDescriptionChange(e.target.value)}
          placeholder={t("app.watchlist.description_placeholder")}
        />
      </form>
    </Modal>
  );
}

interface RenameWatchlistModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (newName: string) => void;
  saving: boolean;
  name: string;
  onNameChange: (v: string) => void;
}

export function RenameWatchlistModal({
  isOpen,
  onClose,
  onSubmit,
  saving,
  name,
  onNameChange,
}: RenameWatchlistModalProps) {
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={t("app.watchlist.rename_title")}
      description={t("app.watchlist.rename_desc")}
      footer={
        <>
          <Button variant="outline" onClick={onClose} disabled={saving}>
            {t("app.auth.cancel")}
          </Button>
          <PrimaryButton onClick={() => onSubmit(name)} disabled={saving || !name.trim()}>
            {saving ? "..." : t("app.watchlist.save")}
          </PrimaryButton>
        </>
      }
    >
      <form onSubmit={(e) => { e.preventDefault(); onSubmit(name); }} className="space-y-4">
        <InputField
          label={t("app.watchlist.name_label")}
          value={name}
          onChange={(e) => onNameChange(e.target.value)}
          placeholder={t("app.watchlist.name_placeholder")}
          required
        />
      </form>
    </Modal>
  );
}

interface AddItemModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: () => void;
  saving: boolean;
  selectedWatchlist: WatchlistType | null;
  selectedAsset: { symbol: string; name: string } | null;
  onAssetSelect: (asset: { symbol: string; name: string } | null) => void;
  note: string;
  onNoteChange: (v: string) => void;
  threshold: string;
  onThresholdChange: (v: string) => void;
}

export function AddItemModal({
  isOpen,
  onClose,
  onSubmit,
  saving,
  selectedWatchlist,
  selectedAsset,
  onAssetSelect,
  note,
  onNoteChange,
  threshold,
  onThresholdChange,
}: AddItemModalProps) {
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={t("app.watchlist.add_item_title")}
      description={selectedWatchlist ? `${t("app.watchlist.add_item_desc")}: ${selectedWatchlist.name}` : ""}
      footer={
        <>
          <Button variant="outline" onClick={onClose} disabled={saving}>
            {t("app.auth.cancel")}
          </Button>
          <PrimaryButton onClick={onSubmit} disabled={saving || !selectedAsset}>
            {saving ? "..." : t("app.watchlist.add")}
          </PrimaryButton>
        </>
      }
    >
      <form onSubmit={(e) => { e.preventDefault(); onSubmit(); }} className="space-y-4">
        <div>
          <label className="mb-1 block text-sm font-medium text-[var(--color-text-primary)]">
            {t("app.watchlist.asset_label")}
          </label>
          <StockPicker
            onSelect={onAssetSelect}
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
          value={note}
          onChange={(e) => onNoteChange(e.target.value)}
          placeholder={t("app.watchlist.note_placeholder")}
        />
        <InputField
          label={t("app.watchlist.threshold_label")}
          type="number"
          value={threshold}
          onChange={(e) => onThresholdChange(e.target.value)}
          placeholder={t("app.watchlist.threshold_placeholder")}
        />
      </form>
    </Modal>
  );
}

interface DeleteConfirmModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  saving: boolean;
  watchlistName: string;
}

export function DeleteConfirmModal({
  isOpen,
  onClose,
  onConfirm,
  saving,
  watchlistName,
}: DeleteConfirmModalProps) {
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={t("app.watchlist.delete_title")}
      description={t("app.watchlist.delete_desc").replace("{name}", watchlistName)}
      footer={
        <>
          <Button variant="outline" onClick={onClose} disabled={saving}>
            {t("app.auth.cancel")}
          </Button>
          <Button onClick={onConfirm} disabled={saving} className="bg-[var(--color-error)] hover:bg-[var(--color-error)]/90 text-white">
            {saving ? "..." : t("app.watchlist.delete")}
          </Button>
        </>
      }
    >
      <p className="text-sm text-[var(--color-text-secondary)]">
        {t("app.watchlist.delete_warning")}
      </p>
    </Modal>
  );
}
