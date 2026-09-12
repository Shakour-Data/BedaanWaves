"use client";

import { useState, useEffect, useMemo, useCallback, memo } from "react";
import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import {
  LayoutDashboard,
  BarChart3,
  TrendingUpDown,
  Briefcase,
  PieChart,
  Brain,
  Filter,
  Wallet,
  Trophy,
  AreaChart,
  GitCompare,
  Palette,
  Activity,
  Globe,
  Newspaper,
  Bell,
  Search,
  Eye,
  BookOpen,
  HelpCircle,
  Settings,
  User,
  House,
  Info,
  Sparkles,
  Book,
  Mail,
  ChevronDown,
  ChevronUp,
  LogOut,
} from "lucide-react";
import { useAppStore } from "@/store/useAppStore";
import { useAuthStore } from "@/store/useAuthStore";
import { cn } from "@/lib/cn";
import { UnifiedSearchBar } from "@/components/search/UnifiedSearchBar";
import { sidebarCategories, sidebarBottomItems, type NavItem, type NavCategory } from "@/lib/sidebar-config";

type IconComponent = React.ComponentType<React.SVGProps<SVGSVGElement>>;

const ICON_MAP: Record<string, IconComponent> = {
  LayoutDashboard,
  BarChart3,
  TrendingUpDown,
  Briefcase,
  PieChart,
  Brain,
  Filter,
  Wallet,
  Trophy,
  AreaChart,
  GitCompare,
  Palette,
  Activity,
  Globe,
  Newspaper,
  Bell,
  Search,
  Eye,
  BookOpen,
  HelpCircle,
  Settings,
  User,
  House,
  Info,
  Sparkles,
  Book,
  Mail,
  ChevronDown,
  ChevronUp,
  LogOut,
};

interface SidebarIconProps {
  name: string;
  className?: string;
}

const SidebarIcon = memo(({ name, className }: SidebarIconProps) => {
  const Icon = ICON_MAP[name] ?? Search;
  return <Icon className={cn("h-5 w-5 shrink-0", className)} />;
});
SidebarIcon.displayName = "SidebarIcon";

const cleanPath = (p: string) => p.split("?")[0];

const isCategoryActive = (items: NavItem[], checkActive: (href: string) => boolean) =>
  items.some((item) => checkActive(item.href));

const SIDEBAR_WIDTH = "16rem";

