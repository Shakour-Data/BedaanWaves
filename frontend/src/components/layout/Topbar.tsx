"use client";

import { useAppStore } from "@/store/useAppStore";
import { cn } from "@/lib/cn";
import { useAuthStore } from "@/store/useAuthStore";
import { SunIcon, MoonIcon, UserIcon, LogoutIcon } from "@/components/icons/Icons";

interface TopbarProps {
  title: string;
}

export function Topbar({ title }: TopbarProps) {
  const { theme, toggleTheme } = useAppStore();
  const { user, logout } = useAuthStore();

  return (
    <header className="sticky top-0 z-20 flex items-center gap-3 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2">
      <h2 className="text-lg font-semibold text-foreground">{title}</h2>

      <div className="ms-auto flex items-center gap-2">
        <button
          type="button"
          onClick={toggleTheme}
          aria-label="تغییر تم"
          className={cn(
            "rounded-xl p-2 transition-colors duration-150",
            theme === "dark" ? "text-accent" : "text-muted-foreground hover:text-foreground",
          )}
        >
          {theme === "dark" ? <MoonIcon className="h-5 w-5" /> : <SunIcon className="h-5 w-5" />}
        </button>

        <div className="flex items-center gap-2 rounded-xl bg-[var(--color-secondary)]/10 px-3 py-2 text-sm text-[var(--color-secondary)]">
          <UserIcon className="h-4 w-4" />
          <span className="hidden sm:inline">{user?.name || "کاربر نمایشی"}</span>
        </div>

        <button
          type="button"
          onClick={logout}
          aria-label="خروج"
          className="rounded-xl p-2 text-muted-foreground transition-colors duration-150 hover:text-foreground"
        >
          <LogoutIcon className="h-5 w-5" />
        </button>
      </div>
    </header>
  );
}

