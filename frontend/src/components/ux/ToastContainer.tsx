"use client";

import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { useUXStore, type ToastType } from "@/store/useUXStore";
import { cn } from "@/lib/cn";

const TOAST_STYLES: Record<ToastType, { bg: string; border: string; icon: string; text: string; subtext: string }> = {
  success: {
    bg: "bg-[var(--color-success)]/10",
    border: "border-[var(--color-success)]/20",
    icon: "text-[var(--color-success)]",
    text: "text-[var(--color-success)]",
    subtext: "text-[var(--color-success)]/80",
  },
  error: {
    bg: "bg-[var(--color-error)]/10",
    border: "border-[var(--color-error)]/20",
    icon: "text-[var(--color-error)]",
    text: "text-[var(--color-error)]",
    subtext: "text-[var(--color-error)]/80",
  },
  warning: {
    bg: "bg-[var(--color-warning)]/10",
    border: "border-[var(--color-warning)]/20",
    icon: "text-[var(--color-warning)]",
    text: "text-[var(--color-warning)]",
    subtext: "text-[var(--color-warning)]/80",
  },
  info: {
    bg: "bg-[var(--color-primary)]/10",
    border: "border-[var(--color-primary)]/20",
    icon: "text-[var(--color-primary)]",
    text: "text-[var(--color-primary)]",
    subtext: "text-[var(--color-primary)]/80",
  },
};

const TOAST_ICONS: Record<ToastType, string> = {
  success: "✓",
  error: "✕",
  warning: "⚠",
  info: "ℹ",
};

export function ToastContainer() {
  const { toasts, removeToast } = useUXStore();
  const [mounted, setMounted] = useState(false);

  useEffect(() => { setMounted(true); }, []); // eslint-disable-line react-hooks/set-state-in-effect

  if (!mounted) return null;

  return createPortal(
    <div className="fixed top-4 right-4 z-[100] flex flex-col gap-3 w-full max-w-sm pointer-events-none">
      {toasts.map((toast) => {
        const style = TOAST_STYLES[toast.type];
        return (
          <div
            key={toast.id}
            role="alert"
            aria-live="assertive"
            className={cn(
              "pointer-events-auto flex items-start gap-3 rounded-xl border p-4 shadow-2xl",
              "animate-in slide-in-from-right-4 fade-in duration-300",
              style.bg,
              style.border
            )}
          >
            <span className={cn("mt-0.5 text-sm font-bold", style.icon)}>
              {TOAST_ICONS[toast.type]}
            </span>
            <div className="flex-1 min-w-0">
              {toast.title && (
                <p className={cn("text-sm font-semibold", style.text)}>{toast.title}</p>
              )}
              <p className={cn("text-sm", style.subtext)}>{toast.message}</p>
              {toast.action && (
                <button
                  type="button"
                  onClick={toast.action.onClick}
                  className={cn("mt-2 text-sm font-semibold underline", style.text)}
                >
                  {toast.action.label}
                </button>
              )}
            </div>
            <button
              type="button"
              onClick={() => removeToast(toast.id)}
              className={cn("text-xs opacity-60 hover:opacity-100 transition-opacity", style.text)}
              aria-label="Dismiss notification"
            >
              ✕
            </button>
          </div>
        );
      })}
    </div>,
    document.body
  );
}