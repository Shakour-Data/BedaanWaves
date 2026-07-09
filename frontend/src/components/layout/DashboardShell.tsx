"use client";

import { useEffect } from "react";
import { useAppStore } from "@/store/useAppStore";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";
import { cn } from "@/lib/cn";

interface DashboardShellProps {
  title: string;
  children: React.ReactNode;
}

export function DashboardShell({ title, children }: DashboardShellProps) {
  const { theme, sidebarOpen, setSidebarOpen } = useAppStore();

  useEffect(() => {
    const root = document.documentElement;
    if (theme === "dark") root.classList.add("dark");
    else root.classList.remove("dark");
  }, [theme]);

  return (
    <div className="flex min-h-screen bg-background text-foreground">
      {/* سایدبار دسکتاپ */}
      <div className="hidden md:block">
        <Sidebar />
      </div>

      {/* سایدبار موبایل (overlay) */}
      {sidebarOpen ? (
        <div className="fixed inset-0 z-30 md:hidden">
          <button
            type="button"
            aria-label="بستن منو"
            className="absolute inset-0 bg-black/40"
            onClick={() => setSidebarOpen(false)}
          />
          <div className="absolute inset-y-0 right-0 animate-[fadeIn_300ms]">
            <Sidebar />
          </div>
        </div>
      ) : null}

      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar title={title} />
        <main className={cn("mx-auto w-full max-w-6xl flex-1 p-3")}>{children}</main>
      </div>
    </div>
  );
}
