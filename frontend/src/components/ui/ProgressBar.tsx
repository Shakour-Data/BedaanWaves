"use client";

import { cn } from "@/lib/cn";

export interface ProgressBarProps {
  /** Current step number (1-based). */
  currentStep: number;
  /** Total number of steps. */
  totalSteps: number;
  /** Optional label for screen readers describing the step purpose. */
  stepLabels?: string[];
  className?: string;
}

export function ProgressBar({
  currentStep,
  totalSteps,
  stepLabels,
  className }: ProgressBarProps) {
  const safeCurrent = Math.max(1, Math.min(currentStep, totalSteps));
  const pct = Math.round((safeCurrent / totalSteps) * 100);

  const progressPct = ((safeCurrent - 1) / (totalSteps - 1)) * 100;

  return (
    <div className={cn("w-full", className)} aria-label="Progress">
      <div className="mb-1 flex items-center justify-between">
        <span className="text-xs font-medium text-[#64748B]">
          {stepLabels?.[safeCurrent - 1] ?? `Step ${safeCurrent} of ${totalSteps}`}
        </span>
        <span className="text-xs font-medium text-[#64748B]" aria-label={`Progress: ${pct}%`}>
          {pct}%
        </span>
      </div>

      <div
        className="relative h-2 w-full overflow-hidden rounded-full bg-[#E2E8F0]"
        role="progressbar"
        aria-valuenow={pct}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div
          className="h-full bg-[#005A9C] transition-all duration-300 ease-out"
          style={{ width: `${progressPct}%` }}
        />
      </div>

      <div className="mt-1 flex justify-between">
        {Array.from({ length: totalSteps }).map((_, i) => {
          const stepNum = i + 1;
          const isActive = stepNum === safeCurrent;
          const isComplete = stepNum < safeCurrent;
          return (
            <span
              key={stepNum}
              className={cn(
                "flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold",
                "transition-colors duration-150",
                isComplete
                  ? "bg-[#10B981] text-[#FFFFFF]"
                  : isActive
                    ? "bg-[#005A9C] text-[#FFFFFF] ring-2 ring-[#005A9C]/20"
                    : "bg-[#E2E8F0] text-[#64748B]",
              )}
              aria-current={isActive ? "step" : undefined}
            >
              {stepNum}
            </span>
          );
        })}
      </div>
    </div>
  );
}
