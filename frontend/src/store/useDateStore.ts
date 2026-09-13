/**
 * useDateStore.ts
 * ---------------------------------------------------------------------------
 * Centralized date + unified temporal snapshot management for the entire app.
 *
 * PURPOSE:
 * - Fix data inconsistency between Spider Chart and Trend Chart
 * - Ensure all charts use the same reference date AND the same snapshotId
 * - Provide a single source of truth for date + snapshot selection
 *
 * USAGE:
 * - All analytical widgets consume snapshot from this store
 * - When snapshotId changes, all charts automatically re-render with parity
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type {
  SnapshotResponse,
  SnapshotIndexResponse,
  FetchSnapshotOptions,
} from "@/lib/api/dashboard";
import { fetchDashboardSnapshot, fetchDashboardSnapshots } from "@/lib/api/dashboard";

interface DateState {
  // Legacy date state
  selectedDate: string | null;
  latestAvailableDate: string | null;
  useLatestDate: boolean;

  // Snapshot state (Temporal Scoring Snapshot Spec)
  snapshot: SnapshotResponse | null;
  snapshotId: string | null;
  snapshotTimestamp: string | null;
  snapshotSymbol: string | null;
  snapshotLoading: boolean;
  snapshotError: string | null;
  snapshotIndex: SnapshotIndexResponse | null;

  // Actions
  setSelectedDate: (date: string | null) => void;
  setLatestAvailableDate: (date: string | null) => void;
  setUseLatestDate: (use: boolean) => void;
  setLiveLatestFromStream: (timestampIso: string) => void;
  getEffectiveDate: () => string | null;
  reset: () => void;

  // Snapshot actions
  setSnapshot: (snap: SnapshotResponse | null, symbol?: string | null) => void;
  clearSnapshot: () => void;
  loadSnapshot: (options?: FetchSnapshotOptions) => Promise<SnapshotResponse | null>;
  loadSnapshotIndex: (opts?: {
    hourly_limit?: number;
    daily_limit?: number;
  }) => Promise<SnapshotIndexResponse | null>;
  selectSnapshotById: (id: string) => Promise<SnapshotResponse | null>;
}

export const useDateStore = create<DateState>()(
  persist(
    (set, get) => ({
      // Initial state - legacy date fields
      selectedDate: null,
      latestAvailableDate: null,
      useLatestDate: true,

      // Initial state - snapshot fields (never persisted)
      snapshot: null,
      snapshotId: null,
      snapshotTimestamp: null,
      snapshotSymbol: null,
      snapshotLoading: false,
      snapshotError: null,
      snapshotIndex: null,

      // ---- Legacy date actions ----
      setSelectedDate: (date) => {
        set({ selectedDate: date });
        if (date) {
          set({ useLatestDate: false });
        }
      },

      setLatestAvailableDate: (date) => {
        const currentLatest = get().latestAvailableDate;
        set({ latestAvailableDate: date });

        if (!currentLatest && get().useLatestDate && date) {
          set({ selectedDate: date });
        }
      },

      setUseLatestDate: (use) => {
        set({ useLatestDate: use });
        if (use && get().latestAvailableDate) {
          set({ selectedDate: get().latestAvailableDate });
        }
      },

      setLiveLatestFromStream: (timestampIso) => {
        if (!timestampIso) return;
        let dateOnly = timestampIso;
        if (timestampIso.includes("T")) {
          dateOnly = timestampIso.split("T")[0];
        }
        const current = get().latestAvailableDate;
        if (current !== dateOnly) {
          set({ latestAvailableDate: dateOnly });
          if (get().useLatestDate) {
            set({ selectedDate: dateOnly });
          }
        }
      },

      getEffectiveDate: () => {
        const state = get();
        if (state.useLatestDate) {
          return state.latestAvailableDate;
        }
        return state.selectedDate;
      },

      reset: () => {
        set({
          selectedDate: null,
          latestAvailableDate: null,
          useLatestDate: true,
          snapshot: null,
          snapshotId: null,
          snapshotTimestamp: null,
          snapshotSymbol: null,
          snapshotLoading: false,
          snapshotError: null,
          snapshotIndex: null,
        });
      },

      // ---- Snapshot actions ----
      setSnapshot: (snap, symbol = null) => {
        if (!snap) {
          set({
            snapshot: null,
            snapshotId: null,
            snapshotTimestamp: null,
            snapshotSymbol: symbol,
            snapshotError: null,
          });
          return;
        }
        set({
          snapshot: snap,
          snapshotId: snap.snapshotId,
          snapshotTimestamp: snap.timestamp,
          snapshotSymbol: symbol ?? null,
          snapshotError: null,
        });
        // Update latest available date from snapshot timestamp parity
        if (snap.timestamp) {
          const snapDate = snap.timestamp.split("T")[0];
          if (snapDate) {
            const current = get().latestAvailableDate;
            if (!current || snapDate > current) {
              get().setLatestAvailableDate(snapDate);
            }
          }
        }
      },

      clearSnapshot: () => {
        set({
          snapshot: null,
          snapshotId: null,
          snapshotTimestamp: null,
          snapshotError: null,
        });
      },

      loadSnapshot: async (options) => {
        set({ snapshotLoading: true, snapshotError: null });
        try {
          const snap = await fetchDashboardSnapshot(options);
          get().setSnapshot(snap, options?.symbol ?? null);
          return snap;
        } catch (err) {
          const msg = err instanceof Error ? err.message : String(err);
          set({ snapshotLoading: false, snapshotError: msg });
          return null;
        } finally {
          set({ snapshotLoading: false });
        }
      },

      loadSnapshotIndex: async (opts) => {
        try {
          const idx = await fetchDashboardSnapshots(opts);
          set({ snapshotIndex: idx });
          return idx;
        } catch {
          return null;
        }
      },

      selectSnapshotById: async (id) => {
        if (!id) {
          get().clearSnapshot();
          return null;
        }
        if (get().snapshotId === id && get().snapshot) {
          return get().snapshot;
        }
        return await get().loadSnapshot({ snapshotId: id });
      },
    }),
    {
      name: "date-storage",
      partialize: (state) => ({
        // Persist only lightweight user preferences; never persist full snapshot
        selectedDate: state.selectedDate,
        useLatestDate: state.useLatestDate,
      }),
    },
  ),
);

// Selector hooks for better performance
export const useSelectedDate = () => useDateStore((state) => state.selectedDate);
export const useLatestAvailableDate = () =>
  useDateStore((state) => state.latestAvailableDate);
export const useEffectiveDate = () => useDateStore((state) => state.getEffectiveDate());
export const useUseLatestDate = () => useDateStore((state) => state.useLatestDate);

// Snapshot-specific selectors
export const useSnapshot = () => useDateStore((state) => state.snapshot);
export const useSnapshotId = () => useDateStore((state) => state.snapshotId);
export const useSnapshotTimestamp = () =>
  useDateStore((state) => state.snapshotTimestamp);
export const useSnapshotSymbol = () => useDateStore((state) => state.snapshotSymbol);
export const useSnapshotLoading = () => useDateStore((state) => state.snapshotLoading);
export const useSnapshotError = () => useDateStore((state) => state.snapshotError);
export const useSnapshotIndex = () => useDateStore((state) => state.snapshotIndex);

export const useLoadSnapshot = () => useDateStore((state) => state.loadSnapshot);
export const useSetSnapshot = () => useDateStore((state) => state.setSnapshot);
export const useClearSnapshot = () => useDateStore((state) => state.clearSnapshot);
export const useLoadSnapshotIndex = () =>
  useDateStore((state) => state.loadSnapshotIndex);
export const useSelectSnapshotById = () =>
  useDateStore((state) => state.selectSnapshotById);

export type {
  SnapshotResponse,
  SnapshotIndexResponse,
  SnapshotIndexEntry,
  HierarchyScores,
  DeltaFrame,
  FetchSnapshotOptions,
  WeightSnapshot,
  WeightTrendPoint,
  WeightDeltaPoint,
  TrendPoint,
  SnapshotTier,
} from "@/lib/api/dashboard";
