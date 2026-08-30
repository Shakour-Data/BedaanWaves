"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { cn } from "@/lib/cn";
import { useStockSearch } from "@/hooks/useStockSearch";

export interface StockSearchBarProps {
  onSelect?: (stock: { symbol: string; name: string }) => void;
  placeholder?: string;
  className?: string;
  minQueryLength?: number;
}

interface HighlightedTextProps {
  text: string;
  query: string;
  className?: string;
}

function HighlightedText({ text, query, className }: HighlightedTextProps) {
  const q = query.trim().toLowerCase();
  if (!q) return <>{text}</>;

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

export function StockSearchBar({
  onSelect,
  placeholder = "Search stocks, tickers...",
  className,
  minQueryLength = 1,
}: StockSearchBarProps) {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLUListElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const { query, results, status, error, setQuery, clearResults } = useStockSearch(minQueryLength);

  const [isOpen, setIsOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);

  const isLoading = status === "loading";
  const isEmpty = status === "empty";
  const hasError = status === "error";
  const showDropdown = isOpen && (isLoading || results.length > 0 || isEmpty || hasError);

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
    if (activeIndex >= 0 && listRef.current) {
      const items = listRef.current.querySelectorAll("[role='option']");
      const active = items[activeIndex] as HTMLElement | undefined;
      active?.scrollIntoView({ block: "nearest" });
    }
  }, [activeIndex]);

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(e.target.value);
    setIsOpen(true);
  }, [setQuery]);

  const handleInputFocus = useCallback(() => {
    if (query.length >= minQueryLength) {
      setIsOpen(true);
    }
  }, [query, minQueryLength]);

  const handleClear = useCallback(() => {
    clearResults();
    inputRef.current?.focus();
  }, [clearResults]);

  const handleSelect = useCallback(
    (stock: { symbol: string; name: string }) => {
      setIsOpen(false);
      setActiveIndex(-1);
      inputRef.current?.blur();
      onSelect?.(stock);
      router.push(`/stocks/${stock.symbol}`);
    },
    [onSelect, router]
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
          setActiveIndex(-1);
          inputRef.current?.blur();
          break;
        }
      }
    },
    [isOpen, isLoading, results, activeIndex, handleSelect]
  );

  const listboxId = "stock-search-listbox";
  const inputId = "stock-search-input";

  return (
    <div ref={containerRef} className={cn("relative w-full", className)}>
      <div className="relative">
        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground text-xs">
          Search
        </span>
        <input
          ref={inputRef}
          id={inputId}
          type="text"
          role="combobox"
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
            "h-10 w-full rounded-lg border border-border bg-surface pl-16 pr-20 text-sm text-foreground placeholder:text-muted-foreground",
            "transition-colors duration-150",
            "focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20",
            showDropdown && "rounded-b-none border-b-0"
          )}
        />

        {query && (
          <button
            type="button"
            onClick={handleClear}
            className="absolute right-16 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground text-xs transition-colors"
            aria-label="Clear search"
          >
            Clear
          </button>
        )}

        <kbd className="absolute right-3 top-1/2 hidden -translate-y-1/2 rounded border border-border bg-border px-1.5 py-0.5 text-[10px] text-muted-foreground md:inline-block">
          ⌘K
        </kbd>
      </div>

      {showDropdown && (
        <div
          className={cn(
            "absolute z-50 w-full rounded-b-xl border border-t-0 border-border bg-surface shadow-lg overflow-hidden"
          )}
        >
          <ul
            ref={listRef}
            id={listboxId}
            role="listbox"
            aria-label="Stock search results"
            className="max-h-80 overflow-y-auto"
          >
            {isLoading && (
              <li
                role="status"
                aria-live="polite"
                className="flex items-center justify-center gap-2 p-4 text-sm text-muted-foreground"
              >
                <svg
                  className="h-4 w-4 animate-spin text-primary"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                Searching...
              </li>
            )}

            {hasError && (
              <li role="alert" className="p-4 text-sm text-error">
                {error ?? "Something went wrong. Please try again."}
              </li>
            )}

            {isEmpty && !isLoading && (
              <li className="p-4 text-sm text-muted-foreground">
                No stock matches your query for &ldquo;{query}&rdquo;
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
                        : "text-foreground hover:bg-border/50"
                    )}
                  >
                    <div
                      className={cn(
                        "flex h-10 w-10 shrink-0 items-center justify-center rounded-lg text-sm font-bold",
                        isActive
                          ? "bg-primary/20 text-primary"
                          : "bg-primary/10 text-primary"
                      )}
                    >
                      {stock.symbol.slice(0, 2)}
                    </div>

                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-sm text-foreground">
                          <HighlightedText text={stock.symbol} query={query} />
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
                      <p
                        className={cn(
                          "text-xs font-medium",
                          isPositive ? "text-success" : "text-error"
                        )}
                      >
                        {isPositive ? "+" : ""}
                        {changePct}%
                      </p>
                    </div>
                  </li>
                );
              })}
          </ul>
        </div>
      )}
    </div>
  );
}
