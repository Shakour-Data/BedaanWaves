"use client";

import { cn } from "@/lib/cn";

export interface ProgressBarProps {
  currentStep: number;
  totalSteps: number;
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
        <span className="text-xs font-medium text-muted-foreground">
          {stepLabels?.[safeCurrent - 1] ?? `Step ${safeCurrent} of ${totalSteps}`}
        </span>
        <span className="text-xs font-medium text-muted-foreground" aria-label={`Progress: ${pct}%`}>
          {pct}%
        </span>
      </div>

      <div
        className="relative h-2 w-full overflow-hidden rounded-full bg-border"
        role="progressbar"
        aria-valuenow={pct}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div
          className="h-full bg-primary transition-all duration-300 ease-out"
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
                  ? "bg-success text-white"
                  : isActive
                    ? "bg-primary text-white ring-2 ring-primary/20"
                    : "bg-border text-muted-foreground",
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
