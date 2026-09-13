"use client";

import { useState, useRef, useEffect, useCallback, useMemo } from "react";
import { useRouter } from "next/navigation";
import {
  Search,
  X,
  Loader2,
  TrendingUp,
  TrendingDown,
  Building2,
  Banknote,
  Stethoscope,
  Zap,
  ShoppingBasket,
  Factory,
  Landmark,
  Plug,
  Globe,
  AlertCircle,
  Newspaper,
  FileText,
  ArrowRight,
} from "lucide-react";
import { cn } from "@/lib/cn";
import { useUnifiedSearch, type UnifiedSearchItem, type SearchGroup } from "@/hooks/useUnifiedSearch";

export interface UnifiedSearchBarProps {
  placeholder?: string;
  className?: string;
  autoFocus?: boolean;
  variant?: "sidebar" | "topbar" | "modal";
  onSelect?: () => void;
}

function HighlightedText({ text, query, className }: { text: string; query: string; className?: string }) {
  const q = query.trim().toLowerCase();
  if (!q || !text) return <>{text}</>;
  const idx = text.toLowerCase().indexOf(q);
  if (idx === -1) return <>{text}</>;
  const before = text.slice(0, idx);
  const match = text.slice(idx, idx + q.length);
  const after = text.slice(idx + q.length);
  return (
    <>
      {before}
      <mark className={cn("rounded bg-primary/20 px-0.5 text-primary", className)}>{match}</mark>
      {after}
    </>
  );
}

function SectorIcon({ sector }: { sector: string }) {
  const s = (sector || "").toLowerCase();
  if (s.includes("technology") || s.includes("software") || s.includes("semiconductor")) return <Zap className="h-4 w-4 text-primary" />;
  if (s.includes("financial") || s.includes("bank") || s.includes("insurance")) return <Banknote className="h-4 w-4 text-secondary" />;
  if (s.includes("health") || s.includes("pharma") || s.includes("biotech")) return <Stethoscope className="h-4 w-4 text-error" />;
  if (s.includes("consumer") || s.includes("retail") || s.includes("cyclical")) return <ShoppingBasket className="h-4 w-4 text-warning" />;
  if (s.includes("industrial") || s.includes("manufact") || s.includes("machinery")) return <Factory className="h-4 w-4 text-accent" />;
  if (s.includes("real estate") || s.includes("reit") || s.includes("property")) return <Landmark className="h-4 w-4 text-success" />;
  if (s.includes("utilities") || s.includes("utility")) return <Plug className="h-4 w-4 text-secondary" />;
  if (s.includes("communication") || s.includes("media") || s.includes("entertain")) return <Globe className="h-4 w-4 text-accent" />;
  return <Building2 className="h-4 w-4 text-muted-foreground" />;
}

function TrendIcon({ change }: { change: number }) {
  if (change > 0) return <TrendingUp className="h-3 w-3 text-success" />;
  if (change < 0) return <TrendingDown className="h-3 w-3 text-error" />;
  return <TrendingUp className="h-3 w-3 text-muted-foreground" />;
}

function formatTimeAgo(iso: string): string {
  if (!iso) return "";
  const t = new Date(iso).getTime();
  if (!Number.isFinite(t)) return "";
  const diff = Date.now() - t;
  if (diff < 60_000) return "just now";
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m ago`;
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}h ago`;
  return `${Math.floor(diff / 86_400_000)}d ago`;
}

const VARIANT_INPUT: Record<NonNullable<UnifiedSearchBarProps["variant"]>, string> = {
  sidebar:
    "h-10 rounded-lg border border-border bg-surface pl-9 pr-3 text-sm",
  topbar:
    "h-10 w-full rounded-xl border border-border bg-background pl-10 pr-10 text-sm",
  modal:
    "h-12 w-full rounded-xl border border-border bg-surface pl-12 pr-12 text-base",
};

