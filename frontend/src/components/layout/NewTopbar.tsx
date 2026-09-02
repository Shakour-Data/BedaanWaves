"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuthStore } from "@/store/useAuthStore";
import { useAppStore } from "@/store/useAppStore";
import { useUXStore } from "@/store/useUXStore";
import { useConfirmDialog } from "@/components/ux/useConfirmDialog";
import { Button } from "@/components/ui/Button";
import { StockSearchBar } from "@/components/search/StockSearchBar";

interface NewTopbarProps {
  title?: string;
}

export function NewTopbar({ title = "Dashboard" }: NewTopbarProps) {
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

  return (
    <>
      <header className="z-30 h-16 shrink-0 border-b border-border bg-background/95 backdrop-blur-xl">
        <div className="flex h-full items-center justify-between px-4 lg:px-6">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="lg:hidden"
              aria-label="Toggle menu"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="3" y1="12" x2="21" y2="12" />
                <line x1="3" y1="6" x2="21" y2="6" />
                <line x1="3" y1="18" x2="21" y2="18" />
              </svg>
            </Button>

            <div className="hidden md:block">
              <h1 className="text-lg font-semibold text-foreground">{title}</h1>
              <p className="text-xs text-muted-foreground">NASDAQ Market Analysis</p>
            </div>
          </div>

          <div className="hidden flex-1 max-w-xl px-8 lg:block" data-search-input>
            <StockSearchBar
              placeholder="Search stocks, tickers..."
              onSelect={(stock) => router.push(`/stocks/${stock.symbol}`)}
            />
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowSearch(true)}
              className="md:hidden"
              aria-label="Open search"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="11" cy="11" r="8" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
            </Button>

            <div className="relative">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setShowNotifications(!showNotifications);
                  setShowUserMenu(false);
                }}
                className="relative"
                aria-label="Notifications"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" />
                  <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" />
                </svg>
                <span className="absolute -right-0.5 -top-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-error text-[10px] font-medium text-white ring-2 ring-background">
                  3
                </span>
              </Button>

              {showNotifications && (
                <>
                  <div className="fixed inset-0 z-40" onClick={() => setShowNotifications(false)} />
                  <div className="absolute right-0 top-full z-50 mt-2 w-80 rounded-xl border border-border bg-surface shadow-lg">
                    <div className="flex items-center justify-between border-b border-border px-4 py-3">
                      <h3 className="text-sm font-semibold text-foreground">Notifications</h3>
                      <button className="text-xs text-primary hover:underline">Mark all read</button>
                    </div>
                    <div className="max-h-64 overflow-y-auto">
                      <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
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
              className="flex items-center gap-2"
              aria-label="User menu"
            >
                <div className="flex h-7 w-7 items-center justify-center rounded-md bg-primary/10 text-sm font-semibold text-primary">
                  {user?.full_name?.[0] || user?.username?.[0] || "U"}
                </div>
                <div className="hidden flex-col items-start px-1 md:flex">
                  <span className="text-xs font-medium text-foreground leading-tight">{user?.full_name || user?.username || "User"}</span>
                </div>
              </Button>

              {showUserMenu && (
                <>
                  <div className="fixed inset-0 z-40" onClick={() => setShowUserMenu(false)} />
                  <div className="absolute right-0 top-full z-50 mt-2 w-56 rounded-xl border border-border bg-surface shadow-lg">
                    <div className="border-b border-border p-4">
                      <p className="text-sm font-semibold text-foreground">{user?.full_name || user?.username || "John Doe"}</p>
                      <p className="text-xs text-muted-foreground">{user?.email || "john@example.com"}</p>
                    </div>
                    <div className="p-2">
                      <Link href="/settings/profile" onClick={() => setShowUserMenu(false)} className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-border hover:text-foreground">Profile</Link>
                      <Link href="/settings" onClick={() => setShowUserMenu(false)} className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-border hover:text-foreground">Settings</Link>
                      <Link href="/help" onClick={() => setShowUserMenu(false)} className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-border hover:text-foreground">Help Center</Link>
                    </div>
                    <div className="border-t border-border p-2">
                      <button onClick={handleLogout} className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-error transition-colors hover:bg-error/10">Sign Out</button>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      {showSearch && (
        <div className="fixed inset-0 z-50 bg-background/95 backdrop-blur-xl md:hidden">
          <div className="flex h-16 items-center justify-between border-b border-border px-4">
            <form onSubmit={handleSearch} className="flex flex-1 items-center gap-3">
              <span className="text-muted-foreground text-xs">Search</span>
              <input
                type="text"
                placeholder="Search stocks..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="flex-1 bg-transparent text-foreground placeholder:text-muted-foreground focus:outline-none"
                autoFocus
              />
            </form>
            <button onClick={() => setShowSearch(false)} className="text-muted-foreground" aria-label="Close search">Cancel</button>
          </div>
          <div className="p-4">
            <p className="text-sm text-muted-foreground">Recent searches</p>
            <div className="mt-2 flex flex-wrap gap-2">
              {["AAPL", "TSLA", "NVDA", "MSFT"].map((ticker) => (
                <button key={ticker} onClick={() => { router.push(`/stocks/${ticker}`); setShowSearch(false); }} className="rounded-lg border border-border bg-surface px-3 py-1.5 text-sm text-muted-foreground hover:border-primary hover:text-foreground transition-colors">{ticker}</button>
              ))}
            </div>
          </div>
        </div>
      )}
    </>
  );
}