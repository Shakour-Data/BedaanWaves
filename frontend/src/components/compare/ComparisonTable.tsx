import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

interface ComparisonTableProps {
  stocks: Array<{
    symbol: string;
    name: string;
    overallScore: number;
    grade: string;
    dimensions: {
      fundamental: number;
      technical: number;
      sentiment: number;
      risk: number;
      macro: number;
      ai: number;
    };
  }>;
  className?: string;
}

const DIMENSIONS = [
  { key: "fundamental", label: "Fundamental" },
  { key: "technical", label: "Technical" },
  { key: "sentiment", label: "Sentiment" },
  { key: "risk", label: "Risk" },
  { key: "macro", label: "Macro" },
  { key: "ai", label: "AI" },
] as const;

export function ComparisonTable({ stocks, className }: ComparisonTableProps) {
  if (!stocks.length) {
    return (
      <div className={cn("text-center text-muted-foreground py-8", className)}>
        No comparison data available.
      </div>
    );
  }

  return (
    <div className={cn("overflow-x-auto", className)}>
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border">
            <th className="text-left py-2 px-3 font-semibold text-muted-foreground">Metric</th>
            {stocks.map((stock) => (
              <th key={stock.symbol} className="text-right py-2 px-3 font-semibold text-foreground">
                {stock.symbol}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          <tr>
            <td className="py-2 px-3 text-muted-foreground">Overall Score</td>
            {stocks.map((stock) => (
              <td key={stock.symbol} className="text-right py-2 px-3 font-semibold text-foreground">
                {stock.overallScore}
              </td>
            ))}
          </tr>
          <tr>
            <td className="py-2 px-3 text-muted-foreground">Grade</td>
            {stocks.map((stock) => (
              <td key={stock.symbol} className="text-right py-2 px-3">
                <span className="inline-flex items-center rounded-full bg-success/10 px-2 py-0.5 text-xs font-medium text-success">
                  {stock.grade}
                </span>
              </td>
            ))}
          </tr>
          {DIMENSIONS.map((dim) => (
            <tr key={dim.key}>
              <td className="py-2 px-3 text-muted-foreground">{dim.label}</td>
              {stocks.map((stock) => (
                <td key={stock.symbol} className="text-right py-2 px-3 text-foreground">
                  {stock.dimensions[dim.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
