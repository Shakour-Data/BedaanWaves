/**
 * useDateStore.ts
 * ---------------------------------------------------------------------------
 * Centralized date management for the entire application.
 * 
 * PURPOSE:
 * - Fix data inconsistency between Spider Chart and Trend Chart
 * - Ensure all charts use the same reference date
 * - Provide a single source of truth for date selection
 * 
 * USAGE:
 * - All charts should use the date from this store
 * - When date changes, all charts will automatically update
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";

interface DateState {
  selectedDate: string | null;
  latestAvailableDate: string | null;
  useLatestDate: boolean;
  setSelectedDate: (date: string | null) => void;
  setLatestAvailableDate: (date: string | null) => void;
  setUseLatestDate: (use: boolean) => void;
  setLiveLatestFromStream: (timestampIso: string) => void;
  getEffectiveDate: () => string | null;
  reset: () => void;
}

export const useDateStore = create<DateState>()(
  persist(
    (set, get) => ({
      // Initial state
      selectedDate: null,
      latestAvailableDate: null,
      useLatestDate: true,

      // Actions
      setSelectedDate: (date) => {
        set({ selectedDate: date });
        // When manually selecting a date, disable auto-latest
        if (date) {
          set({ useLatestDate: false });
        }
      },

      setLatestAvailableDate: (date) => {
        const currentLatest = get().latestAvailableDate;
        set({ latestAvailableDate: date });
        
        // If this is the first time setting latest date and useLatestDate is true,
        // also set selectedDate to this date
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
        if (timestampIso.includes('T')) {
          dateOnly = timestampIso.split('T')[0];
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
        });
      },
    }),
    {
      name: "date-storage",
      partialize: (state) => ({
        selectedDate: state.selectedDate,
        useLatestDate: state.useLatestDate,
      }),
    }
  )
);

// Selector hooks for better performance
export const useSelectedDate = () => useDateStore((state) => state.selectedDate);
export const useLatestAvailableDate = () => useDateStore((state) => state.latestAvailableDate);
export const useEffectiveDate = () => useDateStore((state) => state.getEffectiveDate());
export const useUseLatestDate = () => useDateStore((state) => state.useLatestDate);
