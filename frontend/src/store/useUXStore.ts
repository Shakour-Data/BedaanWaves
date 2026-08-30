import { create } from "zustand";

export type ToastType = "success" | "error" | "warning" | "info";

export interface Toast {
  id: string;
  type: ToastType;
  title?: string;
  message: string;
  duration?: number;
  action?: { label: string; onClick: () => void };
}

export interface ModalState {
  isOpen: boolean;
  title?: string;
  description?: string;
  content?: React.ReactNode;
  primaryAction?: { label: string; onClick: () => void; loading?: boolean };
  secondaryAction?: { label: string; onClick: () => void };
  closeOnOverlay?: boolean;
}

export interface UXState {
  toasts: Toast[];
  modal: ModalState;
  globalLoading: boolean;
  globalLoadingMessage?: string;
  addToast: (toast: Omit<Toast, "id">) => void;
  removeToast: (id: string) => void;
  openModal: (modal: Omit<ModalState, "isOpen">) => void;
  closeModal: () => void;
  setGlobalLoading: (loading: boolean, message?: string) => void;
}

let toastId = 0;

export const useUXStore = create<UXState>((set) => ({
  toasts: [],
  modal: { isOpen: false, closeOnOverlay: true },
  globalLoading: false,
  globalLoadingMessage: undefined,

  addToast: (toast) => {
    const id = `toast-${++toastId}-${Date.now()}`;
    set((state) => ({
      toasts: [...state.toasts, { ...toast, id }],
    }));
    if (toast.duration !== 0) {
      setTimeout(() => {
        set((state) => ({
          toasts: state.toasts.filter((t) => t.id !== id),
        }));
      }, toast.duration ?? 4000);
    }
  },

  removeToast: (id) =>
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id),
    })),

  openModal: (modal) =>
    set({ modal: { ...modal, isOpen: true } }),

  closeModal: () =>
    set((state) => ({
      modal: { ...state.modal, isOpen: false },
    })),

  setGlobalLoading: (loading, message) =>
    set({ globalLoading: loading, globalLoadingMessage: message }),
}));
