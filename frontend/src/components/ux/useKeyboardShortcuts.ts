"use client";

import { useUXStore } from "@/store/useUXStore";

export function useKeyboardShortcuts() {
  const addToast = useUXStore((state) => state.addToast);

  return {
    registerShortcuts: () => {
      const handleKeyDown = (e: KeyboardEvent) => {
        const isInputFocused =
          document.activeElement instanceof HTMLInputElement ||
          document.activeElement instanceof HTMLTextAreaElement ||
          document.activeElement instanceof HTMLSelectElement ||
          (document.activeElement as HTMLElement | null)?.isContentEditable;

        if ((e.metaKey || e.ctrlKey) && e.key === "k") {
          e.preventDefault();
          const searchInput = document.querySelector<HTMLInputElement>(
            'input[aria-autocomplete="list"], input[placeholder*="Search" i], input[placeholder*="search" i]'
          );
          if (searchInput) {
            searchInput.focus();
            searchInput.select();
          } else {
            addToast({
              type: "info",
              message: "Search bar not found on this page.",
            });
          }
        }

        if (e.key === "Escape" && !isInputFocused) {
          const modal = document.querySelector('[role="dialog"]');
          const dropdown = document.querySelector('[role="listbox"]');
          if (modal) {
            modal.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
          } else if (dropdown) {
            dropdown.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
          }
        }
      };

      document.addEventListener("keydown", handleKeyDown);
      return () => document.removeEventListener("keydown", handleKeyDown);
    },
  };
}
