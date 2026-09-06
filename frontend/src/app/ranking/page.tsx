"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { cn } from "@/lib/cn";
import { NewDashboardShell } from "@/components/layout/NewDashboardShell";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { t } from "@/lib/i18n";
import { getApiErrorMessage } from "@/lib/api";
import {
  useLiveData,
  LiveConnectionIndicator,
  type LiveStreamKey,
} from "@/hooks/useLiveData";
import {
  fetchNasdaqRankings,
  type Grade,
  type NasdaqRanking,
  type RankingSortField,
  type SortOrder,
} from "@/lib/api/ranking";

const PAGE_SIZE = 20;

const GRADE_STYLES: Record<Grade, "success" | "warning" | "error" | "default"> = {
  STRONG_BULLISH: "success",
  BULLISH: "success",
  NEUTRAL: "warning",
  BEARISH: "error",
  STRONG_BEARISH: "error",
};

interface ScoreDeltaEvent {
  symbol: string;
  overall_score_delta?: number;
  overall_score?: number;
  grade?: Grade;
  fundamental?: number;
  technical?: number;
  sentiment?: number;
  risk?: number;
  macro?: number;
  ai?: number;
}

interface ScoresStreamPayload {
  deltas?: ScoreDeltaEvent[];
  items?: NasdaqRanking[];
}

type ScoreBadgeMap = Record<string, { delta: number; setAt: number }>;

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
        <div
          className={cn(
            "h-full rounded-full",
            variant === "success"
              ? "bg-success"
              : variant === "warning"
              ? "bg-warning"
              : "bg-error"
          )}
          style={{ width: `${Math.max(0, Math.min(100, score))}%` }}
        />
      </div>
      <span
        className={cn(
          "w-8 text-right text-sm font-semibold",
          variant === "success"
            ? "text-success"
            : variant === "warning"
            ? "text-warning"
            : "text-error"
        )}
      >
        {score}
      </span>
    </div>
  );
}

