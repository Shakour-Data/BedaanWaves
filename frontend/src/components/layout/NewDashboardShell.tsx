"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/useAuthStore";
import { NewSidebar } from "./NewSidebar";
import { NewTopbar } from "./NewTopbar";
import { cn } from "@/lib/cn";

interface NewDashboardShellProps {
  title: string;
  children: React.ReactNode;
}

export function NewDashboardShell({ title, children }: NewDashboardShellProps) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const isLoading = useAuthStore((state) => state.loading);
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [isAuthenticated, isLoading, router]);

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[var(--color-background)]">
        <div className="flex flex-col items-center gap-4">
          <div className="h-12 w-12 animate-spin rounded-full border-4 border-[var(--color-border)] border-t-[#00d4ff]" />
          <p className="text-[var(--color-text-secondary)]">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[var(--color-background)]">
        <p className="text-[var(--color-text-secondary)]">Redirecting to login...</p>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-[var(--color-background)]">
      {/* Sidebar */}
      <NewSidebar />

      {/* Main Content */}
      <div className="flex flex-1 flex-col lg:ml-64">
        <NewTopbar title={title} />
        
        <main className={cn(
          "flex-1 p-4 lg:p-6",
          "min-h-[calc(100vh-4rem)]"
        )}>
          <div className="container-grid">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
