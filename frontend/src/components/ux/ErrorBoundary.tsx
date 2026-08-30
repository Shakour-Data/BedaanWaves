"use client";

import { Component, ReactNode } from "react";
import { useUXStore } from "@/store/useUXStore";

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: { componentStack: string }) {
    console.error("ErrorBoundary caught an error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }
      return <DefaultErrorFallback error={this.state.error} onReset={() => this.setState({ hasError: false, error: null })} />;
    }

    return this.props.children;
  }
}

function DefaultErrorFallback({
  error,
  onReset,
}: {
  error: Error | null;
  onReset: () => void;
}) {
  const addToast = useUXStore((state) => state.addToast);

  const handleReport = () => {
    addToast({
      type: "info",
      message: "Error report copied to clipboard (simulated).",
    });
  };

  return (
    <div className="flex min-h-[60vh] items-center justify-center p-4">
      <div className="max-w-md w-full rounded-2xl border border-[var(--color-error)]/20 bg-[var(--color-error)]/5 p-8 text-center">
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-[var(--color-error)]/10 text-[var(--color-error)] text-xl">
          ✕
        </div>
        <h2 className="mb-2 text-xl font-bold text-[var(--color-text-primary)]">
          Something went wrong
        </h2>
        <p className="mb-6 text-sm text-[var(--color-text-secondary)]">
          {error?.message || "An unexpected error occurred. Please try again."}
        </p>
        <div className="flex items-center justify-center gap-3">
          <button
            type="button"
            onClick={onReset}
            className="rounded-lg bg-[var(--color-primary)] px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-[var(--color-primary-hover)]"
          >
            Try again
          </button>
          <button
            type="button"
            onClick={handleReport}
            className="rounded-lg border border-[var(--color-border)] px-5 py-2.5 text-sm font-medium text-[var(--color-text-secondary)] transition-colors hover:bg-[var(--color-background)]"
          >
            Report issue
          </button>
        </div>
      </div>
    </div>
  );
}
