import type { AssetRow } from "@/lib/dashboard-data";
import { ChangeBadge } from "./StatCard";

const MARKET_LABEL: Record<AssetRow["market"], string> = {
  TSE: "بورس",
  OTC: "فرابورس",
  BINANCE: "کریپتو",
};

export function AssetTable({ rows }: { rows: AssetRow[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="border-b border-border text-muted-foreground">
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
              className="border-b border-border/60 transition duration-fast ease-flow hover:bg-black/5"
            >
              <td className="px-2 py-2 font-semibold">{r.symbol}</td>
              <td className="px-2 py-2 text-muted-foreground">{r.name}</td>
              <td className="px-2 py-2 text-center">
                <span className="rounded-full bg-neutral/70 px-2 py-0.5 text-xs">
                  {MARKET_LABEL[r.market]}
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
