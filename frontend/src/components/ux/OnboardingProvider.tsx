"use client";

import { useState, useEffect } from "react";
import { usePathname } from "next/navigation";
import { useUXStore } from "@/store/useUXStore";

const STORAGE_KEY = "bedaanwaves-onboarding-completed";

const STEPS = [
  {
    target: "[data-search-input]",
    title: "Search stocks",
    content:
      "Use the search bar to find any NASDAQ stock by ticker or company name. Press Enter or click a result to navigate.",
    placement: "bottom" as const,
  },
  {
    target: "[data-sidebar]",
    title: "Navigate your dashboard",
    content:
      "Use the sidebar to jump between Dashboard, Stocks, Scoring, Analysis, Portfolio, News, and more.",
    placement: "right" as const,
  },
  {
    target: "[data-watchlist]",
    title: "Build your watchlist",
    content:
      "Add stocks to your watchlist for quick access. Click any stock in your list to see detailed scoring and risk metrics.",
    placement: "left" as const,
  },
];

export function OnboardingProvider() {
  const [active, setActive] = useState(false);
  const [step, setStep] = useState(0);
  const pathname = usePathname();
  const addToast = useUXStore((state) => state.addToast);

  const skipTour = () => {
    setActive(false);
    if (typeof window !== "undefined") {
      localStorage.setItem(STORAGE_KEY, "true");
    }
    addToast({ type: "info", message: "You can restart the tour from Settings anytime." });
  };

  const completeTour = () => {
    setActive(false);
    if (typeof window !== "undefined") {
      localStorage.setItem(STORAGE_KEY, "true");
    }
    addToast({ type: "success", message: "You are all set! Happy analyzing." });
  };

  const nextStep = () => {
    if (step < STEPS.length - 1) {
      setStep((s) => s + 1);
    } else {
      completeTour();
    }
  };

  useEffect(() => {
    if (typeof window === "undefined") return;
    const completed = localStorage.getItem(STORAGE_KEY) === "true";
    if (!completed && pathname === "/dashboard") {
      const timer = setTimeout(() => setActive(true), 800);
      return () => clearTimeout(timer);
    }
  }, [pathname]);

  if (!active) return null;

  return (
    <div className="fixed inset-0 z-[80] flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
      <div className="w-full max-w-md rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-2xl p-6 animate-in zoom-in-95 fade-in duration-200">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-[var(--color-primary)]">
              {step + 1} / {STEPS.length}
            </span>
            <div className="h-1.5 w-24 rounded-full bg-[var(--color-border)] overflow-hidden">
              <div
                className="h-full rounded-full bg-[var(--color-primary)] transition-all duration-300"
                style={{ width: `${((step + 1) / STEPS.length) * 100}%` }}
              />
            </div>
          </div>
          <button
            type="button"
            onClick={skipTour}
            className="text-xs text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] transition-colors"
          >
            Skip
          </button>
        </div>
        <h3 className="text-lg font-bold text-[var(--color-text-primary)] mb-2">
          {STEPS[step].title}
        </h3>
        <p className="text-sm text-[var(--color-text-secondary)] mb-6">
          {STEPS[step].content}
        </p>
        <div className="flex items-center justify-end gap-3">
          <button
            type="button"
            onClick={skipTour}
            className="rounded-lg border border-[var(--color-border)] px-4 py-2 text-sm font-medium text-[var(--color-text-secondary)] transition-colors hover:bg-[var(--color-background)]"
          >
            Skip
          </button>
          <button
            type="button"
            onClick={nextStep}
            className="rounded-lg bg-[var(--color-primary)] px-5 py-2 text-sm font-medium text-white transition-colors hover:bg-[var(--color-primary-hover)]"
          >
            {step < STEPS.length - 1 ? "Next" : "Finish"}
          </button>
        </div>
      </div>
    </div>
  );
}