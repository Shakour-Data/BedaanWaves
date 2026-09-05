"use client";

import { cn } from "@/lib/cn";
import type { AssetRow } from "@/lib/dashboard-data";

interface AssetTableProps {
  rows: AssetRow[];
  className?: string;
}

export function AssetTable({ rows, className }: AssetTableProps) {
  return (
    <div className={cn("overflow-x-auto rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-sm", className)}>
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-[var(--color-border)]">
            <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-[var(--color-text-secondary)]">Symbol</th>
            <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-[var(--color-text-secondary)]">Name</th>
            <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-[var(--color-text-secondary)]">Market</th>
            <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-[var(--color-text-secondary)]">Price</th>
            <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-[var(--color-text-secondary)]">Change</th>
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? null : rows.map((row) => (
            <tr key={row.symbol} className="border-b border-[var(--color-border)] last:border-0 hover:bg-[var(--color-background)]">
              <td className="px-4 py-3 font-medium text-[var(--color-text-primary)]">{row.symbol}</td>
              <td className="px-4 py-3 text-[var(--color-text-secondary)]">{row.name}</td>
              <td className="px-4 py-3 text-[var(--color-text-secondary)]">{row.market}</td>
              <td className="px-4 py-3 text-right tabular-nums text-[var(--color-text-primary)]">
                {row.price > 0 ? `$${row.price.toFixed(2)}` : "—"}
              </td>
              <td className={cn("px-4 py-3 text-right tabular-nums font-medium", row.changePct >= 0 ? "text-[var(--color-success)]" : "text-[var(--color-error)]")}>
                {row.changePct !== 0 ? `${row.changePct >= 0 ? "+" : ""}${row.changePct.toFixed(2)}%` : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
