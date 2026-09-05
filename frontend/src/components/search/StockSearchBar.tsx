"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { cn } from "@/lib/cn";
import { useStockSearch } from "@/hooks/useStockSearch";
import {
  Search,
  X,
  Loader2,
  Command,
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
  Clock,
  AlertCircle,
} from "lucide-react";

export interface StockSearchBarProps {
  onSelect?: (stock: { symbol: string; name: string }) => void;
  onRecent?: (query: string) => void;
  placeholder?: string;
  className?: string;
  minQueryLength?: number;
  recentSearches?: string[];
}

interface HighlightedTextProps {
  text: string;
  query: string;
  className?: string;
}

function HighlightedText({ text, query, className }: HighlightedTextProps) {
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
      <mark className={cn("rounded bg-primary/20 px-0.5 text-primary", className)}>
        {match}
      </mark>
      {after}
    </>
  );
}

function SectorIcon({ sector }: { sector: string }) {
  const s = sector.toLowerCase();
  if (s.includes("technology") || s.includes("software") || s.includes("semiconductor")) {
    return <Zap className="h-4 w-4 text-primary" />;
  }
  if (s.includes("financial") || s.includes("bank") || s.includes("insurance")) {
    return <Banknote className="h-4 w-4 text-secondary" />;
  }
  if (s.includes("health") || s.includes("pharma") || s.includes("biotech")) {
    return <Stethoscope className="h-4 w-4 text-error" />;
  }
  if (s.includes("consumer") || s.includes("retail") || s.includes("cyclical")) {
    return <ShoppingBasket className="h-4 w-4 text-warning" />;
  }
  if (s.includes("industrial") || s.includes("manufact") || s.includes("machinery")) {
    return <Factory className="h-4 w-4 text-accent" />;
  }
  if (s.includes("real estate") || s.includes("reit") || s.includes("property")) {
    return <Landmark className="h-4 w-4 text-success" />;
  }
  if (s.includes("utilities") || s.includes("utility")) {
    return <Plug className="h-4 w-4 text-secondary" />;
  }
  if (s.includes("communication") || s.includes("media") || s.includes("entertain")) {
    return <Globe className="h-4 w-4 text-accent" />;
  }
  return <Building2 className="h-4 w-4 text-muted-foreground" />;
}

function MarketTrendIcon({ change }: { change: number }) {
  if (change > 0) {
    return <TrendingUp className="h-3 w-3 text-success" />;
  }
  if (change < 0) {
    return <TrendingDown className="h-3 w-3 text-error" />;
  }
  return <TrendingUp className="h-3 w-3 text-muted-foreground" />;
}

