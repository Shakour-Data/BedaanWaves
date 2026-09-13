"use client";

import { Component, ReactNode } from "react";
import { Button } from "./ui/Button";

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
      return (
        <div className="flex min-h-screen items-center justify-center p-4">
          <div className="max-w-md rounded-xl border border-error/20 bg-error/5 p-6 text-center">
            <h2 className="mb-2 text-lg font-semibold text-error">Something went wrong</h2>
            <p className="mb-4 text-sm text-error/80">
              {this.state.error?.message || "An unexpected error occurred"}
            </p>
            <Button onClick={() => this.setState({ hasError: false, error: null })}>
              Try again
            </Button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
