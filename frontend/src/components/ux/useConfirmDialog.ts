"use client";

import { useUXStore } from "@/store/useUXStore";

export function useConfirmDialog() {
  const openModal = useUXStore((state) => state.openModal);
  const closeModal = useUXStore((state) => state.closeModal);

  const confirm = ({
    title = "Are you sure?",
    description,
    confirmLabel = "Confirm",
    cancelLabel = "Cancel",
    onConfirm,
  }: {
    title?: string;
    description?: string;
    confirmLabel?: string;
    cancelLabel?: string;
    onConfirm: () => void | Promise<void>;
  }): Promise<boolean> => {
    return new Promise((resolve) => {
      openModal({
        title,
        description,
        closeOnOverlay: false,
        primaryAction: {
          label: confirmLabel,
          onClick: async () => {
            closeModal();
            await onConfirm();
            resolve(true);
          },
        },
        secondaryAction: {
          label: cancelLabel,
          onClick: () => {
            closeModal();
            resolve(false);
          },
        },
      });
    });
  };

  return { confirm };
}