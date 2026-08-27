"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/cn";

interface NavItem {
  label: string;
  href: string;
}

const mainNavItems: NavItem[] = [
  { label: "Dashboard", href: "/dashboard" },
  { label: "Stocks", href: "/stocks" },
  { label: "Scoring", href: "/scoring" },
  { label: "Analysis", href: "/analysis" },
  { label: "Portfolio", href: "/portfolio" },
  { label: "News", href: "/news" },
  { label: "Alerts", href: "/alerts" },
];

const bottomNavItems: NavItem[] = [
  { label: "Settings", href: "/settings" },
  { label: "Help", href: "/help" },
];

export function NewSidebar() {
  const pathname = usePathname();

  const isActive = (href: string) => {
    if (href === "/dashboard") {
      return pathname === href;
    }
    return pathname.startsWith(href);
  };

  return (
    <aside className="fixed left-0 top-0 z-40 h-screen w-64 bg-[var(--color-background)] border-r border-[var(--color-border)]">
      {/* Logo */}
      <div className="flex h-16 items-center border-b border-[var(--color-border)] px-6">
        <Link href="/dashboard" className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[var(--color-primary)] text-white">
            <span className="font-bold text-lg">N</span>
          </div>
          <div className="flex flex-col">
            <span className="text-lg font-bold text-[var(--color-text-primary)]">NasdaqPulse</span>
            <span className="text-[10px] text-[var(--color-text-secondary)] uppercase tracking-wider">Analytics</span>
          </div>
        </Link>
      </div>

      {/* Main Navigation */}
      <div className="flex flex-col gap-1 p-4">
        <div className="mb-2 px-2">
          <span className="text-[10px] font-semibold uppercase tracking-wider text-[var(--color-text-secondary)]">
            Main Menu
          </span>
        </div>
        {mainNavItems.map((item) => {
          const active = isActive(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200",
                active
                  ? "bg-[var(--color-primary)]/10 text-[var(--color-primary)] border-l-2 border-[var(--color-primary)]"
                  : "text-[var(--color-text-secondary)] hover:bg-[var(--color-border)] hover:text-[var(--color-text-primary)]"
              )}
            >
              <span className={cn("h-5 w-5 flex items-center justify-center transition-colors", active ? "text-[var(--color-primary)]" : "text-[var(--color-text-secondary)] group-hover:text-[var(--color-text-primary)]")}>
                {item.label[0]}
              </span>
              <span>{item.label}</span>
              {active && (
                <div className="ml-auto h-1.5 w-1.5 rounded-full bg-[var(--color-primary)] animate-pulse" />
              )}
            </Link>
          );
        })}
      </div>

      {/* Bottom Navigation */}
      <div className="absolute bottom-0 left-0 right-0 border-t border-[var(--color-border)] bg-[var(--color-background)] p-4">
        <div className="flex flex-col gap-1">
          {bottomNavItems.map((item) => {
            const active = isActive(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "group flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-200",
                  active
                    ? "bg-[var(--color-primary)]/10 text-[var(--color-primary)]"
                    : "text-[var(--color-text-secondary)] hover:bg-[var(--color-border)] hover:text-[var(--color-text-primary)]"
                )}
              >
                <span className="h-4 w-4 flex items-center justify-center">{item.label[0]}</span>
                <span>{item.label}</span>
              </Link>
            );
          })}
        </div>
      </div>
    </aside>
  );
}
