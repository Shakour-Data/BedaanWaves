"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/useAuthStore";
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
  const { isAuthenticated, logout } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    const root = document.documentElement;
    if (theme === "dark") root.classList.add("dark");
    else root.classList.remove("dark");
  }, [theme]);

  useEffect(() => {
    if (sidebarOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [sidebarOpen]);

  useEffect(() => {
    if (!isAuthenticated) {
      router.replace('/login');
    }
  }, [isAuthenticated, router]);

  if (!isAuthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-muted-foreground">در حال انتقال به صفحه ورود...</p>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-background text-foreground">
      {/* سایدبار دسکتاپ */}
      <div className="hidden md:block">
        <Sidebar />
      </div>

      {/* سایدبار موبایل (overlay) */}
      {sidebarOpen ? (
        <div className="fixed inset-0 z-30 md:hidden animate-in fade-in duration-300">
          <button
            type="button"
            aria-label="بستن منو"
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={() => setSidebarOpen(false)}
          />
          <div className="absolute inset-y-0 right-0 w-64 animate-in slide-in-from-right duration-300 ease-flow">
            <Sidebar />
          </div>
        </div>
      ) : null}

      <div className="flex min-w-0 flex-1 flex-col min-h-screen">
        <Topbar title={title} />
        <main className={cn("mx-auto w-full max-w-6xl flex-1 p-3 min-h-0")}>{children}</main>
      </div>
    </div>
  );
}