"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/cn";
import { useAuthStore } from "@/store/useAuthStore";
import { semanticColors } from "@/styles/design-tokens";

interface NavItem {
  href: string;
  label: string;
  icon: string;
  ready: boolean;
}

const AUTH_ITEM: NavItem = { href: "/login", label: "ورود", icon: "🔐", ready: true };

export function Sidebar() {
  const pathname = usePathname();
  const { isAuthenticated, user, logout } = useAuthStore();

  const navItems: NavItem[] = isAuthenticated
    ? [
        { href: "/dashboard", label: "داشبورد", icon: "🏠", ready: true },
        { href: "/stocks", label: "سهام", icon: "🏢", ready: true },
        { href: "/portfolio", label: "پورتفولیو", icon: "💼", ready: true },
        { href: "/analysis", label: "تحلیل", icon: "🔮", ready: true },
        { href: "/news", label: "اخبار", icon: "📰", ready: true },
        { href: "/alerts", label: "هشدارها", icon: "🔔", ready: true },
        { href: "/scoring", label: "امتیازدهی", icon: "🧮", ready: true },
        { href: "/methodology", label: "روش‌شناسی", icon: "📚", ready: true },
        { href: "/help", label: "راهنما", icon: "📖", ready: true },
        { href: "/settings", label: "تنظیمات", icon: "⚙️", ready: true },
      ]
    : [
        { href: "/dashboard", label: "داشبورد", icon: "🏠", ready: true },
        { href: "/stocks", label: "سهام", icon: "🏢", ready: true },
        AUTH_ITEM,
      ];

  return (
    <aside
      className={cn(
        "h-full w-64 shrink-0 border-l border-[var(--color-border)]",
        "flex flex-col gap-2 p-3 bg-[var(--color-background)]",
      )}
    >
      <div className="mb-3 flex items-center gap-2 px-1">
        <span className="text-2xl" aria-hidden="true">
          🌊
        </span>
        <span className="text-lg font-bold text-foreground">BedaanWaves</span>
      </div>

      <nav className="flex flex-col gap-1" aria-label="منوی اصلی">
        {navItems.map((item) => {
          const active = pathname === item.href;
          const inner = (
            <span
              className={cn(
                "flex items-center gap-3 rounded-xl px-3 py-2 text-sm transition-colors duration-150",
                active
                  ? `bg-[${semanticColors.secondary}]/10 font-semibold text-[${semanticColors.secondary}]`
                  : "text-muted-foreground hover:bg-black/5 hover:text-foreground",
              )}
            >
              <span className="text-xl" aria-hidden="true">
                {item.icon}
              </span>
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
          <div className="rounded-xl bg-[var(--color-neutral)]/60 p-3 text-xs text-muted-foreground">
            <div className="flex items-center gap-2">
              <span aria-hidden="true">👤</span>
              <span className="flex-1 truncate">{user.name}</span>
            </div>
            <button
              type="button"
              onClick={logout}
              className="mt-2 w-full rounded-lg border border-[var(--color-border)] px-2 py-1 text-xs transition-colors duration-150 hover:bg-black/5"
            >
              خروج
            </button>
          </div>
        ) : null}
        <div className="rounded-xl bg-[var(--color-neutral)]/60 p-3 text-xs text-muted-foreground">
          معماری ارتعاشی بازار سرمایه
        </div>
      </div>
    </aside>
  );
}