function GradeBadge({ grade }: { grade: Grade }) {
  const label = t(`app.ranking.grades.${grade}`);
  return <Badge variant={GRADE_STYLES[grade]} size="md">{label}</Badge>;
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

function DeltaBadge({ delta }: { delta: number }) {
  if (delta === 0) return null;
  const positive = delta > 0;
  return (
    <span
      className={cn(
        "ml-1 inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-bold tabular-nums",
        positive
          ? "bg-[var(--color-success)]/10 text-[var(--color-success)]"
          : "bg-[var(--color-error)]/10 text-[var(--color-error)]"
      )}
    >
      {positive ? "+" : "-"}
      {Math.abs(delta).toFixed(1)}
    </span>
  );
}

export default function RankingPage() {
  const [items, setItems] = useState<NasdaqRanking[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [offset, setOffset] = useState(0);
  const [sortBy, setSortBy] = useState<RankingSortField>("overall_score");
  const [order, setOrder] = useState<SortOrder>("desc");
  const [liveEnabled, setLiveEnabled] = useState(true);
  const [scoreBadges, setScoreBadges] = useState<ScoreBadgeMap>({});
  const lastEventTimestamp = useRef<number | null>(null);
  const [lastEventTs, setLastEventTs] = useState<number | null>(null);

  const load = useCallback(() => {
    let active = true;
    Promise.resolve()
      .then(() => {
        if (!active) return;
        setLoading(true);
        setError(null);
        return fetchNasdaqRankings({ limit: PAGE_SIZE, offset, sort_by: sortBy, order });
      })
      .then((res) => {
        if (!active || !res) return;
        setItems(res.items);
        setTotal(res.total);
      })
      .catch((err: unknown) => {
        if (!active) return;
        const message = getApiErrorMessage(err);
        setError(message || t("app.ranking.error_desc"));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [offset, sortBy, order]);

  useEffect(() => load(), [load]);

  useEffect(() => {
    if (!liveEnabled) return;
    const timer = setInterval(() => {
      const now = Date.now();
      setScoreBadges((prev) => {
        let changed = false;
        const next: ScoreBadgeMap = {};
        for (const [sym, entry] of Object.entries(prev)) {
          if (now - entry.setAt < 10_000) {
            next[sym] = entry;
          } else {
            changed = true;
          }
        }
        return changed ? next : prev;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, [liveEnabled]);

  const handleScoreData = useCallback(
    (payload: ScoresStreamPayload) => {
      const deltas = payload?.deltas ?? [];
      if (deltas.length === 0) return;
      const now = Date.now();
      lastEventTimestamp.current = now;
      setLastEventTs(now);

      setItems((prevItems) => {
        if (prevItems.length === 0) return prevItems;
        const bySymbol = new Map(prevItems.map((r) => [r.symbol, { ...r }]));
        const patchBadges: ScoreBadgeMap = {};
        let anyPatch = false;

        for (const d of deltas) {
          const row = bySymbol.get(d.symbol);
          if (!row) continue;
          anyPatch = true;
          if (typeof d.overall_score === "number") {
            const prev = row.overall_score;
            row.overall_score = Math.max(0, Math.min(100, d.overall_score));
            const delta = Number((row.overall_score - prev).toFixed(2));
            if (delta !== 0) {
              patchBadges[d.symbol] = { delta, setAt: now };
            }
          } else if (typeof d.overall_score_delta === "number") {
            const prev = row.overall_score;
            row.overall_score = Math.max(
              0,
              Math.min(100, prev + d.overall_score_delta)
            );
            const delta = Number((row.overall_score - prev).toFixed(2));
            if (delta !== 0) {
              patchBadges[d.symbol] = { delta: Number(delta), setAt: now };
            }
          }
          if (d.grade) row.grade = d.grade;
          (["fundamental", "technical", "sentiment", "risk", "macro", "ai"] as const).forEach(
            (dim) => {
              if (typeof d[dim] === "number") {
                (row as NasdaqRanking)[dim] = Math.max(0, Math.min(100, d[dim] as number));
              }
            }
          );
        }

        if (!anyPatch) return prevItems;

        setScoreBadges((prev) => ({ ...prev, ...patchBadges }));

        const sorted = [...bySymbol.values()].sort((a, b) => {
          const av = a[sortBy] as number | string;
          const bv = b[sortBy] as number | string;
          if (typeof av === "number" && typeof bv === "number") {
            return order === "desc" ? bv - av : av - bv;
          }
          return order === "desc"
            ? String(bv).localeCompare(String(av))
            : String(av).localeCompare(String(bv));
        });
        return sorted;
      });
    },
    [sortBy, order]
  );

  const scoresLive = useLiveData<ScoresStreamPayload>("scores" as LiveStreamKey, {
    enabled: liveEnabled,
    onData: handleScoreData,
  });

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
    <NewDashboardShell title={t("app.ranking.title")}>
      <div className="space-y-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold text-foreground">{t("app.ranking.title")}</h1>
            <p className="text-muted-foreground">{t("app.ranking.subtitle")}</p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <LiveConnectionIndicator
              health={scoresLive.connectionHealth}
              dataAgeMs={scoresLive.lastDataAgeMs}
              lastEventTs={lastEventTs}
              label="Scores"
            />
            <label className="inline-flex items-center gap-2 rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-1.5 text-xs font-medium">
              <input
                type="checkbox"
                className="h-3.5 w-3.5 accent-[var(--color-primary)]"
                checked={liveEnabled}
                onChange={(e) => setLiveEnabled(e.target.checked)}
              />
              LIVE patch ranking
            </label>
          </div>
        </div>

        {loading ? (
          <div className="flex justify-center py-12">
            <Spinner size="lg" />
          </div>
        ) : error ? (
          <ErrorMessage
            message={t("app.ranking.error_title")}
            actions={[{ label: t("app.ranking.retry"), onAction: () => load() }]}
          />
        ) : (
          <Card>
            <div className="mb-4 flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                {t("app.ranking.showing")
                  .replace("{from}", String(from))
                  .replace("{to}", String(to))
                  .replace("{total}", String(total))}
              </p>
              <p className="text-sm text-muted-foreground">
                {t("app.ranking.page")
                  .replace("{page}", String(currentPage))
                  .replace("{pages}", String(totalPages))}
              </p>
            </div>

            {items.length === 0 ? (
              <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border bg-surface/30 py-16">
                <h3 className="mt-2 text-lg font-medium text-foreground">{t("app.ranking.no_results")}</h3>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full border-collapse text-sm">
                  <thead>
                    <tr className="border-b border-border">
                      <th className={cn(headerCellClass, "w-12 text-center")} onClick={() => toggleSort("overall_score")}>
                        {t("app.ranking.rank")}
                      </th>
                      <th className={cn(headerCellClass, "min-w-[80px]")}>{t("app.ranking.symbol")}</th>
                      <th className={cn(headerCellClass, "min-w-[160px]")}>{t("app.ranking.name")}</th>
                      <th className={headerCellClass} onClick={() => toggleSort("overall_score")}>
                        {t("app.ranking.overall_score")}
                        {sortIndicator("overall_score")}
                      </th>
                      <th className={cn(headerCellClass, "min-w-[110px]")}>{t("app.ranking.grade")}</th>
                      {["fundamental", "technical", "sentiment", "risk", "macro", "ai"].map((dim) => (
                        <th key={dim} className={headerCellClass} onClick={() => toggleSort(dim as RankingSortField)}>
                          {t(`app.ranking.${dim}`)}
                          {sortIndicator(dim as RankingSortField)}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {items.map((row, idx) => {
                      const badge = scoreBadges[row.symbol];
                      return (
                        <tr
                          key={row.symbol}
                          className="transition-all duration-300 ease-out hover:bg-neutral/50"
                        >
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
                            <div className="flex items-center">
                              <ScoreBar score={row.overall_score} />
                              {badge ? <DeltaBadge delta={badge.delta} /> : null}
                            </div>
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
                      );
                    })}
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
                {t("app.ranking.previous")}
              </Button>
              <Button
                size="sm"
                variant="outline"
                disabled={currentPage >= totalPages}
                onClick={() => setOffset((prev) => Math.min((totalPages - 1) * PAGE_SIZE, prev + PAGE_SIZE))}
              >
                {t("app.ranking.next")}
              </Button>
            </div>
          </Card>
        )}
      </div>
    </NewDashboardShell>
  );
}
