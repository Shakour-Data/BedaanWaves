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
import {
  sidebarCategories,
  sidebarBottomItems,
  type NavItem,
  type NavCategory,
} from "@/lib/sidebar-config";

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

const cleanPath = (p: string) => p.split("?")[0];

const isCategoryActive = (items: NavItem[], checkActive: (href: string) => boolean) =>
  items.some((item) => checkActive(item.href));

const SidebarIcon = memo(({ name, className }: { name: string; className?: string }) => {
  const Icon = ICON_MAP[name] ?? Search;
  return <Icon className={cn("h-5 w-5 shrink-0", className)} />;
});
SidebarIcon.displayName = "SidebarIcon";

const SIDEBAR_WIDTH = "16rem";

const RightSidebarComponent = () => {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const sidebarOpen = useAppStore((state) => state.rightSidebarOpen);
  const setSidebarOpen = useAppStore((state) => state.setRightSidebarOpen);
  const { user } = useAuthStore();

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