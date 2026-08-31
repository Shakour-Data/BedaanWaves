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
  { label: "Methodology", href: "/methodology" },
];

const dashboardTabs: NavItem[] = [
  { label: "General", href: "/dashboard" },
  { label: "Technical", href: "/dashboard" },
  { label: "Fundamental", href: "/dashboard" },
  { label: "News", href: "/dashboard" },
  { label: "Risk", href: "/dashboard" },
  { label: "Board", href: "/dashboard" },
  { label: "AI", href: "/dashboard" },
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
    <aside className="fixed left-0 top-0 z-40 h-screen w-64 border-r border-border bg-background hidden lg:block">
      <div className="flex h-16 items-center border-b border-border px-6">
        <Link href="/dashboard" className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-white">
            <span className="font-bold text-lg">N</span>
          </div>
          <div className="flex flex-col">
            <span className="text-lg font-bold text-foreground">BedaanWaves</span>
            <span className="text-[10px] text-muted-foreground uppercase tracking-wider">Analytics</span>
          </div>
        </Link>
      </div>

      <div className="flex flex-col gap-1 p-4">
        <div className="mb-2 px-2">
          <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
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
                "group flex items-center rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200",
                active
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-border hover:text-foreground"
              )}
            >
              <span>{item.label}</span>
              {active && (
                <div className="ml-auto h-1.5 w-1.5 rounded-full bg-primary" />
              )}
            </Link>
          );
        })}

        <div className="mt-4 mb-2 px-2">
          <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
            Dashboards
          </span>
        </div>
        {dashboardTabs.map((item) => {
          const active = isActive(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "group flex items-center rounded-lg px-3 py-2 text-sm font-medium transition-all duration-200",
                active
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-border hover:text-foreground"
              )}
            >
              <span>{item.label}</span>
              {active && (
                <div className="ml-auto h-1.5 w-1.5 rounded-full bg-primary" />
              )}
            </Link>
          );
        })}
      </div>

      <div className="absolute bottom-0 left-0 right-0 border-t border-border bg-background p-4">
        <div className="flex flex-col gap-1">
          {bottomNavItems.map((item) => {
            const active = isActive(item.href);
            return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "group flex items-center rounded-lg px-3 py-2 text-sm font-medium transition-all duration-200",
                active
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-border hover:text-foreground"
              )}
            >
              <span>{item.label}</span>
            </Link>
            );
          })}
        </div>
      </div>
    </aside>
  );
}
