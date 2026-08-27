"use client";

import type { ReactNode } from "react";
import { useAuthStore } from "@/store/useAuthStore";

interface AuthGateProps {
  authenticatedContent: ReactNode;
  unauthenticatedNav: ReactNode;
}

export function AuthGate({ authenticatedContent, unauthenticatedNav }: AuthGateProps) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  if (isAuthenticated) {
    return <>{authenticatedContent}</>;
  }

  return (
    <>
      {unauthenticatedNav}
      {authenticatedContent}
    </>
  );
}
