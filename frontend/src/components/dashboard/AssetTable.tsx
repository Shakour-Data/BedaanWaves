import Link from "next/link";
import type { AssetRow } from "@/lib/dashboard-data";
import { ChangeBadge } from "./StatCard";

const MARKET_LABEL: Record<string, string> = {
  TSE: "بورس",
  OTC: "فرابورس",
  BINANCE: "کریپتو",
};

export function AssetTable({ rows }: { rows: AssetRow[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="border-b border-[var(--color-border)] text-muted-foreground">
            <th className="px-2 py-2 text-right font-medium">نماد</th>
            <th className="px-2 py-2 text-right font-medium">نام</th>
            <th className="px-2 py-2 text-center font-medium">بازار</th>
            <th className="px-2 py-2 text-left font-medium">قیمت</th>
            <th className="px-2 py-2 text-left font-medium">تغییر</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr
              key={r.symbol}
              className="border-b border-[var(--color-border)]/60 transition duration-150 ease-flow hover:bg-black/5"
            >
              <td className="px-2 py-2 font-semibold">
                <Link
                  href={`/stocks/${encodeURIComponent(r.symbol)}`}
                  className="text-primary hover:underline"
                >
                  {r.symbol}
                </Link>
              </td>
              <td className="px-2 py-2 text-muted-foreground">{r.name}</td>
              <td className="px-2 py-2 text-center">
                <span className="rounded-full bg-[var(--color-muted-foreground)]/20 px-2 py-0.5 text-xs">
                  {MARKET_LABEL[r.market] ?? r.market}
                </span>
              </td>
              <td className="px-2 py-2 text-left">{r.price.toLocaleString("fa-IR")}</td>
              <td className="px-2 py-2 text-left">
                <ChangeBadge value={r.changePct} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
