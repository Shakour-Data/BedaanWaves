"use client";

import { useState, useEffect, useMemo, useCallback } from "react";
import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { useAppStore } from "@/store/useAppStore";
import { cn } from "@/lib/cn";

interface NavItem {
  label: string;
  href: string;
  marker: string;
}

interface NavCategory {
  label: string;
  items: NavItem[];
}

const isCategoryActive = (items: NavItem[], checkActive: (href: string) => boolean) =>
  items.some((item) => checkActive(item.href));

const categories: NavCategory[] = [
  {
    label: "Dashboard",
    items: [
      { label: "General", href: "/dashboard?tab=general", marker: "D" },
      { label: "Technical", href: "/dashboard?tab=technical", marker: "T" },
      { label: "Fundamental", href: "/dashboard?tab=fundamental", marker: "F" },
      { label: "News Feed", href: "/dashboard?tab=news", marker: "N" },
      { label: "Risk Metrics", href: "/dashboard?tab=risk", marker: "R" },
      { label: "Board & Governance", href: "/dashboard?tab=board", marker: "B" },
      { label: "AI Insights", href: "/dashboard?tab=ai", marker: "AI" },
    ],
  },
  {
    label: "Markets",
    items: [
      { label: "Stocks", href: "/stocks", marker: "S" },
      { label: "Analysis", href: "/analysis", marker: "A" },
      { label: "Scoring", href: "/scoring", marker: "SC" },
      { label: "Portfolio", href: "/portfolio", marker: "P" },
      { label: "Rankings", href: "/ranking", marker: "RN" },
    ],
  },
  {
    label: "Intelligence",
    items: [
      { label: "News", href: "/news", marker: "NW" },
      { label: "Alerts", href: "/alerts", marker: "AL" },
      { label: "Search", href: "/search-demo", marker: "SR" },
    ],
  },
  {
    label: "Resources",
    items: [
      { label: "Methodology", href: "/methodology", marker: "M" },
      { label: "Help", href: "/help", marker: "H" },
    ],
  },
];

const bottomItems: NavItem[] = [
  { label: "Settings", href: "/settings", marker: "ST" },
  { label: "Profile", href: "/settings/profile", marker: "PR" },
];

