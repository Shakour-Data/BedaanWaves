"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/useAuthStore";
import { NewSidebar } from "./NewSidebar";
import { NewTopbar } from "./NewTopbar";
import { Spinner } from "@/components/ui/Spinner";
import { cn } from "@/lib/cn";
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
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-4">
          <Spinner size="lg" />
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <p className="text-muted-foreground">Redirecting to login...</p>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-background">
      <NewSidebar />

      <div className="flex flex-1 flex-col lg:ml-64">
        <NewTopbar title={title} />

        <main className={cn(
          "flex-1 p-4 lg:p-6",
          "min-h-[calc(100vh-4rem)]"
        )}>
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