export function StockSearchBar({
  onSelect,
  onRecent,
  placeholder = "Search stocks, tickers...",
  className,
  minQueryLength = 1,
  recentSearches = [],
}: StockSearchBarProps) {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLUListElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const { query, results, status, error, setQuery, clearResults } = useStockSearch(minQueryLength);

  const [isOpen, setIsOpen] = useState(false);
  const [isFocused, setIsFocused] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);

  const isLoading = status === "loading";
  const isEmpty = status === "empty";
  const hasError = status === "error";

  const showQuickPicks = isFocused && query.trim() === "" && !isLoading && !hasError;
  const showDropdown =
    isOpen &&
    (isLoading || results.length > 0 || isEmpty || hasError || showQuickPicks);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
        setIsFocused(false);
        setActiveIndex(-1);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    if (activeIndex >= 0 && listRef.current) {
      const items = listRef.current.querySelectorAll("[role='option'], [role='button']");
      const active = items[activeIndex] as HTMLElement | undefined;
      active?.scrollIntoView?.({ block: "nearest" });
    }
  }, [activeIndex]);

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setQuery(e.target.value);
      setIsOpen(true);
      setIsFocused(true);
    },
    [setQuery]
  );

  const handleInputFocus = useCallback(() => {
    setIsFocused(true);
    setIsOpen(true);
  }, []);

  const handleClear = useCallback(() => {
    clearResults();
    inputRef.current?.focus();
  }, [clearResults]);

  const recordRecent = useCallback(
    (query: string) => {
      onRecent?.(query.trim());
    },
    [onRecent]
  );

  const handleSelect = useCallback(
    (stock: { symbol: string; name: string }) => {
      recordRecent(stock.symbol);
      setIsOpen(false);
      setIsFocused(false);
      setActiveIndex(-1);
      inputRef.current?.blur();
      onSelect?.(stock);
      router.push(`/stocks/${stock.symbol}`);
    },
    [onSelect, router, recordRecent]
  );

  const handleQuickPick = useCallback(
    (value: string) => {
      recordRecent(value);
      setQuery(value);
      setIsOpen(true);
      setIsFocused(true);
      setActiveIndex(0);
      inputRef.current?.focus();
    },
    [setQuery, recordRecent]
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (!isOpen) {
        if (e.key === "ArrowDown" || e.key === "Enter") {
          setIsOpen(true);
          e.preventDefault();
        }
        return;
      }

      if (showQuickPicks) {
        const totalItems = recentSearches.length;
        switch (e.key) {
          case "ArrowDown": {
            e.preventDefault();
            setActiveIndex((prev) => (prev + 1) % totalItems);
            break;
          }
          case "ArrowUp": {
            e.preventDefault();
            setActiveIndex((prev) => (prev - 1 + totalItems) % totalItems);
            break;
          }
          case "Enter": {
            e.preventDefault();
            if (activeIndex >= 0 && activeIndex < recentSearches.length) {
              handleQuickPick(recentSearches[activeIndex]);
            }
            break;
          }
          case "Escape": {
            e.preventDefault();
            setIsOpen(false);
            setIsFocused(false);
            setActiveIndex(-1);
            inputRef.current?.blur();
            break;
          }
        }
        return;
      }

      const totalItems = isLoading ? 1 : results.length;

      switch (e.key) {
        case "ArrowDown": {
          e.preventDefault();
          setActiveIndex((prev) => (prev + 1) % totalItems);
          break;
        }
        case "ArrowUp": {
          e.preventDefault();
          setActiveIndex((prev) => (prev - 1 + totalItems) % totalItems);
          break;
        }
        case "Enter": {
          e.preventDefault();
          if (isLoading) break;

          if (activeIndex >= 0 && activeIndex < results.length) {
            handleSelect(results[activeIndex]);
          } else if (results.length > 0 && activeIndex === -1) {
            handleSelect(results[0]);
          }
          break;
        }
        case "Escape": {
          e.preventDefault();
          setIsOpen(false);
          setIsFocused(false);
          setActiveIndex(-1);
          inputRef.current?.blur();
          break;
        }
      }
    },
    [isOpen, isLoading, results, activeIndex, showQuickPicks, recentSearches, handleSelect, handleQuickPick]
  );

  const listboxId = "stock-search-listbox";
  const inputId = "stock-search-input";

  return (
    <div ref={containerRef} className={cn("relative w-full", className)}>
      <div className="relative">
        <span
          className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground"
          aria-hidden="true"
        >
          <Search className="h-4 w-4" />
        </span>

        <input
          ref={inputRef}
          id={inputId}
          type="text"
          role="combobox"
          autoComplete="off"
          autoCapitalize="none"
          spellCheck={false}
          aria-autocomplete="list"
          aria-controls={listboxId}
          aria-expanded={showDropdown}
          aria-activedescendant={
            activeIndex >= 0 && activeIndex < results.length
              ? `stock-option-${activeIndex}`
              : undefined
          }
          placeholder={placeholder}
          value={query}
          onChange={handleInputChange}
          onFocus={handleInputFocus}
          onKeyDown={handleKeyDown}
          className={cn(
            "h-10 w-full rounded-lg border border-border bg-surface pl-10 pr-12 text-sm text-foreground placeholder:text-muted-foreground",
            "transition-colors duration-150",
            "focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20",
            showDropdown && "rounded-b-none border-b-0"
          )}
        />

        {query && !isLoading && (
          <button
            type="button"
            onClick={handleClear}
            className="absolute right-3 top-1/2 -translate-y-1/2 rounded p-1 text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
            aria-label="Clear search"
          >
            <X className="h-4 w-4" />
          </button>
        )}

        {!query && !isLoading && (
          <kbd
            className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 inline-flex items-center gap-0.5 rounded border border-border bg-border px-1.5 py-0.5 text-[10px] text-muted-foreground md:pointer-events-auto md:inline-flex"
            aria-hidden="true"
          >
            <Command className="h-3 w-3" />
            <span>K</span>
          </kbd>
        )}
      </div>

      {showDropdown && (
        <div className="absolute z-50 w-full rounded-b-xl border border-t-0 border-border bg-surface shadow-lg overflow-hidden">
          <ul
            ref={listRef}
            id={listboxId}
            role="listbox"
            aria-label="Stock search results"
            className="max-h-80 overflow-y-auto"
          >
            {showQuickPicks && (
              <li className="border-b border-border px-3 py-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Quick picks
              </li>
            )}

            {showQuickPicks &&
              recentSearches.map((ticker, index) => {
                const isActive = index === activeIndex;
                return (
                  <li
                    key={ticker}
                    id={`quickpick-option-${index}`}
                    role="option"
                    aria-selected={isActive}
                    onClick={() => handleQuickPick(ticker)}
                    onMouseEnter={() => setActiveIndex(index)}
                    className={cn(
                      "flex cursor-pointer items-center gap-3 px-4 py-2.5 transition-colors",
                      isActive
                        ? "bg-primary/10 text-foreground"
                        : "text-foreground hover:bg-muted"
                    )}
                  >
                    <Clock className="h-4 w-4 text-muted-foreground" />
                    <span className="font-mono text-sm">{ticker}</span>
                  </li>
                );
              })}

            {isLoading && (
              <li
                role="status"
                aria-live="polite"
                className="flex items-center justify-center gap-2 p-4 text-sm text-muted-foreground"
              >
                <Loader2 className="h-4 w-4 animate-spin text-primary" />
                Searching...
              </li>
            )}

            {hasError && (
              <li
                role="alert"
                className="flex items-start gap-3 p-4 text-sm text-error"
              >
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{error ?? "Something went wrong. Please try again."}</span>
              </li>
            )}

            {isEmpty && !isLoading && !showQuickPicks && (
              <li className="flex items-start gap-3 p-4 text-sm text-muted-foreground">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>
                  No stock matches your query for &ldquo;{query}&rdquo;. Try a ticker
                  symbol or company name (e.g. AAPL, Apple).
                </span>
              </li>
            )}

            {!isLoading &&
              results.map((stock, index) => {
                const isActive = index === activeIndex;
                const isPositive = stock.change >= 0;
                const changePct =
                  stock.price > 0 ? ((stock.change / stock.price) * 100).toFixed(2) : "0.00";

                return (
                  <li
                    key={stock.symbol}
                    id={`stock-option-${index}`}
                    role="option"
                    aria-selected={isActive}
                    onClick={() => handleSelect(stock)}
                    onMouseEnter={() => setActiveIndex(index)}
                    className={cn(
                      "flex cursor-pointer items-center gap-3 px-4 py-3 transition-colors",
                      isActive
                        ? "bg-primary/10 text-foreground"
                        : "text-foreground hover:bg-muted"
                    )}
                  >
                    <div
                      className={cn(
                        "flex h-10 w-10 shrink-0 items-center justify-center rounded-lg text-xs font-bold",
                        isActive
                          ? "bg-primary/20 text-primary"
                          : "bg-primary/10 text-primary"
                      )}
                    >
                      <SectorIcon sector={stock.sector} />
                    </div>

                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-sm text-foreground">
                          <HighlightedText text={stock.symbol} query={query} />
                        </span>
                        <span
                          className={cn(
                            "inline-flex items-center gap-0.5 text-xs font-medium",
                            isPositive ? "text-success" : "text-error"
                          )}
                        >
                          <MarketTrendIcon change={stock.change} />
                          {isPositive ? "+" : ""}
                          {changePct}%
                        </span>
                      </div>
                      <p className="truncate text-xs text-muted-foreground">
                        <HighlightedText text={stock.name} query={query} />
                      </p>
                      <p className="text-[10px] text-muted-foreground">{stock.sector}</p>
                    </div>

                    <div className="shrink-0 text-right">
                      <p className="text-sm font-semibold text-foreground">
                        ${stock.price.toFixed(2)}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {changePct}%
                      </p>
                    </div>
                  </li>
                );
              })}

            {!isLoading && results.length > 0 && (
              <li className="border-t border-border px-3 py-1.5 text-xs text-muted-foreground">
                Displaying {results.length} result{results.length === 1 ? "" : "s"}
              </li>
            )}
          </ul>
        </div>
      )}
    </div>
  );
}

export default StockSearchBar;
