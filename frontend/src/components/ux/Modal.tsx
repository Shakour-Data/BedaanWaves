"use client";

import { Modal as UiModal } from "@/components/ui/Modal";
import { useUXStore } from "@/store/useUXStore";

export function Modal() {
  const { modal, closeModal } = useUXStore();

  if (!modal.isOpen) return null;

  return (
    <UiModal
      isOpen={modal.isOpen}
      onClose={closeModal}
      title={modal.title}
      description={modal.description}
      closeOnOverlay={modal.closeOnOverlay}
      footer={
        (modal.primaryAction || modal.secondaryAction) ? (
          <>
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
          </>
        ) : undefined
      }
    >
      {modal.content}
    </UiModal>
  );
}