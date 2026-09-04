"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/useAuthStore";
import { NewSidebar } from "./NewSidebar";
import { NewTopbar } from "./NewTopbar";
import { Breadcrumbs, type BreadcrumbItem } from "@/components/ux/Breadcrumbs";

interface NewDashboardShellProps {
  title: string;
  children: React.ReactNode;
  breadcrumbs?: BreadcrumbItem[];
}

export function NewDashboardShell({ title, children, breadcrumbs }: NewDashboardShellProps) {
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
          <div className="h-10 w-10 animate-spin rounded-full border-4 border-[var(--color-primary)] border-t-transparent" />
          <p className="text-sm text-[var(--color-text-muted)]">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[var(--color-background)]">
        <p className="text-sm text-[var(--color-text-muted)]">Redirecting to login...</p>
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--color-background)]">
      <NewSidebar />

      <div className="flex flex-1 flex-col min-w-0 lg:ml-64">
        <NewTopbar title={title} breadcrumbs={breadcrumbs} />

        <main className="flex-1 overflow-y-auto p-4 lg:p-6">
          <div className="w-full max-w-[90rem]">
            {breadcrumbs && breadcrumbs.length > 0 && (
              <Breadcrumbs items={breadcrumbs} />
            )}
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
