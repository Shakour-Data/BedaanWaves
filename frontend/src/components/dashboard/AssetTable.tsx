import Link from "next/link";
import type { AssetRow } from "@/lib/dashboard-data";
import { ChangeBadge } from "./StatCard";
import { Badge } from "@/components/ui/Badge";

const MARKET_LABEL: Record<string, string> = {
  NASDAQ: "NASDAQ" };

export function AssetTable({ rows }: { rows: AssetRow[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="border-b border-border text-muted-foreground">
            <th className="px-4 py-3 text-right font-medium">Symbol</th>
            <th className="px-4 py-3 text-right font-medium">Name</th>
            <th className="px-4 py-3 text-center font-medium">Market</th>
            <th className="px-4 py-3 text-right font-medium">Price</th>
            <th className="px-4 py-3 text-right font-medium">Change</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {rows.map((r) => (
            <tr
              key={r.symbol}
              className="transition-colors duration-150 hover:bg-neutral/50"
            >
              <td className="px-4 py-3 font-semibold">
                <Link
                  href={`/stocks/${encodeURIComponent(r.symbol)}`}
                  className="text-primary hover:underline"
                >
                  {r.symbol}
                </Link>
              </td>
              <td className="px-4 py-3 text-muted-foreground">{r.name}</td>
              <td className="px-4 py-3 text-center">
                <Badge variant="neutral" size="sm">
                  {MARKET_LABEL[r.market] ?? r.market}
                </Badge>
              </td>
              <td className="px-4 py-3 text-right">{r.price.toLocaleString("fa-IR")}</td>
              <td className="px-4 py-3 text-right">
                <ChangeBadge value={r.changePct} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