const VARIANT_WRAPPER: Record<NonNullable<UnifiedSearchBarProps["variant"]>, string> = {
  sidebar: "w-full",
  topbar: "w-full",
  modal: "w-full",
};

const VARIANT_ICON_LEFT: Record<NonNullable<UnifiedSearchBarProps["variant"]>, string> = {
  sidebar: "left-3 h-4 w-4",
  topbar: "left-3 h-4 w-4",
  modal: "left-4 h-5 w-5",
};

const VARIANT_ICON_RIGHT: Record<NonNullable<UnifiedSearchBarProps["variant"]>, string> = {
  sidebar: "right-3 h-4 w-4",
  topbar: "right-3 h-4 w-4",
  modal: "right-4 h-5 w-5",
};

const VARIANT_DROPDOWN_WIDTH: Record<NonNullable<UnifiedSearchBarProps["variant"]>, string> = {
  sidebar: "w-[22rem] max-w-[calc(100vw-1rem)]",
  topbar: "w-[28rem] max-w-[calc(100vw-1rem)]",
  modal: "w-[40rem] max-w-[calc(100vw-1rem)]",
};

function StockResult({ item, query, active }: { item: Extract<UnifiedSearchItem, { kind: "stock" }>; query: string; active: boolean }) {
  const isPositive = item.change >= 0;
  const changePct = item.price > 0 ? (item.change / item.price) * 100 : 0;
  return (
    <div className="flex items-center gap-3 px-4 py-2.5">
      <div
        className={cn(
          "flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-xs font-bold",
          active ? "bg-primary/20 text-primary" : "bg-primary/10 text-primary"
        )}
      >
        <SectorIcon sector={item.sector} />
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-sm text-foreground">
            <HighlightedText text={item.symbol} query={query} />
          </span>
          <span
            className={cn(
              "inline-flex items-center gap-0.5 text-xs font-medium",
              isPositive ? "text-success" : "text-error"
            )}
          >
            <TrendIcon change={item.change} />
            {isPositive ? "+" : ""}
            {changePct.toFixed(2)}%
          </span>
        </div>
        <p className="truncate text-xs text-muted-foreground">
          <HighlightedText text={item.name} query={query} />
        </p>
      </div>
      <div className="shrink-0 text-right">
        <p className="text-sm font-semibold text-foreground">${item.price.toFixed(2)}</p>
      </div>
    </div>
  );
}

function NewsResult({ item, query, active }: { item: Extract<UnifiedSearchItem, { kind: "news" }>; query: string; active: boolean }) {
  return (
    <div className="flex items-start gap-3 px-4 py-2.5">
      <div
        className={cn(
          "flex h-9 w-9 shrink-0 items-center justify-center rounded-lg",
          active ? "bg-primary/20 text-primary" : "bg-muted text-muted-foreground"
        )}
      >
        <Newspaper className="h-4 w-4" />
      </div>
      <div className="min-w-0 flex-1">
        <p className="line-clamp-1 text-sm font-medium text-foreground">
          <HighlightedText text={item.title} query={query} />
        </p>
        <p className="text-xs text-muted-foreground">
          {item.source}
          {item.publishedAt ? ` · ${formatTimeAgo(item.publishedAt)}` : ""}
          {item.isMarketMoving ? " · Market-moving" : ""}
        </p>
      </div>
    </div>
  );
}

function PageResult({ item, query, active }: { item: Extract<UnifiedSearchItem, { kind: "page" }>; query: string; active: boolean }) {
  return (
    <div className="flex items-start gap-3 px-4 py-2.5">
      <div
        className={cn(
          "flex h-9 w-9 shrink-0 items-center justify-center rounded-lg",
          active ? "bg-primary/20 text-primary" : "bg-muted text-muted-foreground"
        )}
      >
        <FileText className="h-4 w-4" />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium text-foreground">
          <HighlightedText text={item.title} query={query} />
        </p>
        <p className="truncate text-xs text-muted-foreground">
          {item.category} · {item.description}
        </p>
      </div>
      <ArrowRight className="h-3.5 w-3.5 text-muted-foreground" />
    </div>
  );
}

