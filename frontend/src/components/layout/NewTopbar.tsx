"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuthStore } from "@/store/useAuthStore";
import { useAppStore } from "@/store/useAppStore";
import { useUXStore } from "@/store/useUXStore";
import { useConfirmDialog } from "@/components/ux/useConfirmDialog";
import { Button } from "@/components/ui/Button";
import { UnifiedSearchBar } from "@/components/search/UnifiedSearchBar";

interface NewTopbarProps {
  title?: string;
  breadcrumbs?: { label: string; href?: string }[];
}

export function NewTopbar({ title = "Dashboard", breadcrumbs }: NewTopbarProps) {
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [showSearch, setShowSearch] = useState(false);

  const sidebarOpen = useAppStore((state) => state.sidebarOpen);
  const setSidebarOpen = useAppStore((state) => state.setSidebarOpen);
  const { user, logout } = useAuthStore();
  const router = useRouter();
  const { confirm } = useConfirmDialog();
  const addToast = useUXStore((state) => state.addToast);

  const handleLogout = useCallback(async () => {
    const confirmed = await confirm({
      title: "Sign out?",
      description: "You will need to sign in again to access your analytics.",
      confirmLabel: "Sign out",
      onConfirm: () => {
        addToast({ type: "info", message: "You have been signed out." });
      },
    });
    if (confirmed) {
      logout();
      router.push("/login");
    }
  }, [confirm, logout, router, addToast]);

  return (
    <>
      <header className="z-30 h-16 shrink-0 border-b border-[var(--color-border)] bg-[var(--color-surface)]/80 backdrop-blur-xl">
        <div className="flex h-full items-center justify-between gap-3 px-4 lg:px-6">
          <div className="flex items-center gap-3 min-w-0">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="lg:hidden"
              aria-label="Toggle menu"
            >
              <span className="text-lg font-mono">&#9776;</span>
            </Button>

            <div className="hidden md:block min-w-0">
              <h1 className="text-lg font-semibold text-[var(--color-text-primary)] tracking-tight truncate">{title}</h1>
              {breadcrumbs && breadcrumbs.length > 0 && (
                <nav aria-label="Breadcrumb" className="hidden lg:flex items-center gap-1.5 text-xs text-[var(--color-text-muted)]">
                  {breadcrumbs.map((crumb, i) => (
                    <span key={i} className="flex items-center gap-1.5">
                      {i > 0 && <span>/</span>}
                      {crumb.href ? (
                        <Link href={crumb.href} className="hover:text-[var(--color-primary)] transition-colors">{crumb.label}</Link>
                      ) : (
                        <span className="text-[var(--color-text-secondary)] truncate max-w-[200px]">{crumb.label}</span>
                      )}
                    </span>
                  ))}
                </nav>
              )}
            </div>
          </div>

          <div className="hidden md:flex flex-1 max-w-xl px-4 lg:px-8" data-search-input>
            <UnifiedSearchBar
              variant="topbar"
              placeholder="Search stocks, tickers, news&hellip;"
              className="w-full"
            />
          </div>

          <div className="flex items-center gap-1">
             <Button
               variant="ghost"
               size="sm"
               onClick={() => setShowSearch(true)}
               className="md:hidden"
               aria-label="Open search"
             >
              <span className="text-xs font-bold">S</span>
            </Button>

            <div className="relative">
             <Button
               variant="ghost"
               size="sm"
               onClick={() => {
                 setShowNotifications(!showNotifications);
                 setShowUserMenu(false);
               }}
               className="relative px-3"
               aria-label="Notifications"
               aria-expanded={showNotifications}
             >
                <span className="text-xs font-semibold">Notif</span>
                <span className="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center rounded-full bg-[var(--color-error)] text-[10px] font-medium text-white ring-2 ring-[var(--color-surface)]">
                  3
                </span>
              </Button>

              {showNotifications && (
                <>
                  <div className="fixed inset-0 z-40" onClick={() => setShowNotifications(false)} aria-hidden="true" />
                  <div
                    role="dialog"
                    aria-label="Notifications"
                    className="absolute right-0 top-full z-50 mt-2 w-80 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-lg"
                  >
                    <div className="flex items-center justify-between border-b border-[var(--color-border)] px-4 py-3">
                      <h3 className="text-sm font-semibold text-[var(--color-text-primary)]">Notifications</h3>
                      <button className="text-xs text-[var(--color-primary)] hover:underline">Mark all read</button>
                    </div>
                    <div className="max-h-64 overflow-y-auto">
                      <div className="flex flex-col items-center justify-center py-8 text-[var(--color-text-muted)]">
                        <p className="text-sm">No new notifications</p>
                      </div>
                    </div>
                  </div>
                </>
              )}
            </div>

            <div className="relative">
             <Button
               variant="ghost"
               onClick={() => {
                 setShowUserMenu(!showUserMenu);
                 setShowNotifications(false);
               }}
               className="flex items-center gap-2 px-3"
               aria-label="User menu"
               aria-expanded={showUserMenu}
             >
                <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-accent)] text-xs font-semibold text-white">
                  {user?.full_name?.[0] || user?.username?.[0] || "U"}
                </div>
                <span className="h-3 w-3 text-[var(--color-text-muted)] hidden sm:block text-xs font-mono">
                  {showUserMenu ? "&#9652;" : "&#9662;"}
                </span>
              </Button>

              {showUserMenu && (
                <>
                  <div className="fixed inset-0 z-40" onClick={() => setShowUserMenu(false)} aria-hidden="true" />
                  <div
                    role="menu"
                    aria-label="User menu"
                    className="absolute right-0 top-full z-50 mt-2 w-56 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-lg overflow-hidden"
                  >
                    <div className="border-b border-[var(--color-border)] p-4">
                      <p className="text-sm font-semibold text-[var(--color-text-primary)]">{user?.full_name || user?.username || "John Doe"}</p>
                      <p className="text-xs text-[var(--color-text-muted)] mt-0.5">{user?.email || "john@example.com"}</p>
                    </div>
                    <div className="p-2">
                      <Link href="/settings/profile" onClick={() => setShowUserMenu(false)} role="menuitem" className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-[var(--color-text-secondary)] transition-colors hover:bg-[var(--color-muted)] hover:text-[var(--color-text-primary)]">Profile</Link>
                      <Link href="/settings" onClick={() => setShowUserMenu(false)} role="menuitem" className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-[var(--color-text-secondary)] transition-colors hover:bg-[var(--color-muted)] hover:text-[var(--color-text-primary)]">Settings</Link>
                      <Link href="/help" onClick={() => setShowUserMenu(false)} role="menuitem" className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-[var(--color-text-secondary)] transition-colors hover:bg-[var(--color-muted)] hover:text-[var(--color-text-primary)]">Help Center</Link>
                    </div>
                    <div className="border-t border-[var(--color-border)] p-2">
                      <button onClick={handleLogout} role="menuitem" className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-[var(--color-error)] transition-colors hover:bg-[var(--color-error-light)]">Sign Out</button>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      {showSearch && (
        <div className="fixed inset-0 z-50 bg-[var(--color-background)]/95 backdrop-blur-xl md:hidden">
          <div className="flex h-16 items-center justify-between border-b border-[var(--color-border)] px-4">
            <div className="flex flex-1 items-center gap-3">
              <UnifiedSearchBar
                variant="topbar"
                placeholder="Search stocks&hellip;"
                autoFocus
                className="flex-1"
              />
            </div>
            <button onClick={() => setShowSearch(false)} className="text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] text-lg font-mono" aria-label="Close search">
              &times;
            </button>
          </div>
        </div>
      )}
    </>
  );
}