export function NewSidebar() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const currentTab = searchParams.get("tab") || "general";
  const currentSub = searchParams.get("sub");
  const sidebarOpen = useAppStore((state) => state.sidebarOpen);
  const setSidebarOpen = useAppStore((state) => state.setSidebarOpen);

  const [userExpanded, setUserExpanded] = useState<Set<string>>(new Set(["Dashboard", "Markets"]));

  const isActive = useCallback((href: string) => {
    if (href.startsWith("/dashboard?") && !href.includes("sub=")) {
      const url = new URL(href, "http://x");
      const tab = url.searchParams.get("tab") || "general";
      return pathname === "/dashboard" && currentTab === tab;
    }
    if (href === "/dashboard") {
      return pathname === href && currentTab === "general";
    }
    if (href.startsWith("/dashboard?") && href.includes("sub=")) {
      const url = new URL(href, "http://x");
      const tab = url.searchParams.get("tab") || "general";
      const sub = url.searchParams.get("sub");
      return pathname === "/dashboard" && currentTab === tab && currentSub === sub;
    }
    return pathname.startsWith(href);
  }, [pathname, currentTab, currentSub]);

  const autoExpanded = useMemo(() => {
    const auto = new Set<string>();
    categories.forEach((cat) => {
      if (isCategoryActive(cat.items, isActive)) {
        auto.add(cat.label);
      }
    });
    return auto;
  }, [isActive]);

  const expandedCategories = new Set([...autoExpanded, ...userExpanded]);

  useEffect(() => {
    if (sidebarOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [sidebarOpen]);

  const toggleCategory = (label: string) => {
    setUserExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(label)) {
        next.delete(label);
      } else {
        next.add(label);
      }
      return next;
    });
  };

  return (
    <>
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 w-64 bg-[var(--color-surface)] border-r border-[var(--color-border)] transition-transform duration-300 ease-in-out",
          "lg:translate-x-0",
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex h-screen flex-col">
          <div className="flex h-16 items-center border-b border-[var(--color-border)] px-5 shrink-0">
            <Link href="/dashboard" className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-accent)] text-white shadow-md">
                <span className="font-bold text-lg">B</span>
              </div>
              <div className="flex flex-col">
                <span className="text-base font-bold text-[var(--color-text-primary)] leading-tight tracking-tight">BedaanWaves</span>
                <span className="text-[10px] font-medium text-[var(--color-text-muted)] uppercase tracking-wider leading-tight">Analytics</span>
              </div>
            </Link>
          </div>

          <div className="flex-1 overflow-y-auto py-4">
            <nav className="flex flex-col gap-1 px-3">
              {categories.map((cat) => {
                const isExpanded = expandedCategories.has(cat.label);
                const hasActive = isCategoryActive(cat.items, isActive);

                return (
                  <div key={cat.label} className="mb-1">
                    <button
                      onClick={() => toggleCategory(cat.label)}
                      className={cn(
                        "flex w-full items-center gap-3 rounded-lg px-3 py-2 text-xs font-semibold uppercase tracking-wider transition-colors",
                        hasActive ? "text-[var(--color-primary)]" : "text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-muted)]"
                      )}
                    >
                      <span
                        className={cn(
                          "h-1.5 w-1.5 rounded-full transition-colors",
                          hasActive ? "bg-[var(--color-primary)]" : "bg-[var(--color-border)]"
                        )}
                      />
                      <span className="flex-1 text-left">{cat.label}</span>
                      <span
                        className={cn(
                          "text-xs text-[var(--color-text-muted)] transition-transform duration-200 font-mono",
                          isExpanded && "rotate-180"
                        )}
                      >
                        {isExpanded ? "\u25B2" : "\u25BC"}
                      </span>
                    </button>

                    {isExpanded && (
                      <div className="ml-2 mt-1 flex flex-col gap-0.5 border-l border-[var(--color-border)] pl-3">
                        {cat.items.map((item) => {
                          const active = isActive(item.href);
                          return (
                             <Link
                               key={item.href}
                               href={item.href}
                               onClick={() => setSidebarOpen(false)}
                               className={cn(
                                 "group flex items-center gap-3 rounded-r-lg px-3 py-2 text-sm font-medium transition-all duration-200 border-l-2 border-l-transparent",
                                 active
                                   ? "bg-[var(--color-primary-soft)] text-[var(--color-primary)] border-l-[var(--color-primary)]"
                                   : "text-[var(--color-text-muted)] hover:bg-[var(--color-muted)] hover:text-[var(--color-text-primary)] hover:border-l-[var(--color-border)]"
                               )}
                             >
                              <span
                                className={cn(
                                  "flex h-5 w-5 items-center justify-center rounded transition-colors text-[10px] font-bold",
                                  active ? "text-[var(--color-primary)]" : "text-[var(--color-text-muted)] group-hover:text-[var(--color-text-primary)]"
                                )}
                              >
                                {item.marker}
                              </span>
                              <span className="flex-1">{item.label}</span>
                              {active && (
                                <span className="h-1.5 w-1.5 rounded-full bg-[var(--color-primary)]" />
                              )}
                            </Link>
                          );
                        })}
                      </div>
                    )}
                  </div>
                );
              })}
            </nav>
          </div>

          <div className="border-t border-[var(--color-border)] p-3 shrink-0">
            <div className="mb-2 px-3">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
                Account
              </span>
            </div>
            <div className="flex flex-col gap-0.5">
              {bottomItems.map((item) => {
                const active = isActive(item.href);
                return (
                   <Link
                     key={item.href}
                     href={item.href}
                     onClick={() => setSidebarOpen(false)}
                     className={cn(
                       "group flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-200 border-l-2 border-l-transparent",
                       active
                         ? "bg-[var(--color-primary-soft)] text-[var(--color-primary)] border-l-[var(--color-primary)]"
                         : "text-[var(--color-text-muted)] hover:bg-[var(--color-muted)] hover:text-[var(--color-text-primary)] hover:border-l-[var(--color-border)]"
                     )}
                   >
                    <span
                      className={cn(
                        "flex h-5 w-5 items-center justify-center rounded transition-colors text-[10px] font-bold",
                        active ? "text-[var(--color-primary)]" : "text-[var(--color-text-muted)] group-hover:text-[var(--color-text-primary)]"
                      )}
                    >
                      {item.marker}
                    </span>
                    <span className="flex-1">{item.label}</span>
                    {active && (
                      <span className="h-1.5 w-1.5 rounded-full bg-[var(--color-primary)]" />
                    )}
                  </Link>
                );
              })}
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
