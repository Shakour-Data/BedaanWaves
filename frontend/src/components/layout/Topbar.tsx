"use client";

import { useAppStore } from "@/store/useAppStore";
import { cn } from "@/lib/cn";

interface TopbarProps {
  title: string;
}

export function Topbar({ title }: TopbarProps) {
  const { theme, toggleTheme, toggleSidebar } = useAppStore();

  return (
    <header className="tarot-card sticky top-0 z-20 flex items-center gap-3 rounded-none border-b border-border px-3 py-2">
      <button
        type="button"
        onClick={toggleSidebar}
        aria-label="باز/بستن منو"
        className="rounded-xl p-2 text-xl text-muted-foreground transition duration-fast ease-flow hover:bg-black/5 hover:text-foreground"
      >
        ☰
      </button>

      <h2 className="text-lg font-semibold">{title}</h2>

      <div className="ms-auto flex items-center gap-2">
        <label className="hidden items-center gap-2 rounded-xl bg-neutral/60 px-3 py-2 text-sm text-muted-foreground sm:flex">
          <span aria-hidden="true">🔍</span>
          <input
            type="search"
            placeholder="جست‌وجوی نماد…"
            className="bg-transparent text-foreground outline-none placeholder:text-muted-foreground/70"
          />
        </label>

        <button
          type="button"
          onClick={toggleTheme}
          aria-label="تغییر تم"
          className={cn(
            "rounded-xl p-2 text-xl transition duration-fast ease-flow hover:bg-black/5",
            theme === "dark" ? "text-accent" : "text-muted-foreground",
          )}
        >
          {theme === "dark" ? "🌙" : "☀️"}
        </button>

        <div className="flex items-center gap-2 rounded-xl bg-secondary/10 px-3 py-2 text-sm text-secondary">
          <span aria-hidden="true">👤</span>
          <span className="hidden sm:inline">کاربر نمایشی</span>
        </div>
      </div>
    </header>
  );
}
