"use client";

import { ThemeProvider } from "@/providers/ThemeProvider";
import { ToastContainer } from "@/components/ux/ToastContainer";
import { Modal } from "@/components/ux/Modal";
import { OnboardingProvider } from "@/components/ux/OnboardingProvider";
import { useKeyboardShortcuts } from "@/components/ux/useKeyboardShortcuts";

export function UXProviders({ children }: { children: React.ReactNode }) {
  useKeyboardShortcuts();

  return (
    <ThemeProvider>
      {children}
      <ToastContainer />
      <Modal />
      <OnboardingProvider />
    </ThemeProvider>
  );
}