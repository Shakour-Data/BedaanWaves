"use client";

import { useState, useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuthStore } from "@/store/useAuthStore";
import { useAppStore } from "@/store/useAppStore";
import { useUXStore } from "@/store/useUXStore";
import { useConfirmDialog } from "@/components/ux/useConfirmDialog";
import { Button } from "@/components/ui/Button";
import { Menu, Search, Bell, ChevronDown, X } from "lucide-react";

interface NewTopbarProps {
  title?: string;
  breadcrumbs?: { label: string; href?: string }[];
}

export function NewTopbar({ title = "Dashboard", breadcrumbs }: NewTopbarProps) {
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
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
      description: "You will need to sign in again to access your dashboard.",
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

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      router.push(`/stocks?search=${encodeURIComponent(searchQuery)}`);
      setShowSearch(false);
    }
  };

  useEffect(() => {
    if (showSearch) {
      const timer = setTimeout(() => setShowSearch(false), 30000);
      return () => clearTimeout(timer);
    }
  }, [showSearch]);

  return (
    <>
      <header className="z-30 h-16 shrink-0 border-b border-[var(--color-border)] bg-[var(--color-surface)]/80 backdrop-blur-xl">
        <div className="flex h-full items-center justify-between px-4 lg:px-6">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="lg:hidden h-9 w-9"
              aria-label="Toggle menu"
            >
              <Menu className="h-5 w-5" />
            </Button>

            <div className="hidden md:block">
              <h1 className="text-lg font-semibold text-[var(--color-text-primary)] tracking-tight">{title}</h1>
              {breadcrumbs && breadcrumbs.length > 0 && (
                <nav className="flex items-center gap-1.5 text-xs text-[var(--color-text-muted)]">
                  {breadcrumbs.map((crumb, i) => (
                    <span key={i} className="flex items-center gap-1.5">
                      {i > 0 && <span>/</span>}
                      {crumb.href ? (
                        <Link href={crumb.href} className="hover:text-[var(--color-primary)] transition-colors">{crumb.label}</Link>
                      ) : (
                        <span className="text-[var(--color-text-secondary)]">{crumb.label}</span>
                      )}
                    </span>
                  ))}
                </nav>
              )}
            </div>
          </div>

          <div className="hidden flex-1 max-w-xl px-8 lg:block" data-search-input>
            <form onSubmit={handleSearch} className="relative">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--color-text-muted)]" />
              <input
                type="text"
                placeholder="Search stocks, tickers..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-background)] pl-10 pr-4 py-2 text-sm text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] focus:border-[var(--color-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]/20 transition-all"
              />
            </form>
          </div>

          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowSearch(true)}
              className="md:hidden h-9 w-9"
              aria-label="Open search"
            >
              <Search className="h-4 w-4" />
            </Button>

            <div className="relative">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setShowNotifications(!showNotifications);
                  setShowUserMenu(false);
                }}
                className="relative h-9 w-9"
                aria-label="Notifications"
              >
                <Bell className="h-4 w-4" />
                <span className="absolute -right-0.5 -top-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-[var(--color-error)] text-[10px] font-medium text-white ring-2 ring-[var(--color-surface)]">
                  3
                </span>
              </Button>

              {showNotifications && (
                <>
                  <div className="fixed inset-0 z-40" onClick={() => setShowNotifications(false)} />
                  <div className="absolute right-0 top-full z-50 mt-2 w-80 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-lg">
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
                className="flex items-center gap-2 h-9 px-2"
                aria-label="User menu"
              >
                <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-accent)] text-xs font-semibold text-white">
                  {user?.full_name?.[0] || user?.username?.[0] || "U"}
                </div>
                <ChevronDown className="h-3 w-3 text-[var(--color-text-muted)] hidden sm:block" />
              </Button>

              {showUserMenu && (
                <>
                  <div className="fixed inset-0 z-40" onClick={() => setShowUserMenu(false)} />
                  <div className="absolute right-0 top-full z-50 mt-2 w-56 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-lg overflow-hidden">
                    <div className="border-b border-[var(--color-border)] p-4">
                      <p className="text-sm font-semibold text-[var(--color-text-primary)]">{user?.full_name || user?.username || "John Doe"}</p>
                      <p className="text-xs text-[var(--color-text-muted)] mt-0.5">{user?.email || "john@example.com"}</p>
                    </div>
                    <div className="p-2">
                      <Link href="/settings/profile" onClick={() => setShowUserMenu(false)} className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-[var(--color-text-secondary)] transition-colors hover:bg-[var(--color-muted)] hover:text-[var(--color-text-primary)]">Profile</Link>
                      <Link href="/settings" onClick={() => setShowUserMenu(false)} className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-[var(--color-text-secondary)] transition-colors hover:bg-[var(--color-muted)] hover:text-[var(--color-text-primary)]">Settings</Link>
                      <Link href="/help" onClick={() => setShowUserMenu(false)} className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-[var(--color-text-secondary)] transition-colors hover:bg-[var(--color-muted)] hover:text-[var(--color-text-primary)]">Help Center</Link>
                    </div>
                    <div className="border-t border-[var(--color-border)] p-2">
                      <button onClick={handleLogout} className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-[var(--color-error)] transition-colors hover:bg-[var(--color-error-light)]">Sign Out</button>
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
            <form onSubmit={handleSearch} className="flex flex-1 items-center gap-3">
              <Search className="h-4 w-4 text-[var(--color-text-muted)]" />
              <input
                type="text"
                placeholder="Search stocks..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="flex-1 bg-transparent text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] focus:outline-none"
                autoFocus
              />
            </form>
            <button onClick={() => setShowSearch(false)} className="text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)]" aria-label="Close search">
              <X className="h-5 w-5" />
            </button>
          </div>
          <div className="p-4">
            <p className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-3">Recent searches</p>
            <div className="flex flex-wrap gap-2">
              {["AAPL", "TSLA", "NVDA", "MSFT"].map((ticker) => (
                <button key={ticker} onClick={() => { router.push(`/stocks/${ticker}`); setShowSearch(false); }} className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-1.5 text-sm text-[var(--color-text-secondary)] hover:border-[var(--color-primary)] hover:text-[var(--color-text-primary)] transition-colors">{ticker}</button>
              ))}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
