"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { cn } from "@/lib/cn";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { TarotCard } from "@/components/ui/TarotCard";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { PageLoading } from "@/components/ui/PageLoading";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { t } from "@/lib/i18n";
import { useAuthStore } from "@/store/useAuthStore";
import {
  fetchNasdaqRankings,
  type Grade,
  type NasdaqRanking,
  type RankingSortField,
  type SortOrder
} from "@/lib/api/ranking";

const PAGE_SIZE = 20;

const DIMENSIONS: { key: RankingSortField; labelKey: string }[] = [
  { key: "fundamental", labelKey: "app.ranking.fundamental" },
  { key: "technical", labelKey: "app.ranking.technical" },
  { key: "sentiment", labelKey: "app.ranking.sentiment" },
  { key: "risk", labelKey: "app.ranking.risk" },
  { key: "macro", labelKey: "app.ranking.macro" },
  { key: "ai", labelKey: "app.ranking.ai" }
];

const GRADE_STYLES: Record<Grade, string> = {
  A_STRONG_BUY: "bg-emerald-600/15 text-emerald-500 border border-emerald-600/30",
  B_BUY: "bg-lime-600/15 text-lime-500 border border-lime-600/30",
  C_HOLD: "bg-amber-500/15 text-amber-400 border border-amber-500/30",
  D_SELL: "bg-orange-600/15 text-orange-500 border border-orange-600/30",
  E_STRONG_SELL: "bg-red-600/15 text-red-500 border border-red-600/30"
};

function scoreBarClass(score: number): string {
  if (score >= 70) return "bg-emerald-600";
  if (score >= 55) return "bg-lime-500";
  if (score >= 40) return "bg-amber-500";
  return "bg-red-600";
}

function scoreTextClass(score: number): string {
  if (score >= 70) return "text-emerald-500";
  if (score >= 55) return "text-lime-500";
  if (score >= 40) return "text-amber-400";
  return "text-red-500";
}

function ScoreBar({ score }: { score: number }) {
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-16 overflow-hidden rounded-full bg-[var(--color-border)]">
        <div className={cn("h-full rounded-full", scoreBarClass(score))} style={{ width: `${Math.max(0, Math.min(100, score))}%` }} />
      </div>
      <span className={cn("w-8 text-right text-sm font-semibold", scoreTextClass(score))}>{score}</span>
    </div>
  );
}

function GradeBadge({ grade }: { grade: Grade }) {
  const label = t(`app.ranking.grades.${grade}`, "en");
  return (
    <span className={cn("inline-block rounded-full px-2.5 py-0.5 text-xs font-bold", GRADE_STYLES[grade])}>
      {label}
    </span>
  );
}

function RankCell({ rank }: { rank: number }) {
  const classes =
    rank === 1
      ? "bg-[var(--color-warning)] text-white"
      : rank === 2
        ? "bg-gray-400 text-white"
        : rank === 3
          ? "bg-amber-700 text-white"
          : "bg-[var(--color-border)] text-[var(--color-text-secondary)]";
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
        const message = err instanceof Error ? err.message : String(err);
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
    "cursor-pointer select-none whitespace-nowrap px-3 py-3 text-left text-xs font-semibold uppercase tracking-wide text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]";

  return (
    <DashboardShell title={t("app.ranking.title", currentLang)}>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">{t("app.ranking.title", currentLang)}</h1>
          <p className="text-[var(--color-text-secondary)]">{t("app.ranking.subtitle", currentLang)}</p>
        </div>

        {loading ? (
          <PageLoading />
        ) : error ? (
          <ErrorMessage
            message={t("app.ranking.error_title", currentLang)}
            actions={[{ label: t("app.ranking.retry", currentLang), onAction: () => load() }]}
          />
        ) : (
          <TarotCard>
            <div className="mb-4 flex items-center justify-between">
              <p className="text-sm text-[var(--color-text-secondary)]">
                {t("app.ranking.showing", currentLang)
                  .replace("{from}", String(from))
                  .replace("{to}", String(to))
                  .replace("{total}", String(total))}
              </p>
              <p className="text-sm text-[var(--color-text-secondary)]">
                {t("app.ranking.page", currentLang)
                  .replace("{page}", String(currentPage))
                  .replace("{pages}", String(totalPages))}
              </p>
            </div>

            {items.length === 0 ? (
              <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-[var(--color-border)] bg-[var(--color-surface)]/30 py-16">
                <h3 className="mt-2 text-lg font-medium text-[var(--color-text-primary)]">{t("app.ranking.no_results", currentLang)}</h3>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full border-collapse text-sm">
                  <thead>
                    <tr className="border-b border-[var(--color-border)]">
                      <th
                        className={cn(headerCellClass, "w-12 text-center")}
                        onClick={() => toggleSort("overall_score")}
                      >
                        {t("app.ranking.rank", currentLang)}
                      </th>
                      <th className={cn(headerCellClass, "min-w-[80px]")}>{t("app.ranking.symbol", currentLang)}</th>
                      <th className={cn(headerCellClass, "min-w-[160px]")}>{t("app.ranking.name", currentLang)}</th>
                      <th
                        className={headerCellClass}
                        onClick={() => toggleSort("overall_score")}
                      >
                        {t("app.ranking.overall_score", currentLang)}
                        {sortIndicator("overall_score")}
                      </th>
                      <th className={cn(headerCellClass, "min-w-[110px]")}>{t("app.ranking.grade", currentLang)}</th>
                      {DIMENSIONS.map((dim) => (
                        <th
                          key={dim.key}
                          className={headerCellClass}
                          onClick={() => toggleSort(dim.key)}
                        >
                          {t(dim.labelKey, currentLang)}
                          {sortIndicator(dim.key)}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {items.map((row, idx) => (
                      <tr
                        key={row.symbol}
                        className="border-b border-[var(--color-border)] transition-colors hover:bg-[var(--color-surface)]/50"
                      >
                        <td className="px-3 py-3 text-center">
                          <RankCell rank={row.rank || offset + idx + 1} />
                        </td>
                        <td className="px-3 py-3">
                          <Link
                            href={`/stocks/${row.symbol}`}
                            className="font-semibold text-[var(--color-primary)] hover:underline"
                          >
                            {row.symbol}
                          </Link>
                        </td>
                        <td className="max-w-[220px] truncate px-3 py-3 text-[var(--color-text-secondary)]" title={row.name}>
                          {row.name}
                        </td>
                        <td className="px-3 py-3">
                          <ScoreBar score={row.overall_score} />
                        </td>
                        <td className="px-3 py-3">
                          <GradeBadge grade={row.grade} />
                        </td>
                        {DIMENSIONS.map((dim) => (
                          <td key={dim.key} className="px-3 py-3">
                            <ScoreBar score={row[dim.key]} />
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            <div className="mt-4 flex items-center justify-between">
              <PrimaryButton
                size="sm"
                variant="outline"
                disabled={currentPage <= 1}
                onClick={() => setOffset((prev) => Math.max(0, prev - PAGE_SIZE))}
              >
                {t("app.ranking.previous", currentLang)}
              </PrimaryButton>
              <PrimaryButton
                size="sm"
                variant="outline"
                disabled={currentPage >= totalPages}
                onClick={() => setOffset((prev) => Math.min((totalPages - 1) * PAGE_SIZE, prev + PAGE_SIZE))}
              >
                {t("app.ranking.next", currentLang)}
              </PrimaryButton>
            </div>
          </TarotCard>
        )}
      </div>
    </DashboardShell>
  );
}
