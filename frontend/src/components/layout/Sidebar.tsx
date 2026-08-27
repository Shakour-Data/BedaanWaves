"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/cn";
import { useAuthStore } from "@/store/useAuthStore";
import {
  DashboardIcon,
  StockIcon,
  PortfolioIcon,
  AnalysisIcon,
  NewsIcon,
  AlertIcon,
  ScoringIcon,
  MethodologyIcon,
  HelpIcon,
  SettingsIcon,
  LoginIcon,
  UserIcon,
} from "@/components/icons/Icons";

interface NavItem {
  href: string;
  label: string;
  Icon: React.ComponentType<{ className?: string }>;
  ready: boolean;
}

const AUTH_ITEM: NavItem = { href: "/login", label: "ورود", Icon: LoginIcon, ready: true };

export function Sidebar() {
  const pathname = usePathname();
  const { isAuthenticated, user, logout } = useAuthStore();

  const navItems: NavItem[] = isAuthenticated
    ? [
        { href: "/dashboard", label: "داشبورد", Icon: DashboardIcon, ready: true },
        { href: "/stocks", label: "سهام", Icon: StockIcon, ready: true },
        { href: "/portfolio", label: "پورتفولیو", Icon: PortfolioIcon, ready: true },
        { href: "/analysis", label: "تحلیل", Icon: AnalysisIcon, ready: true },
        { href: "/news", label: "اخبار", Icon: NewsIcon, ready: true },
        { href: "/alerts", label: "هشدارها", Icon: AlertIcon, ready: true },
        { href: "/scoring", label: "امتیازدهی", Icon: ScoringIcon, ready: true },
        { href: "/methodology", label: "روش‌شناسی", Icon: MethodologyIcon, ready: true },
        { href: "/help", label: "راهنما", Icon: HelpIcon, ready: true },
        { href: "/settings", label: "تنظیمات", Icon: SettingsIcon, ready: true },
      ]
    : [
        { href: "/dashboard", label: "داشبورد", Icon: DashboardIcon, ready: true },
        { href: "/stocks", label: "سهام", Icon: StockIcon, ready: true },
        AUTH_ITEM,
      ];

  return (
    <aside
      className={cn(
        "h-full w-64 shrink-0 border-l border-border",
        "flex flex-col gap-2 p-3 bg-background",
      )}
    >
      <div className="mb-3 flex items-center gap-2 px-1">
        <span className="text-2xl font-bold text-primary" aria-hidden="true">
          B
        </span>
        <span className="text-lg font-bold text-foreground">BedaanWaves</span>
      </div>

      <nav className="flex flex-col gap-1" aria-label="منوی اصلی">
        {navItems.map((item) => {
          const active = pathname === item.href;
          const inner = (
            <span
              className={cn(
                "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition duration-fast ease-flow",
                active
                  ? "bg-primary/10 text-primary font-bold shadow-sm"
                  : "text-muted-foreground hover:bg-neutral hover:text-foreground",
              )}
            >
              <item.Icon className="h-5 w-5" />
              <span className="flex-1">{item.label}</span>
              {!item.ready ? (
                <span className="rounded-full bg-accent/30 px-2 py-0.5 text-xs text-accent-foreground">
                  به‌زودی
                </span>
              ) : null}
            </span>
          );

          if (item.ready) {
            return (
              <Link key={item.href} href={item.href} aria-current={active ? "page" : undefined}>
                {inner}
              </Link>
            );
          }
          return (
            <span key={item.href} aria-disabled="true" title="به‌زودی">
              {inner}
            </span>
          );
        })}
      </nav>

      <div className="mt-auto flex flex-col gap-2">
        {isAuthenticated && user ? (
          <div className="rounded-xl bg-neutral/60 p-3 text-xs text-muted-foreground">
            <div className="flex items-center gap-2">
              <UserIcon className="h-4 w-4" />
              <span className="flex-1 truncate">{user.name}</span>
            </div>
            <button
              type="button"
              onClick={logout}
              className="mt-2 w-full rounded-lg border border-border px-2 py-1 text-xs transition duration-fast ease-flow hover:bg-black/5"
            >
              خروج
            </button>
          </div>
        ) : null}
        <div className="rounded-xl bg-neutral/60 p-3 text-xs text-muted-foreground">
          معماری ارتعاشی بازار سرمایه
        </div>
      </div>
    </aside>
  );
}

