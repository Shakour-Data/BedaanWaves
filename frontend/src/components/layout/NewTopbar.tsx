"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuthStore } from "@/store/useAuthStore";
import { useAppStore } from "@/store/useAppStore";

interface NewTopbarProps {
  title?: string;
}

// Mock notifications
const notifications = [
  {
    id: 1,
    type: "gain",
    title: "AAPL up 2.5%",
    message: "Apple Inc. gained in pre-market trading",
    time: "2m ago",
    color: "#10b981"
  },
  {
    id: 2,
    type: "alert",
    title: "Market opens in 30 min",
    message: "NASDAQ pre-market session active",
    time: "28m ago",
    color: "#f59e0b"
  },
  {
    id: 3,
    type: "loss",
    title: "TSLA down 1.2%",
    message: "Tesla Inc. declined pre-market",
    time: "1h ago",
    color: "#ef4444"
  }
];

export function NewTopbar({ title = "Dashboard" }: NewTopbarProps) {
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [showSearch, setShowSearch] = useState(false);
  
  const sidebarOpen = useAppStore((state) => state.sidebarOpen);
  const setSidebarOpen = useAppStore((state) => state.setSidebarOpen);
  const { user, logout } = useAuthStore();
  const router = useRouter();

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      router.push(`/stocks?search=${encodeURIComponent(searchQuery)}`);
      setShowSearch(false);
    }
  };

  return (
    <>
      <header className="fixed top-0 left-0 right-0 z-40 h-16 border-b border-[var(--color-border)] bg-[var(--color-background)]/95 backdrop-blur-xl">
        <div className="flex h-full items-center justify-between px-4 lg:px-6">
          {/* Left Section */}
          <div className="flex items-center gap-4">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="flex h-10 w-10 items-center justify-center rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text-secondary)] transition-colors hover:border-[var(--color-border)] hover:text-[var(--color-text-primary)] lg:hidden"
            >
              <span className="text-lg">Menu</span>
            </button>
            
            <div className="hidden md:block">
              <h1 className="text-lg font-semibold text-[var(--color-text-primary)]">{title}</h1>
              <p className="text-xs text-[var(--color-text-secondary)]">NASDAQ Market Analysis</p>
            </div>
          </div>

          {/* Center Section - Search */}
          <div className="hidden flex-1 max-w-xl px-8 lg:block">
            <form onSubmit={handleSearch} className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-text-secondary)] text-xs">Search</span>
              <input
                type="text"
                placeholder="Search stocks, tickers..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="h-10 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] pl-16 pr-4 text-sm text-[var(--color-text-primary)] placeholder-[#64748b] transition-colors focus:border-[var(--color-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--color-primary)]"
              />
              <kbd className="absolute right-3 top-1/2 hidden -translate-y-1/2 rounded border border-[var(--color-border)] bg-[var(--color-border)] px-1.5 py-0.5 text-[10px] text-[var(--color-text-secondary)] md:inline-block">
                ⌘K
              </kbd>
            </form>
          </div>

          {/* Right Section */}
          <div className="flex items-center gap-2">
            {/* Search Button (Mobile) */}
            <button 
              onClick={() => setShowSearch(true)}
              className="flex h-10 w-10 items-center justify-center rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text-secondary)] transition-colors hover:border-[var(--color-border)] hover:text-[var(--color-text-primary)] md:hidden"
            >
              <span className="text-lg">Search</span>
            </button>

            {/* Notifications */}
            <div className="relative">
              <button
                onClick={() => {
                  setShowNotifications(!showNotifications);
                  setShowUserMenu(false);
                }}
                className="relative flex h-10 w-10 items-center justify-center rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text-secondary)] transition-colors hover:border-[var(--color-border)] hover:text-[var(--color-text-primary)]"
              >
                <span className="text-sm">Alerts</span>
                <span className="absolute -right-0.5 -top-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-[var(--color-error)] text-[10px] font-medium text-white ring-2 ring-[var(--color-surface)]">
                  3
                </span>
              </button>

              {/* Notifications Dropdown */}
              {showNotifications && (
                <>
                  <div 
                    className="fixed inset-0 z-40" 
                    onClick={() => setShowNotifications(false)} 
                  />
                  <div className="absolute right-0 top-full z-50 mt-2 w-80 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-2xl">
                    <div className="flex items-center justify-between border-b border-[var(--color-border)] px-4 py-3">
                      <h3 className="text-sm font-semibold text-[var(--color-text-primary)]">Notifications</h3>
                      <button className="text-xs text-[var(--color-primary)] hover:underline">
                        Mark all read
                      </button>
                    </div>
                    <div className="max-h-64 overflow-y-auto">
                      {notifications.map((notif) => (
                        <div 
                          key={notif.id} 
                          className="flex items-start gap-3 border-b border-[var(--color-border)] p-4 hover:bg-[var(--color-border)]/50 cursor-pointer"
                        >
                          <div 
                            className="flex h-8 w-8 items-center justify-center rounded-full"
                            style={{ backgroundColor: `${notif.color}20` }}
                          >
                            <span style={{ color: notif.color }}>●</span>
                          </div>
                          <div className="flex-1">
                            <p className="text-sm text-[var(--color-text-primary)]">{notif.title}</p>
                            <p className="text-xs text-[var(--color-text-secondary)]">{notif.message}</p>
                          </div>
                          <span className="text-xs text-[var(--color-text-secondary)] whitespace-nowrap">{notif.time}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              )}
            </div>

            {/* User Menu */}
            <div className="relative">
              <button
                onClick={() => {
                  setShowUserMenu(!showUserMenu);
                  setShowNotifications(false);
                }}
                className="flex items-center gap-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-1.5 transition-colors hover:border-[var(--color-primary)]"
              >
                <div className="flex h-7 w-7 items-center justify-center rounded-md bg-[var(--color-primary)]/10 text-sm font-semibold text-[var(--color-primary)]">
                  {user?.full_name?.[0] || user?.username?.[0] || "U"}
                </div>
                <div className="hidden flex-col items-start px-1 md:flex">
                  <span className="text-xs font-medium text-[var(--color-text-primary)] leading-tight">{user?.full_name || user?.username || "User"}</span>
                </div>
              </button>

              {/* User Dropdown */}
              {showUserMenu && (
                <>
                  <div 
                    className="fixed inset-0 z-40" 
                    onClick={() => setShowUserMenu(false)} 
                  />
                  <div className="absolute right-0 top-full z-50 mt-2 w-56 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-2xl">
                    <div className="border-b border-[var(--color-border)] p-4">
                      <p className="text-sm font-semibold text-[var(--color-text-primary)]">{user?.full_name || user?.username || "John Doe"}</p>
                      <p className="text-xs text-[var(--color-text-secondary)]">{user?.email || "john@example.com"}</p>
                    </div>
                    <div className="p-2">
                      <Link
                        href="/settings/profile"
                        onClick={() => setShowUserMenu(false)}
                        className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-[var(--color-text-secondary)] transition-colors hover:bg-[var(--color-border)] hover:text-[var(--color-text-primary)]"
                      >
                        Profile
                      </Link>
                      <Link
                        href="/settings"
                        onClick={() => setShowUserMenu(false)}
                        className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-[var(--color-text-secondary)] transition-colors hover:bg-[var(--color-border)] hover:text-[var(--color-text-primary)]"
                      >
                        Settings
                      </Link>
                      <Link
                        href="/help"
                        onClick={() => setShowUserMenu(false)}
                        className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-[var(--color-text-secondary)] transition-colors hover:bg-[var(--color-border)] hover:text-[var(--color-text-primary)]"
                      >
                        Help Center
                      </Link>
                    </div>
                    <div className="border-t border-[var(--color-border)] p-2">
                      <button
                        onClick={handleLogout}
                        className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-[var(--color-error)] transition-colors hover:bg-[var(--color-error)]/10"
                      >
                        Sign Out
                      </button>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Mobile Search Overlay */}
      {showSearch && (
        <div className="fixed inset-0 z-50 bg-[var(--color-background)]/95 backdrop-blur-xl md:hidden">
          <div className="flex h-16 items-center justify-between border-b border-[var(--color-border)] px-4">
            <form onSubmit={handleSearch} className="flex flex-1 items-center gap-3">
              <span className="text-[var(--color-text-secondary)] text-xs">Search</span>
              <input
                type="text"
                placeholder="Search stocks..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="flex-1 bg-transparent text-[var(--color-text-primary)] placeholder-[#64748b] focus:outline-none"
                autoFocus
              />
            </form>
            <button 
              onClick={() => setShowSearch(false)}
              className="text-[var(--color-text-secondary)]"
            >
              Cancel
            </button>
          </div>
          <div className="p-4">
            <p className="text-sm text-[var(--color-text-secondary)]">Recent searches</p>
            <div className="mt-2 flex flex-wrap gap-2">
              {["AAPL", "TSLA", "NVDA", "MSFT"].map((ticker) => (
                <button
                  key={ticker}
                  onClick={() => {
                    router.push(`/stocks/${ticker}`);
                    setShowSearch(false);
                  }}
                  className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-1.5 text-sm text-[var(--color-text-secondary)] hover:border-[var(--color-border)] hover:text-[var(--color-text-primary)]"
                >
                  {ticker}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
