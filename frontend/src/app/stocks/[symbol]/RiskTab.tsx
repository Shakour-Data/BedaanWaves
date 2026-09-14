"use client";

import { TarotCard } from "@/components/ui/TarotCard";
import { t } from "@/lib/i18n";
import type { RiskData, FundamentalData } from "./types";

interface RiskTabProps {
  risk: RiskData | null;
  fundamental: FundamentalData | null;
}

function fmt(n: number, digits = 0): string {
  return n.toLocaleString("en-US", { maximumFractionDigits: digits });
}

export function RiskTab({ risk, fundamental }: RiskTabProps) {
  if (!risk || Object.keys(risk).length === 0) {
    return (
      <div className="space-y-4 animate-in fade-in duration-200">
        <div className="rounded-xl border border-dashed border-[var(--color-border)] bg-[var(--color-surface)]/30 py-12 text-center">
          <p className="text-sm text-[var(--color-text-secondary)]">
            Risk analysis data is not yet available for this stock.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4 animate-in fade-in duration-200">
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <TarotCard title="Risk Metrics">
          <div className="space-y-3">
            {Object.entries(risk).map(([key, value]) => (
              <div key={key} className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground capitalize">
                  {key.replace(/_/g, " ")}
                </span>
                <span className="font-semibold">
                  {typeof value === "number" ? fmt(value, 2) : String(value)}
                </span>
              </div>
            ))}
          </div>
        </TarotCard>
        {fundamental && Object.keys(fundamental).length > 0 && (
          <TarotCard title="Fundamentals">
            <div className="space-y-3">
              {Object.entries(fundamental).map(([key, value]) => (
                <div key={key} className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground capitalize">
                    {key.replace(/_/g, " ")}
                  </span>
                  <span className="font-semibold">
                    {typeof value === "number" ? fmt(value, 2) : String(value)}
                  </span>
                </div>
              ))}
            </div>
          </TarotCard>
        )}
      </div>
    </div>
  );
}
