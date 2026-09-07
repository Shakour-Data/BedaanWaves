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
  selectedSnapshotId: string | null;

  // Actions
  setSelectedDate: (date: string | null) => void;
  setLatestAvailableDate: (date: string | null) => void;
  setUseLatestDate: (use: boolean) => void;
  setLiveLatestFromStream: (timestampIso: string) => void;
  getEffectiveDate: () => string | null;
  reset: () => void;

  // Snapshot actions
  setSnapshot: (snap: SnapshotResponse | null, symbol?: string | null) => void;
  setSnapshotLoading: (loading: boolean) => void;
  setSnapshotError: (error: string | null) => void;
  setSnapshotIndex: (idx: SnapshotIndexResponse | null) => void;
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
      selectedSnapshotId: null,

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
        set((state) => {
          state.selectedDate = null;
          state.latestAvailableDate = null;
          state.useLatestDate = true;
          state.snapshot = null;
          state.snapshotId = null;
          state.snapshotTimestamp = null;
          state.snapshotSymbol = null;
          state.snapshotLoading = false;
          state.snapshotError = null;
          state.snapshotIndex = null;
          state.selectedSnapshotId = null;
          return state;
        });
      },

      // ---- Snapshot actions ----
      setSnapshot: (snap, symbol = null) => {
        if (!snap) {
          set((state) => {
            state.snapshot = null;
            state.snapshotId = null;
            state.snapshotTimestamp = null;
            state.snapshotSymbol = symbol;
            state.snapshotError = null;
            return state;
          });
          return;
        }
        set((state) => {
          state.snapshot = snap;
          state.snapshotId = snap.snapshotId;
          state.snapshotTimestamp = snap.timestamp;
          state.snapshotSymbol = symbol ?? null;
          state.snapshotError = null;
          return state;
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

      setSnapshotLoading: (loading: boolean) => {
        set((state) => {
          state.snapshotLoading = loading;
          return state;
        });
      },

      setSnapshotError: (error: string | null) => {
        set((state) => {
          state.snapshotError = error;
          return state;
        });
      },

      setSnapshotIndex: (idx: SnapshotIndexResponse | null) => {
        set((state) => {
          state.snapshotIndex = idx;
          return state;
        });
      },

      clearSnapshot: () => {
        set((state) => {
          state.snapshot = null;
          state.snapshotId = null;
          state.snapshotTimestamp = null;
          state.snapshotError = null;
          return state;
        });
      },

      loadSnapshot: async (options) => {
        set((state) => {
          state.snapshotLoading = true;
          state.snapshotError = null;
          return state;
        });
        try {
          const snap = await fetchDashboardSnapshot(options);
          get().setSnapshot(snap, options?.symbol ?? null);
          return snap;
        } catch (err) {
          const msg = err instanceof Error ? err.message : String(err);
          set((state) => {
            state.snapshotLoading = false;
            state.snapshotError = msg;
            return state;
          });
          return null;
        } finally {
          set((state) => {
            state.snapshotLoading = false;
            return state;
          });
        }
      },

      loadSnapshotIndex: async (opts) => {
        try {
          const idx = await fetchDashboardSnapshots(opts);
          set((state) => {
            state.snapshotIndex = idx;
            return state;
          });
          return idx;
        } catch {
          return null;
        }
      },

      selectSnapshotById: async (id) => {
        if (!id) {
          get().clearSnapshot();
          set((state) => {
            state.selectedSnapshotId = null;
            return state;
          });
          return null;
        }
        set((state) => {
          state.selectedSnapshotId = id;
          return state;
        });
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
