"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/cn";
import { useAuthStore } from "@/store/useAuthStore";
import { t } from "@/lib/i18n";

interface NavItem {
  href: string;
  label: string;
  icon: string;
  ready: boolean;
}

export function Sidebar() {
  const pathname = usePathname();
  const { isAuthenticated, user, logout, currentLang } = useAuthStore();

  const navItems: NavItem[] = isAuthenticated
    ? [
        { href: "/dashboard", label: t("app.nav.dashboard", currentLang), icon: "📊", ready: true },
        { href: "/stocks", label: t("app.nav.stocks", currentLang), icon: "📈", ready: true },
        { href: "/portfolio", label: t("app.nav.portfolio", currentLang), icon: "💼", ready: true },
        { href: "/analysis", label: t("app.nav.analysis", currentLang), icon: "🔍", ready: true },
        { href: "/news", label: t("app.nav.news", currentLang), icon: "📰", ready: true },
        { href: "/alerts", label: t("app.nav.alerts", currentLang), icon: "🔔", ready: true },
        { href: "/scoring", label: t("app.nav.scoring", currentLang), icon: "💯", ready: true },
        { href: "/methodology", label: t("app.nav.methodology", currentLang), icon: "📘", ready: true },
        { href: "/help", label: t("app.nav.help", currentLang), icon: "❓", ready: true },
        { href: "/settings", label: t("app.nav.settings", currentLang), icon: "⚙️", ready: true },
      ]
    : [
        { href: "/dashboard", label: t("app.nav.dashboard", currentLang), icon: "📊", ready: true },
        { href: "/stocks", label: t("app.nav.stocks", currentLang), icon: "📈", ready: true },
        { href: "/login", label: t("app.auth.login", currentLang), icon: "🔑", ready: true },
      ];

  return (
    <aside
      className={cn(
        "h-full w-64 shrink-0 border-e border-border",
        "flex flex-col gap-2 p-3 bg-background",
      )}
    >
      <div className="mb-3 flex items-center gap-2 px-1">
        <span className="text-2xl" aria-hidden="true">
          🌊
        </span>
        <span className="text-lg font-bold text-foreground">BedaanWaves</span>
      </div>

      <nav className="flex flex-col gap-1" aria-label={t("app.nav.dashboard", currentLang)}>
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
              <span className="text-xl" aria-hidden="true">
                {item.icon}
              </span>
              <span className="flex-1">{item.label}</span>
              {!item.ready ? (
                <span className="rounded-full bg-accent/30 px-2 py-0.5 text-xs text-accent-foreground">
                  {t("app.portfolio.coming_soon", currentLang)}
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
            <span key={item.href} aria-disabled="true" title={t("app.portfolio.coming_soon", currentLang)}>
              {inner}
            </span>
          );
        })}
      </nav>

      <div className="mt-auto flex flex-col gap-2">
        {isAuthenticated && user ? (
          <div className="rounded-xl bg-neutral/60 p-3 text-xs text-muted-foreground">
            <div className="flex items-center gap-2">
              <span aria-hidden="true">👤</span>
              <span className="flex-1 truncate">{user.name}</span>
            </div>
            <button
              type="button"
              onClick={logout}
              className="mt-2 w-full rounded-lg border border-border px-2 py-1 text-xs transition duration-fast ease-flow hover:bg-black/5"
            >
              {t("app.nav.logout", currentLang)}
            </button>
          </div>
        ) : null}
        <div className="rounded-xl bg-neutral/60 p-3 text-xs text-muted-foreground">
          {t("app.subtitle", currentLang)}
        </div>
      </div>
    </aside>
  );
}

