"use client";

import { useEffect, useMemo, useState, useCallback } from "react";
import { useStockSearch } from "@/hooks/useStockSearch";
import { cn } from "@/lib/cn";
import { Search, X, Loader2, AlertCircle } from "lucide-react";

interface StockPickerProps {
  onSelect: (stock: { symbol: string; name: string; id?: string }) => void;
  placeholder?: string;
  className?: string;
}

export function StockPicker({ onSelect, placeholder = "Search stocks...", className }: StockPickerProps) {
  const [query, setQuery] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const { results, status, error } = useStockSearch(1);

  const isLoading = status === "loading";
  const isEmpty = status === "empty";
  const hasError = status === "error";

  const showDropdown = isOpen && (isLoading || results.length > 0 || isEmpty || hasError);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (!e.target || !(e.target as HTMLElement).closest("[data-stock-picker]")) {
        setIsOpen(false);
        setActiveIndex(-1);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    if (activeIndex >= 0 && results.length > 0) {
      const el = document.getElementById(`stock-picker-option-${activeIndex}`);
      el?.scrollIntoView?.({ block: "nearest" });
    }
  }, [activeIndex]);

  const handleSelect = useCallback(
    (stock: { symbol: string; name: string }) => {
      onSelect(stock);
      setIsOpen(false);
      setActiveIndex(-1);
    },
    [onSelect]
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
          break;
        }
      }
    },
    [isOpen, isLoading, results, activeIndex, handleSelect]
  );

  return (
    <div data-stock-picker className={cn("relative w-full", className)}>
      <div className="relative">
        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" aria-hidden="true">
          <Search className="h-4 w-4" />
        </span>
        <input
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setIsOpen(true);
            setActiveIndex(-1);
          }}
          onFocus={() => setIsOpen(true)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className="h-10 w-full rounded-lg border border-border bg-surface pl-10 pr-10 text-sm text-foreground placeholder:text-muted-foreground transition-colors duration-150 focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
        />
        {query && !isLoading && (
          <button
            type="button"
            onClick={() => {
              setQuery("");
              setIsOpen(false);
              setActiveIndex(-1);
            }}
            className="absolute right-3 top-1/2 -translate-y-1/2 rounded p-1 text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
            aria-label="Clear search"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      {showDropdown && (
        <div className="absolute z-50 w-full rounded-b-xl border border-t-0 border-border bg-surface shadow-lg overflow-hidden">
          <ul className="max-h-80 overflow-y-auto" role="listbox">
            {isLoading && (
              <li role="status" aria-live="polite" className="flex items-center justify-center gap-2 p-4 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin text-primary" />
                Searching...
              </li>
            )}

            {hasError && (
              <li role="alert" className="flex items-start gap-3 p-4 text-sm text-error">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{error ?? "Something went wrong. Please try again."}</span>
              </li>
            )}

            {isEmpty && !isLoading && (
              <li className="flex items-start gap-3 p-4 text-sm text-muted-foreground">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>
                  No stock matches your query for &ldquo;{query}&rdquo;. Try a ticker symbol or company name.
                </span>
              </li>
            )}

            {!isLoading &&
              results.map((stock, index) => {
                const isActive = index === activeIndex;
                return (
                  <li
                    key={stock.symbol}
                    id={`stock-picker-option-${index}`}
                    role="option"
                    aria-selected={isActive}
                    onClick={() => handleSelect({ symbol: stock.symbol, name: stock.name })}
                    onMouseEnter={() => setActiveIndex(index)}
                    className={cn(
                      "flex cursor-pointer items-center gap-3 px-4 py-3 transition-colors",
                      isActive ? "bg-primary/10 text-foreground" : "text-foreground hover:bg-muted"
                    )}
                  >
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-sm text-foreground">{stock.symbol}</span>
                      </div>
                      <p className="truncate text-xs text-muted-foreground">{stock.name}</p>
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
