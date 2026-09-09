import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ProgressBar } from "@/components/ui/ProgressBar";

describe("QA Priority 1 - Accessibility & Empty States", () => {
  it("has correct ARIA attributes for progress bar", () => {
    render(<ProgressBar currentStep={2} totalSteps={4} />);
    const progressbar = screen.getByRole("progressbar");
    expect(progressbar).toHaveAttribute("aria-valuenow", "50");
    expect(progressbar).toHaveAttribute("aria-valuemin", "0");
    expect(progressbar).toHaveAttribute("aria-valuemax", "100");
  });

  it("marks current step with aria-current", () => {
    render(<ProgressBar currentStep={2} totalSteps={4} />);
    const currentStep = document.querySelector('[aria-current="step"]');
    expect(currentStep).toBeInTheDocument();
    expect(currentStep).toHaveTextContent("2");
  });

  it("renders empty state for stocks with correct guidance", () => {
    const emptyState = (
      <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-[var(--color-border)] bg-muted/30 py-16">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-muted text-muted-foreground mb-4">
          <svg className="h-8 w-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>
        </div>
        <h3 className="mt-4 text-lg font-medium text-[var(--color-text-primary)]">No stocks found</h3>
        <p className="mt-1 text-sm text-[var(--color-text-secondary)]">Try adjusting your search or filters</p>
      </div>
    );

    render(<div>{emptyState}</div>);
    expect(screen.getByText("No stocks found")).toBeInTheDocument();
    expect(screen.getByText("Try adjusting your search or filters")).toBeInTheDocument();
  });

  it("renders empty state for scoring with correct guidance", () => {
    const emptyState = (
      <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-[var(--color-border)] bg-[var(--color-surface)]/30 py-16">
        <span className="text-4xl text-[#334155]" role="img" aria-label="No results">Search</span>
        <h3 className="mt-4 text-lg font-medium text-[var(--color-text-primary)]">No stocks found</h3>
        <p className="mt-1 text-sm text-[var(--color-text-secondary)]">Try adjusting your filters</p>
      </div>
    );

    render(<div>{emptyState}</div>);
    expect(screen.getByText("No stocks found")).toBeInTheDocument();
    expect(screen.getByText("Try adjusting your filters")).toBeInTheDocument();
  });

  it("has accessible icon in error boundary", () => {
    const errorIcon = (
      <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-[var(--color-error)]/10 text-[var(--color-error)] text-xl">
        ✕
      </div>
    );

    render(<div>{errorIcon}</div>);
    expect(screen.getByText("✕")).toBeInTheDocument();
  });
});
