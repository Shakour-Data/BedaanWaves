"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { cn } from "@/lib/cn";
import { NewDashboardShell } from "@/components/layout/NewDashboardShell";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { t } from "@/lib/i18n";
import { useAuthStore } from "@/store/useAuthStore";
import { getApiErrorMessage } from "@/lib/api";
import {
  fetchNasdaqRankings,
  type Grade,
  type NasdaqRanking,
  type RankingSortField,
  type SortOrder
} from "@/lib/api/ranking";

const PAGE_SIZE = 20;

const GRADE_STYLES: Record<Grade, "success" | "warning" | "error" | "default"> = {
  A_STRONG_BUY: "success",
  B_BUY: "success",
  C_HOLD: "warning",
  D_SELL: "error",
  E_STRONG_SELL: "error",
};

function scoreBarVariant(score: number): "success" | "warning" | "error" {
  if (score >= 70) return "success";
  if (score >= 40) return "warning";
  return "error";
}

function ScoreBar({ score }: { score: number }) {
  const variant = scoreBarVariant(score);
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-16 overflow-hidden rounded-full bg-border">
        <div className={cn("h-full rounded-full", variant === "success" ? "bg-success" : variant === "warning" ? "bg-warning" : "bg-error")} style={{ width: `${Math.max(0, Math.min(100, score))}%` }} />
      </div>
      <span className={cn("w-8 text-right text-sm font-semibold", variant === "success" ? "text-success" : variant === "warning" ? "text-warning" : "text-error")}>{score}</span>
    </div>
  );
}

function GradeBadge({ grade }: { grade: Grade }) {
  const label = t(`app.ranking.grades.${grade}`, "en");
  return (
    <Badge variant={GRADE_STYLES[grade]} size="md">{label}</Badge>
  );
}

function RankCell({ rank }: { rank: number }) {
  const classes =
    rank === 1
      ? "bg-warning text-white"
      : rank === 2
        ? "bg-secondary text-white"
        : rank === 3
          ? "bg-warning/80 text-white"
          : "bg-border text-muted-foreground";
  return (
    <div className={cn("flex h-7 w-7 items-center justify-center rounded-lg text-sm font-bold", classes)}>
      {rank}
    </div>
  );
}

