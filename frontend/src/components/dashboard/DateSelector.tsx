/**
 * DateSelector.tsx
 * ---------------------------------------------------------------------------
 * Centralized date selector component for the dashboard.
 * 
 * PURPOSE:
 * - Provides a unified date selection interface
 * - Ensures all charts use the same reference date
 * - Shows the latest available date from the backend
 */

"use client";

import { useState, useEffect } from "react";
import { cn } from "@/lib/cn";
import { useDateStore } from "@/store/useDateStore";

interface DateSelectorProps {
  className?: string;
  variant?: "compact" | "full";
}

export function DateSelector({ className, variant = "compact" }: DateSelectorProps) {
  const {
    selectedDate,
    latestAvailableDate,
    useLatestDate,
    setSelectedDate,
    setUseLatestDate,
  } = useDateStore();

  const [dateInput, setDateInput] = useState(selectedDate || "");

  // Sync input with store
  useEffect(() => {
    if (selectedDate) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setDateInput(selectedDate);
    }
  }, [selectedDate]);

  const handleDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newDate = e.target.value;
    setDateInput(newDate);
    if (newDate) {
      setSelectedDate(newDate);
    }
  };

  const handleUseLatestToggle = () => {
    setUseLatestDate(!useLatestDate);
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return "—";
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
      });
    } catch {
      return dateStr;
    }
  };

  if (variant === "compact") {
    return (
      <div className={cn("flex items-center gap-3", className)}>
        <div className="flex items-center gap-2">
          <span className="text-xs text-[var(--color-text-secondary)]">Date:</span>
          <input
            type="date"
            value={dateInput}
            onChange={handleDateChange}
            max={latestAvailableDate || undefined}
            className="h-7 rounded border border-[var(--color-border)] bg-[var(--color-background)] px-2 text-xs text-[var(--color-text-primary)] focus:border-[var(--color-primary)] focus:outline-none"
          />
        </div>
        
        <label className="flex cursor-pointer items-center gap-1.5">
          <input
            type="checkbox"
            checked={useLatestDate}
            onChange={handleUseLatestToggle}
            className="h-3.5 w-3.5 rounded border-[var(--color-border)] text-[var(--color-primary)] focus:ring-[var(--color-primary)]"
          />
          <span className="text-xs text-[var(--color-text-secondary)]">Auto (latest)</span>
        </label>

        {latestAvailableDate && (
          <span className="text-[10px] text-[var(--color-text-secondary)]">
            Latest: {formatDate(latestAvailableDate)}
          </span>
        )}
      </div>
    );
  }

  // Full variant
  return (
    <div className={cn("rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-4", className)}>
      <div className="mb-3">
        <h3 className="text-sm font-semibold text-[var(--color-text-primary)]">Date Selection</h3>
        <p className="text-xs text-[var(--color-text-secondary)]">
          Select a date to synchronize all charts
        </p>
      </div>

      <div className="space-y-3">
        <div>
          <label className="mb-1 block text-xs text-[var(--color-text-secondary)]">Selected Date</label>
          <input
            type="date"
            value={dateInput}
            onChange={handleDateChange}
            max={latestAvailableDate || undefined}
            className="w-full rounded border border-[var(--color-border)] bg-[var(--color-background)] px-3 py-2 text-sm text-[var(--color-text-primary)] focus:border-[var(--color-primary)] focus:outline-none"
          />
        </div>

        <label className="flex cursor-pointer items-center gap-2 rounded border border-[var(--color-border)] bg-[var(--color-background)] p-3 transition-colors hover:bg-[var(--color-surface)]">
          <input
            type="checkbox"
            checked={useLatestDate}
            onChange={handleUseLatestToggle}
            className="h-4 w-4 rounded border-[var(--color-border)] text-[var(--color-primary)] focus:ring-[var(--color-primary)]"
          />
          <div className="flex-1">
            <div className="text-sm font-medium text-[var(--color-text-primary)]">Use Latest Date Automatically</div>
            <div className="text-xs text-[var(--color-text-secondary)]">
              Always use the most recent available data
            </div>
          </div>
        </label>

        {latestAvailableDate && (
          <div className="rounded bg-[var(--color-background)] p-3">
            <div className="text-xs text-[var(--color-text-secondary)]">Latest Available Data</div>
            <div className="text-sm font-semibold text-[var(--color-text-primary)]">
              {formatDate(latestAvailableDate)}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default DateSelector;