const SidebarComponent = () => {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const sidebarOpen = useAppStore((state) => state.sidebarOpen);
  const setSidebarOpen = useAppStore((state) => state.setSidebarOpen);
  const { user, logout } = useAuthStore();

  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(() => {
    const initial = new Set<string>();
    sidebarCategories.forEach((cat) => {
      if (isCategoryActive(cat.items, (href) => {
        const hrefPath = cleanPath(href);
        const currentPath = cleanPath(pathname);
        return currentPath === hrefPath || currentPath.startsWith(`${hrefPath}/`);
      })) {
        initial.add(cat.label);
      }
    });
    if (initial.size === 0) {
      sidebarCategories.slice(0, 1).forEach((cat) => initial.add(cat.label));
    }
    return initial;
  });

  const isActive = useCallback((href: string) => {
    const hrefPath = cleanPath(href);
    const currentPath = cleanPath(pathname);
    const currentQuery = searchParams.toString();
    const hrefQuery = href.split("?")[1] ?? "";

    if (hrefPath === "/dashboard") {
      return (
        currentPath === "/" ||
        currentPath === "/dashboard" ||
        currentPath.startsWith("/dashboard/")
      );
    }
    if (hrefPath === "/") return currentPath === "/";

    if (hrefQuery) {
      return currentPath === hrefPath && currentQuery === hrefQuery;
    }
    return currentPath === hrefPath || currentPath.startsWith(`${hrefPath}/`);
  }, [pathname, searchParams]);

  const autoExpanded = useMemo(() => {
    const auto = new Set<string>();
    sidebarCategories.forEach((cat) => {
      if (isCategoryActive(cat.items, isActive)) {
        auto.add(cat.label);
      }
    });
    return auto;
  }, [isActive]);

  const allExpanded = useMemo(
    () => new Set([...autoExpanded, ...expandedCategories]),
    [autoExpanded, expandedCategories]
  );

  useEffect(() => {
    document.body.style.overflow = sidebarOpen ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [sidebarOpen]);

  const toggleCategory = useCallback((label: string) => {
    setExpandedCategories((prev) => {
      const next = new Set(prev);
      if (next.has(label)) {
        next.delete(label);
      } else {
        next.add(label);
      }
      return next;
    });
  }, []);

  const renderNavItem = (item: NavItem, isBottom: boolean = false) => {
    const active = isActive(item.href);
    return (
      <Link
        key={item.href}
        href={item.href}
        onClick={() => setSidebarOpen(false)}
        className={cn(
          "group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium",
          "transition-all duration-200 ease-out min-h-[44px]",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-primary)]/30",
          active
            ? "bg-[var(--color-primary-soft)] text-[var(--color-primary)]"
            : "text-[var(--color-text-secondary)] hover:bg-[var(--color-muted)] hover:text-[var(--color-text-primary)]"
        )}
      >
        <span
          className={cn(
            "flex h-8 w-8 items-center justify-center rounded-lg transition-all duration-200",
            active
              ? "bg-[var(--color-primary)] text-white shadow-md shadow-[var(--color-primary)]/20"
              : "bg-[var(--color-muted)] text-[var(--color-text-muted)] group-hover:bg-[var(--color-primary)]/10 group-hover:text-[var(--color-primary)]"
          )}
          aria-hidden="true"
        >
          <SidebarIcon name={item.icon} className="h-4 w-4" />
        </span>
        <span className="flex-1 truncate">{item.label}</span>
        {item.badge && (
          <span
            className={cn(
              "inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase",
              item.badge === "NEW"
                ? "bg-[var(--color-success)]/10 text-[var(--color-success)]"
                : "bg-[var(--color-warning)]/10 text-[var(--color-warning)]"
            )}
            aria-label={item.badge}
          >
            {item.badge}
          </span>
        )}
        {active && !isBottom && (
          <span
            className="absolute left-0 h-5 w-0.5 rounded-full bg-[var(--color-primary)]"
            aria-hidden="true"
          />
        )}
      </Link>
    );
  };

  return (
    <>
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm lg:hidden"
          onClick={() => setSidebarOpen(false)}
          aria-hidden="true"
        />
      )}

      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 w-64 border-r bg-[var(--color-surface)] transition-transform duration-200 ease-in-out",
          "lg:translate-x-0",
          sidebarOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0",
          "lg:border-l-0 lg:border-r"
        )}
        aria-label="Main navigation"
        style={{ width: SIDEBAR_WIDTH }}
      >
        <div className="flex h-screen flex-col">
          <div className="flex h-16 items-center gap-3 border-b border-[var(--color-border)] px-5 shrink-0">
            <Link href="/dashboard" className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-accent)] text-white shadow-md">
                <span className="font-bold text-lg">B</span>
              </div>
              <div className="flex flex-col">
                <span className="text-base font-bold text-[var(--color-text-primary)] leading-tight tracking-tight">
                  BedaanWaves
                </span>
                <span className="text-[10px] font-medium text-[var(--color-text-muted)] uppercase tracking-wider leading-tight">
                  Analytics
                </span>
              </div>
            </Link>
          </div>

          <div className="flex-1 overflow-y-auto py-4">
            <div className="px-3 pb-3">
              <UnifiedSearchBar variant="sidebar" placeholder="Search stocks, news, pages..." />
            </div>

            <nav className="flex flex-col gap-1 px-3">
              {sidebarCategories.map((cat) => {
                const isExpanded = allExpanded.has(cat.label);
                const hasActive = isCategoryActive(cat.items, isActive);

                return (
                  <div key={cat.label} className="mb-1">
                    <button
                      type="button"
                      onClick={() => toggleCategory(cat.label)}
                      aria-expanded={isExpanded}
                      aria-controls={`nav-category-${cat.label.replace(/\s+/g, "-").toLowerCase()}`}
                      className={cn(
                        "flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-xs font-semibold uppercase tracking-wider transition-all duration-200",
                        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-primary)]/30 min-h-[44px]",
                        hasActive
                          ? "text-[var(--color-primary)]"
                          : "text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-muted)]"
                      )}
                    >
                      <span
                        className={cn(
                          "flex h-6 w-6 items-center justify-center rounded-md transition-colors",
                          hasActive
                            ? "bg-[var(--color-primary)]/15 text-[var(--color-primary)]"
                            : "text-[var(--color-text-muted)]"
                        )}
                        aria-hidden="true"
                      >
                        <SidebarIcon name={cat.icon} className="h-3.5 w-3.5" />
                      </span>
                      <span className="flex-1 text-left">{cat.label}</span>
                      <span
                        className={cn(
                          "text-xs text-[var(--color-text-muted)] transition-transform duration-200 font-mono flex-shrink-0",
                          isExpanded && "rotate-180"
                        )}
                        aria-hidden="true"
                      >
                        {isExpanded ? (
                          <ChevronUp className="h-4 w-4" />
                        ) : (
                          <ChevronDown className="h-4 w-4" />
                        )}
                      </span>
                    </button>

                    {isExpanded && (
                      <div
                        id={`nav-category-${cat.label.replace(/\s+/g, "-").toLowerCase()}`}
                        className="ml-3 mt-1 flex flex-col gap-0.5"
                      >
                        {cat.items.map((item) => renderNavItem(item))}
                      </div>
                    )}
                  </div>
                );
              })}
            </nav>
          </div>

          <div className="border-t border-[var(--color-border)] p-3 shrink-0">
            <div className="mb-3 px-3">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
                Account
              </span>
            </div>
            <div className="flex flex-col gap-0.5">
              {sidebarBottomItems.map((item) => renderNavItem(item, true))}
            </div>

            {user && (
              <div className="mt-3 border-t border-[var(--color-border)] pt-2">
                <div className="flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-accent)] text-xs font-semibold text-white">
                    {user.full_name?.[0] || user.username?.[0] || "U"}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-[var(--color-text-primary)] truncate">
                      {user.full_name || user.username || "User"}
                    </p>
                    <p className="text-xs text-[var(--color-text-muted)] truncate">
                      {user.email || ""}
                    </p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={logout}
                  className={cn(
                    "w-full flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-[var(--color-text-secondary)]",
                    "transition-all duration-200 hover:bg-[var(--color-error)]/10 hover:text-[var(--color-error)]",
                    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-error)]/30 min-h-[44px]"
                  )}
                >
                  <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--color-error)]/10 text-[var(--color-error)]">
                    <LogOut className="h-4 w-4" />
                  </span>
                  <span>Sign Out</span>
                </button>
              </div>
            )}

            <div className="mt-3 px-3 text-center">
              <p className="text-[10px] text-[var(--color-text-muted)]">
                <span className="font-mono">Cmd</span> + <span className="font-mono">K</span> — Quick search
              </p>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};

export const NewSidebar = memo(SidebarComponent);