export default function RankingPage() {
  const currentLang = useAuthStore((state) => state.currentLang) ?? "en";

  const [items, setItems] = useState<NasdaqRanking[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [offset, setOffset] = useState(0);
  const [sortBy, setSortBy] = useState<RankingSortField>("overall_score");
  const [order, setOrder] = useState<SortOrder>("desc");

  const load = useCallback(() => {
    let active = true;
    setLoading(true);
    setError(null);
    fetchNasdaqRankings({ limit: PAGE_SIZE, offset, sort_by: sortBy, order })
      .then((res) => {
        if (!active) return;
        setItems(res.items);
        setTotal(res.total);
      })
      .catch((err: unknown) => {
        if (!active) return;
        const message = getApiErrorMessage(err);
        setError(message || t("app.ranking.error_desc", currentLang));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [offset, sortBy, order, currentLang]);

  useEffect(() => load(), [load]);

  const totalPages = useMemo(() => Math.max(1, Math.ceil(total / PAGE_SIZE)), [total]);
  const currentPage = useMemo(() => Math.floor(offset / PAGE_SIZE) + 1, [offset]);
  const from = total === 0 ? 0 : offset + 1;
  const to = Math.min(offset + items.length, total);

  function toggleSort(field: RankingSortField) {
    if (field === sortBy) {
      setOrder((prev) => (prev === "desc" ? "asc" : "desc"));
    } else {
      setSortBy(field);
      setOrder("desc");
    }
    setOffset(0);
  }

  function sortIndicator(field: RankingSortField): string {
    if (field !== sortBy) return "";
    return order === "desc" ? " ↓" : " ↑";
  }

  const headerCellClass =
    "cursor-pointer select-none whitespace-nowrap px-3 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground hover:text-foreground";

  return (
    <NewDashboardShell title={t("app.ranking.title", currentLang)}>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-foreground">{t("app.ranking.title", currentLang)}</h1>
          <p className="text-muted-foreground">{t("app.ranking.subtitle", currentLang)}</p>
        </div>

        {loading ? (
          <div className="flex justify-center py-12">
            <Spinner size="lg" />
          </div>
        ) : error ? (
          <ErrorMessage
            message={t("app.ranking.error_title", currentLang)}
            actions={[{ label: t("app.ranking.retry", currentLang), onAction: () => load() }]}
          />
        ) : (
          <Card>
            <div className="mb-4 flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                {t("app.ranking.showing", currentLang)
                  .replace("{from}", String(from))
                  .replace("{to}", String(to))
                  .replace("{total}", String(total))}
              </p>
              <p className="text-sm text-muted-foreground">
                {t("app.ranking.page", currentLang)
                  .replace("{page}", String(currentPage))
                  .replace("{pages}", String(totalPages))}
              </p>
            </div>

            {items.length === 0 ? (
              <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border bg-surface/30 py-16">
                <h3 className="mt-2 text-lg font-medium text-foreground">{t("app.ranking.no_results", currentLang)}</h3>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full border-collapse text-sm">
                  <thead>
                    <tr className="border-b border-border">
                      <th className={cn(headerCellClass, "w-12 text-center")} onClick={() => toggleSort("overall_score")}>
                        {t("app.ranking.rank", currentLang)}
                      </th>
                      <th className={cn(headerCellClass, "min-w-[80px]")}>{t("app.ranking.symbol", currentLang)}</th>
                      <th className={cn(headerCellClass, "min-w-[160px]")}>{t("app.ranking.name", currentLang)}</th>
                      <th className={headerCellClass} onClick={() => toggleSort("overall_score")}>
                        {t("app.ranking.overall_score", currentLang)}
                        {sortIndicator("overall_score")}
                      </th>
                      <th className={cn(headerCellClass, "min-w-[110px]")}>{t("app.ranking.grade", currentLang)}</th>
                      {["fundamental", "technical", "sentiment", "risk", "macro", "ai"].map((dim) => (
                        <th key={dim} className={headerCellClass} onClick={() => toggleSort(dim as RankingSortField)}>
                          {t(`app.ranking.${dim}`, currentLang)}
                          {sortIndicator(dim as RankingSortField)}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {items.map((row, idx) => (
                      <tr key={row.symbol} className="transition-colors hover:bg-neutral/50">
                        <td className="px-3 py-3 text-center">
                          <RankCell rank={row.rank || offset + idx + 1} />
                        </td>
                        <td className="px-3 py-3">
                          <Link
                            href={`/stocks/${row.symbol}`}
                            className="font-semibold text-primary hover:underline"
                          >
                            {row.symbol}
                          </Link>
                        </td>
                        <td className="max-w-[220px] truncate px-3 py-3 text-muted-foreground" title={row.name}>
                          {row.name}
                        </td>
                        <td className="px-3 py-3">
                          <ScoreBar score={row.overall_score} />
                        </td>
                        <td className="px-3 py-3">
                          <GradeBadge grade={row.grade} />
                        </td>
                        {(["fundamental", "technical", "sentiment", "risk", "macro", "ai"] as RankingSortField[]).map((dim) => (
                          <td key={dim} className="px-3 py-3">
                            <ScoreBar score={row[dim] as number} />
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            <div className="mt-4 flex items-center justify-between">
              <Button
                size="sm"
                variant="outline"
                disabled={currentPage <= 1}
                onClick={() => setOffset((prev) => Math.max(0, prev - PAGE_SIZE))}
              >
                {t("app.ranking.previous", currentLang)}
              </Button>
              <Button
                size="sm"
                variant="outline"
                disabled={currentPage >= totalPages}
                onClick={() => setOffset((prev) => Math.min((totalPages - 1) * PAGE_SIZE, prev + PAGE_SIZE))}
              >
                {t("app.ranking.next", currentLang)}
              </Button>
            </div>
          </Card>
        )}
      </div>
    </NewDashboardShell>
  );
}