export function UnifiedSearchBar({
  placeholder = "Search stocks, news, pages…",
  className,
  autoFocus = false,
  variant = "sidebar",
  onSelect,
}: UnifiedSearchBarProps) {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [isOpen, setIsOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);

  const search = useUnifiedSearch();

  const flatItems = useMemo<UnifiedSearchItem[]>(() => {
    const out: UnifiedSearchItem[] = [];
    for (const g of search.groups) {
      for (const it of g.items) out.push(it);
    }
    return out;
  }, [search.groups]);

  const indexByKey = useMemo(() => {
    const map = new Map<string, number>();
    flatItems.forEach((it, idx) => {
      const key =
        it.kind === "stock"
          ? `stock-${it.symbol}`
          : it.kind === "news"
          ? `news-${it.id}`
          : `page-${it.id}`;
      map.set(key, idx);
    });
    return map;
  }, [flatItems]);

  const isLoading = search.status === "loading";
  const isEmpty = search.status === "empty";
  const hasError = search.status === "error";
  const showDropdown = isOpen && (isLoading || isEmpty || hasError || flatItems.length > 0);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
        setActiveIndex(-1);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    if (autoFocus) {
      inputRef.current?.focus();
    }
  }, [autoFocus]);

  const selectItem = useCallback(
    (item: UnifiedSearchItem) => {
      setIsOpen(false);
      setActiveIndex(-1);
      inputRef.current?.blur();
      onSelect?.();
      if (item.kind === "stock") {
        router.push(`/stocks/${item.symbol}`);
      } else if (item.kind === "news") {
        if (item.url) {
          window.open(item.url, "_blank", "noopener,noreferrer");
        } else {
          router.push(`/news?q=${encodeURIComponent(item.title)}`);
        }
      } else if (item.kind === "page") {
        router.push(item.href);
      }
    },
    [router, onSelect]
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === "Escape") {
        setIsOpen(false);
        setActiveIndex(-1);
        inputRef.current?.blur();
        return;
      }
      if (flatItems.length === 0) {
        if (e.key === "ArrowDown" || e.key === "Enter") {
          setIsOpen(true);
          e.preventDefault();
        }
        return;
      }
      switch (e.key) {
        case "ArrowDown":
          e.preventDefault();
          setActiveIndex((prev) => (prev + 1) % flatItems.length);
          break;
        case "ArrowUp":
          e.preventDefault();
          setActiveIndex((prev) => (prev - 1 + flatItems.length) % flatItems.length);
          break;
        case "Enter":
          e.preventDefault();
          if (activeIndex >= 0 && activeIndex < flatItems.length) {
            selectItem(flatItems[activeIndex]);
          } else if (flatItems.length > 0) {
            selectItem(flatItems[0]);
          }
          break;
      }
    },
    [flatItems, activeIndex, selectItem]
  );

  const handleClear = useCallback(() => {
    search.clear();
    inputRef.current?.focus();
  }, [search]);

  return (
    <div ref={containerRef} className={cn(VARIANT_WRAPPER[variant], className)}>
      <div className="relative">
        <span
          className={cn(
            "absolute top-1/2 -translate-y-1/2 text-muted-foreground pointer-events-none",
            VARIANT_ICON_LEFT[variant]
          )}
          aria-hidden="true"
        >
          <Search className="h-full w-full" />
        </span>

        <input
          ref={inputRef}
          type="text"
          role="combobox"
          autoComplete="off"
          autoCapitalize="none"
          spellCheck={false}
          aria-autocomplete="list"
          aria-controls="unified-search-listbox"
          aria-expanded={showDropdown}
          placeholder={placeholder}
          value={search.query}
          onChange={(e) => {
            search.setQuery(e.target.value);
            setIsOpen(true);
          }}
          onFocus={() => {
            setIsOpen(true);
          }}
          onKeyDown={handleKeyDown}
          className={cn(
            VARIANT_INPUT[variant],
            "text-foreground placeholder:text-muted-foreground transition-colors duration-150",
            "focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
          )}
        />

        {search.query && !isLoading && (
          <button
            type="button"
            onClick={handleClear}
            className={cn(
              "absolute top-1/2 -translate-y-1/2 rounded p-1 text-muted-foreground hover:text-foreground hover:bg-muted transition-colors",
              VARIANT_ICON_RIGHT[variant]
            )}
            aria-label="Clear search"
          >
            <X className="h-full w-full" />
          </button>
        )}
      </div>

      {showDropdown && (
        <div
          className={cn(
            "absolute left-0 top-full z-50 mt-2 rounded-xl border border-border bg-surface shadow-2xl overflow-hidden",
            VARIANT_DROPDOWN_WIDTH[variant]
          )}
        >
          <div className="max-h-[60vh] overflow-y-auto">
            {isLoading && flatItems.length === 0 && (
              <div className="flex items-center gap-2 p-4 text-sm text-muted-foreground" role="status" aria-live="polite">
                <Loader2 className="h-4 w-4 animate-spin text-primary" />
                Searching…
              </div>
            )}

            {hasError && (
              <div className="flex items-start gap-3 p-4 text-sm text-error" role="alert">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{search.error ?? "Something went wrong. Please try again."}</span>
              </div>
            )}

            {isEmpty && !isLoading && (
              <div className="flex items-start gap-3 p-4 text-sm text-muted-foreground">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>
                  No results for &ldquo;{search.query}&rdquo;. Try a ticker (AAPL), company name, or page (Leaderboard, News).
                </span>
              </div>
            )}

            {!isLoading && !hasError && search.groups.length > 0 && (
              <SearchResultsList
                groups={search.groups}
                query={search.query}
                indexByKey={indexByKey}
                activeIndex={activeIndex}
                onSelect={selectItem}
              />
            )}
          </div>

          {!isLoading && !hasError && search.total > 0 && (
            <div className="border-t border-border px-3 py-1.5 text-[10px] uppercase tracking-wider text-muted-foreground flex items-center justify-between">
              <span>{search.total} result{search.total === 1 ? "" : "s"}</span>
              <span>↑↓ navigate · ↵ open · esc close</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function SearchResultsList({
  groups,
  query,
  indexByKey,
  activeIndex,
  onSelect,
}: {
  groups: SearchGroup[];
  query: string;
  indexByKey: Map<string, number>;
  activeIndex: number;
  onSelect: (item: UnifiedSearchItem) => void;
}) {
  return (
    <div className="py-1" id="unified-search-listbox" role="listbox">
      {groups.map((group) => (
        <div key={group.label} className="mb-1 last:mb-0">
          <div className="px-4 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
            {group.label}
          </div>
          <ul aria-label={`${group.label} results`}>
            {group.items.map((item) => {
              const key =
                item.kind === "stock"
                  ? `stock-${item.symbol}`
                  : item.kind === "news"
                  ? `news-${item.id}`
                  : `page-${item.id}`;
              const idx = indexByKey.get(key) ?? -1;
              const active = idx === activeIndex;
              const content =
                item.kind === "stock" ? (
                  <StockResult item={item} query={query} active={active} />
                ) : item.kind === "news" ? (
                  <NewsResult item={item} query={query} active={active} />
                ) : (
                  <PageResult item={item} query={query} active={active} />
                );
              return (
                <li
                  key={key}
                  role="option"
                  aria-selected={active}
                  onClick={() => onSelect(item)}
                  className={cn(
                    "cursor-pointer transition-colors",
                    active ? "bg-primary/10" : "hover:bg-muted"
                  )}
                >
                  {content}
                </li>
              );
            })}
          </ul>
        </div>
      ))}
    </div>
  );
}

export default UnifiedSearchBar;
