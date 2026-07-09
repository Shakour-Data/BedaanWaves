"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/cn";

interface NavItem {
  href: string;
  label: string;
  icon: string;
  ready: boolean;
}

const NAV_ITEMS: NavItem[] = [
  { href: "/dashboard", label: "داشبورد", icon: "🏠", ready: true },
  { href: "/market", label: "بازار", icon: "📈", ready: false },
  { href: "/stocks", label: "سهام", icon: "🏢", ready: false },
  { href: "/portfolio", label: "پورتفولیو", icon: "💼", ready: false },
  { href: "/analysis", label: "تحلیل", icon: "🔮", ready: false },
  { href: "/news", label: "اخبار", icon: "📰", ready: false },
  { href: "/alerts", label: "هشدارها", icon: "🔔", ready: false },
  { href: "/settings", label: "تنظیمات", icon: "⚙️", ready: false },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside
      className={cn(
        "tarot-card h-full w-64 shrink-0 rounded-none border-l border-border",
        "flex flex-col gap-2 p-3",
      )}
    >
      <div className="mb-3 flex items-center gap-2 px-1">
        <span className="text-2xl" aria-hidden="true">
          🌊
        </span>
        <span className="text-lg font-bold">BedaanWaves</span>
      </div>

      <nav className="flex flex-col gap-1" aria-label="منوی اصلی">
        {NAV_ITEMS.map((item) => {
          const active = pathname === item.href;
          const inner = (
            <span
              className={cn(
                "flex items-center gap-3 rounded-xl px-3 py-2 text-sm transition",
                "duration-fast ease-flow",
                active
                  ? "bg-secondary/10 font-semibold text-secondary"
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

      <div className="mt-auto rounded-xl bg-neutral/60 p-3 text-xs text-muted-foreground">
        معماری ارتعاشی بازار سرمایه
      </div>
    </aside>
  );
}
