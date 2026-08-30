"use client";

import { useEffect, useRef, useCallback } from "react";
import { createPortal } from "react-dom";
import { useUXStore } from "@/store/useUXStore";
import { cn } from "@/lib/cn";

export function Modal() {
  const { modal, closeModal } = useUXStore();
  const overlayRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!modal.isOpen) return;

    previousFocusRef.current = document.activeElement as HTMLElement | null;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        closeModal();
        return;
      }

      if (e.key === "Tab" && contentRef.current) {
        const focusable = contentRef.current.querySelectorAll(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        if (focusable.length === 0) return;

        const first = focusable[0] as HTMLElement;
        const last = focusable[focusable.length - 1] as HTMLElement;

        if (e.shiftKey) {
          if (document.activeElement === first) {
            e.preventDefault();
            last.focus();
          }
        } else {
          if (document.activeElement === last) {
            e.preventDefault();
            first.focus();
          }
        }
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    document.body.style.overflow = "hidden";

    const timer = setTimeout(() => {
      const firstFocusable = contentRef.current?.querySelector(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      (firstFocusable as HTMLElement | undefined)?.focus();
    }, 50);

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "";
      clearTimeout(timer);
      previousFocusRef.current?.focus();
    };
  }, [modal.isOpen, closeModal]);

  const handleOverlayClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (e.target === overlayRef.current && modal.closeOnOverlay !== false) {
        closeModal();
      }
    },
    [closeModal, modal.closeOnOverlay]
  );

  if (!modal.isOpen) return null;

  return createPortal(
    <div
      ref={overlayRef}
      onClick={handleOverlayClick}
      className="fixed inset-0 z-[90] flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm animate-in fade-in duration-200"
      role="dialog"
      aria-modal="true"
      aria-labelledby={modal.title ? "modal-title" : undefined}
      aria-describedby={modal.description ? "modal-desc" : undefined}
    >
      <div
        ref={contentRef}
        className={cn(
          "w-full max-w-lg rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-2xl",
          "animate-in zoom-in-95 fade-in duration-200"
        )}
      >
        {(modal.title || modal.description) && (
          <div className="border-b border-[var(--color-border)] p-6">
            {modal.title && (
              <h2 id="modal-title" className="text-lg font-semibold text-[var(--color-text-primary)]">
                {modal.title}
              </h2>
            )}
            {modal.description && (
              <p id="modal-desc" className="mt-1 text-sm text-[var(--color-text-secondary)]">
                {modal.description}
              </p>
            )}
          </div>
        )}
        <div className="p-6">
          {modal.content}
        </div>
        {(modal.primaryAction || modal.secondaryAction) && (
          <div className="flex items-center justify-end gap-3 border-t border-[var(--color-border)] p-6">
            {modal.secondaryAction && (
              <button
                type="button"
                onClick={() => {
                  modal.secondaryAction?.onClick();
                  closeModal();
                }}
                className="rounded-lg border border-[var(--color-border)] px-4 py-2 text-sm font-medium text-[var(--color-text-secondary)] transition-colors hover:bg-[var(--color-background)]"
              >
                {modal.secondaryAction.label}
              </button>
            )}
            {modal.primaryAction && (
              <button
                type="button"
                onClick={() => {
                  modal.primaryAction?.onClick();
                }}
                disabled={modal.primaryAction.loading}
                className="rounded-lg bg-[var(--color-primary)] px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-[var(--color-primary-hover)] disabled:opacity-50 disabled:pointer-events-none"
              >
                {modal.primaryAction.loading ? "Processing..." : modal.primaryAction.label}
              </button>
            )}
          </div>
        )}
      </div>
    </div>,
    document.body
  );
}
