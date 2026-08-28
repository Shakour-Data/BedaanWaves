"use client";

import { type ReactNode, useEffect } from "react";
import { usePathname } from "next/navigation";
import { useAppStore } from "@/store/useAppStore";
import { cn } from "@/lib/cn";

interface PageWrapperProps {
  children: ReactNode;
  sidebar?: ReactNode;
  header?: ReactNode;
  className?: string;
}

export function PageWrapper({
  children,
  sidebar,
  header,
  className,
}: PageWrapperProps) {
  const pathname = usePathname();
  const sidebarOpen = useAppStore((s) => s.sidebarOpen);
  const setSidebarOpen = useAppStore((s) => s.setSidebarOpen);

  useEffect(() => {
    setSidebarOpen(false);
  }, [pathname, setSidebarOpen]);

  return (
    <div className="flex min-h-screen bg-[var(--color-background)]">
      {sidebar && (
        <aside
          className={cn(
            "sidebar-transition fixed left-0 top-0 z-40 h-screen bg-[var(--color-background)] border-r border-[var(--color-border)]",
            sidebarOpen ? "w-64 translate-x-0" : "w-64 -translate-x-full lg:w-16 lg:translate-x-0"
          )}
        >
          {sidebar}
        </aside>
      )}

      <div
        className={cn(
          "flex flex-1 flex-col transition-all duration-300",
          sidebarOpen ? "lg:ml-64" : "lg:ml-16"
        )}
      >
        {header && <div className="sticky top-0 z-30">{header}</div>}
        <main className={cn("flex-1 p-4 lg:p-6", className)}>
          <div className="container-grid">{children}</div>
        </main>
      </div>

      {/* Mobile sidebar overlay */}
      {sidebar && sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  );
}
