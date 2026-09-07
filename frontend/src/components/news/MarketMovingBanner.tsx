"use client";

import { AlertTriangle, Zap } from "lucide-react";
import { cn } from "@/lib/cn";

interface MarketMovingBannerProps {
  count: number;
  onClick: () => void;
}

export function MarketMovingBanner({ count, onClick }: MarketMovingBannerProps) {
  if (count === 0) return null;

  return (
    <button
      onClick={onClick}
      className={cn(
        "w-full flex items-center gap-3 px-4 py-3 rounded-xl border border-red-200",
        "bg-gradient-to-r from-red-50 to-orange-50 hover:from-red-100 hover:to-orange-100",
        "transition-all duration-200 shadow-sm hover:shadow-md"
      )}
    >
      <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-red-100 text-red-600">
        <Zap className="h-4 w-4" />
      </div>
      <div className="flex-1 text-right">
        <p className="text-sm font-semibold text-red-900">
          {count} Market-Moving News {count === 1 ? "Item" : "Items"}
        </p>
        <p className="text-xs text-red-700">
          High-impact news detected in the last 15 minutes
        </p>
      </div>
      <AlertTriangle className="h-4 w-4 text-red-500 animate-pulse" />
    </button>
  );
}
