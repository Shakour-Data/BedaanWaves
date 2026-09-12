"use client";

import { useEffect, useRef, useState, useCallback, Suspense, lazy } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  TrendingUp,
  TrendingDown,
  Activity,
  Trophy,
  Newspaper,
  Sparkles,
  RefreshCw,
  Globe,
  ArrowUpRight,
  Zap,
  Newspaper as NewspaperIcon,
} from "lucide-react";
import { NewDashboardShell } from "@/components/layout/NewDashboardShell";
import { PageLoading } from "@/components/ui/PageLoading";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { Card } from "@/components/ui/Card";
import { cn } from "@/lib/cn";
import { fetchDashboardData, fetchGeneralDashboard, type GeneralDashboardResponse } from "@/lib/api/dashboard";
import { useUXStore } from "@/store/useUXStore";

const UnifiedSearchBar = lazy(() => import("@/components/search/UnifiedSearchBar").then(mod => ({ default: mod.UnifiedSearchBar })));
const GeneralDashboardTab = lazy(() => import("@/components/dashboard/GeneralDashboardTab").then(mod => ({ default: mod.GeneralDashboardTab })));
const DashboardTabNav = lazy(() => import("@/components/dashboard/DashboardTabNav").then(mod => ({ default: mod.DashboardTabNav })));

interface DimensionSummary {
  avg_score: number;
  min_score: number;
  max_score: number;
  count: number;
}

interface DashboardSnapshot {
  stats: { label: string; value: string; changePct?: number }[];
  topPerformers: { symbol: string; name: string; score: number }[];
  bottomPerformers: { symbol: string; name: string; score: number }[];
  movers: { symbol: string; name: string; market: "NASDAQ"; price: number; changePct: number }[];
  watchlist: { symbol: string; name: string; market: "NASDAQ"; price: number; changePct: number }[];
  news: { title: string; source: string; time: string }[];
  dimensions: { key: string; label: string; weight: number; data?: DimensionSummary }[];
  latestDate: string | null;
}

function gradeLabel(score: number): { grade: string; tone: "success" | "primary" | "warning" | "error" } {
  if (score >= 80) return { grade: "A", tone: "success" };
  if (score >= 65) return { grade: "B", tone: "primary" };
  if (score >= 50) return { grade: "C", tone: "warning" };
  return { grade: "D", tone: "error" };
}

function fmtScore(score: number | null | undefined): string {
  if (typeof score !== "number" || !Number.isFinite(score)) return "—";
  return score.toFixed(1);
}

function fmtDate(iso: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (!Number.isFinite(d.getTime())) return "—";
  return d.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function DashboardOverview({ data, load }: {
  data: DashboardSnapshot;
  load: (mode: "initial" | "refresh") => Promise<void>;
}) {
  return (
    <>
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-accent)] text-white shadow-md">
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-[var(--color-text-primary)]">
                Market Dashboard
              </h1>
              <p className="text-sm text-[var(--color-text-secondary)]">
                Live NASDAQ overview · last update {fmtDate(data.latestDate)}
              </p>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => load("refresh")}
            className="inline-flex items-center gap-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm font-medium text-[var(--color-text-secondary)] transition-colors hover:border-[var(--color-primary)] hover:text-[var(--color-text-primary)]"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </button>
          <Link
            href="/leaderboard"
            className="inline-flex items-center gap-2 rounded-xl border border-transparent bg-[var(--color-primary)] px-3 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-[var(--color-primary-hover)]"
          >
            View leaderboard
            <ArrowUpRight className="h-4 w-4" />
          </Link>
        </div>
      </header>

      <section className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5 shadow-sm">
        <div className="mb-3 flex items-center gap-2">
          <Zap className="h-4 w-4 text-[var(--color-primary)]" />
          <h2 className="text-sm font-semibold uppercase tracking-wider text-[var(--color-text-secondary)]">
            Quick search
          </h2>
        </div>
        <p className="mb-3 text-sm text-[var(--color-text-secondary)]">
          Search any stock, news headline, or page in the sidebar. Or use the quick search below.
        </p>
        <Suspense fallback={<div className="h-10 w-full" />}>
          <UnifiedSearchBar variant="topbar" placeholder="Search stocks, news, or pages…" />
        </Suspense>
      </section>

      <section className="grid grid-cols-2 gap-3 md:grid-cols-4">
        {data.stats.map((s) => (
          <Card key={s.label} className="flex flex-col gap-1 p-4">
            <span className="text-xs font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
              {s.label}
            </span>
            <span className="text-xl font-bold text-[var(--color-text-primary)]">{s.value}</span>
          </Card>
        ))}
      </section>

      <section className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-3 p-6">
          <div className="mb-4 flex items-center gap-2">
            <Newspaper className="h-4 w-4 text-[var(--color-primary)]" />
            <h2 className="text-sm font-semibold uppercase tracking-wider text-[var(--color-text-secondary)]">
              Latest news
            </h2>
          </div>
          {data.news.length === 0 ? (
            <p className="text-sm text-[var(--color-text-muted)]">No news available right now.</p>
          ) : (
            <ul className="flex flex-col gap-3">
              {data.news.slice(0, 6).map((n, i) => (
                <li key={i} className="border-b border-[var(--color-border)] pb-3 last:border-b-0 last:pb-0">
                  <p className="line-clamp-2 text-sm font-medium text-[var(--color-text-primary)]">{n.title}</p>
                  <p className="mt-1 text-xs text-[var(--color-text-muted)]">
                    {n.source}
                    {n.time ? ` · ${n.time}` : ""}
                  </p>
                </li>
              ))}
            </ul>
          )}
          <Link
            href="/news"
            className="mt-3 inline-flex items-center gap-1 text-xs font-medium text-[var(--color-primary)] hover:underline"
          >
            See all news <ArrowUpRight className="h-3 w-3" />
          </Link>
        </Card>
      </section>

      <section className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card className="p-6">
          <div className="mb-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Trophy className="h-4 w-4 text-[var(--color-warning)]" />
              <h2 className="text-sm font-semibold uppercase tracking-wider text-[var(--color-text-secondary)]">
                Top performers
              </h2>
            </div>
            <Link
              href="/leaderboard"
              className="text-xs font-medium text-[var(--color-primary)] hover:underline"
            >
              See all →
            </Link>
          </div>
          {data.topPerformers.length === 0 ? (
            <p className="text-sm text-[var(--color-text-muted)]">No data available.</p>
          ) : (
            <ul className="flex flex-col gap-2">
              {data.topPerformers.map((p) => {
                const { grade, tone } = gradeLabel(p.score);
                return (
                  <li key={p.symbol}>
                    <Link
                      href={`/stocks/${p.symbol}`}
                      className="group flex items-center gap-3 rounded-lg p-2 transition-colors hover:bg-[var(--color-muted)]"
                    >
                      <span
                        className={cn(
                          "flex h-9 w-9 items-center justify-center rounded-lg text-xs font-bold",
                          tone === "success" && "bg-[var(--color-success)]/15 text-[var(--color-success)]",
                          tone === "primary" && "bg-[var(--color-primary)]/15 text-[var(--color-primary)]",
                          tone === "warning" && "bg-[var(--color-warning)]/15 text-[var(--color-warning)]",
                          tone === "error" && "bg-[var(--color-error)]/15 text-[var(--color-error)]"
                        )}
                      >
                        {grade}
                      </span>
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-semibold text-[var(--color-text-primary)]">{p.symbol}</p>
                        <p className="truncate text-xs text-[var(--color-text-secondary)]">{p.name}</p>
                      </div>
                      <div className="flex items-center gap-1 text-sm font-semibold text-[var(--color-success)]">
                        <TrendingUp className="h-3.5 w-3.5" />
                        {fmtScore(p.score)}
                      </div>
                    </Link>
                  </li>
                );
              })}
            </ul>
          )}
        </Card>

        <Card className="p-6">
          <div className="mb-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Activity className="h-4 w-4 text-[var(--color-error)]" />
              <h2 className="text-sm font-semibold uppercase tracking-wider text-[var(--color-text-secondary)]">
                Underperformers
              </h2>
            </div>
            <Link
              href="/movers"
              className="text-xs font-medium text-[var(--color-primary)] hover:underline"
            >
              See all →
            </Link>
          </div>
          {data.bottomPerformers.length === 0 ? (
            <p className="text-sm text-[var(--color-text-muted)]">No data available.</p>
          ) : (
            <ul className="flex flex-col gap-2">
              {data.bottomPerformers.map((p) => {
                const { grade, tone } = gradeLabel(p.score);
                return (
                  <li key={p.symbol}>
                    <Link
                      href={`/stocks/${p.symbol}`}
                      className="group flex items-center gap-3 rounded-lg p-2 transition-colors hover:bg-[var(--color-muted)]"
                    >
                      <span
                        className={cn(
                          "flex h-9 w-9 items-center justify-center rounded-lg text-xs font-bold",
                          tone === "success" && "bg-[var(--color-success)]/15 text-[var(--color-success)]",
                          tone === "primary" && "bg-[var(--color-primary)]/15 text-[var(--color-primary)]",
                          tone === "warning" && "bg-[var(--color-warning)]/15 text-[var(--color-warning)]",
                          tone === "error" && "bg-[var(--color-error)]/15 text-[var(--color-error)]"
                        )}
                      >
                        {grade}
                      </span>
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-semibold text-[var(--color-text-primary)]">{p.symbol}</p>
                        <p className="truncate text-xs text-[var(--color-text-secondary)]">{p.name}</p>
                      </div>
                      <div className="flex items-center gap-1 text-sm font-semibold text-[var(--color-error)]">
                        <TrendingDown className="h-3.5 w-3.5" />
                        {fmtScore(p.score)}
                      </div>
                    </Link>
                  </li>
                );
              })}
            </ul>
          )}
        </Card>
      </section>

      {data.watchlist.length > 0 && (
        <section>
          <Card className="p-6">
            <div className="mb-4 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Globe className="h-4 w-4 text-[var(--color-primary)]" />
                <h2 className="text-sm font-semibold uppercase tracking-wider text-[var(--color-text-secondary)]">
                  Your watchlist
                </h2>
              </div>
              <Link
                href="/watchlist"
                className="text-xs font-medium text-[var(--color-primary)] hover:underline"
              >
                Open watchlist →
              </Link>
            </div>
            <ul className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {data.watchlist.slice(0, 6).map((w) => {
                const positive = w.changePct >= 0;
                return (
                  <li key={w.symbol}>
                    <Link
                      href={`/stocks/${w.symbol}`}
                      className="flex items-center justify-between rounded-lg border border-[var(--color-border)] p-3 transition-colors hover:border-[var(--color-primary)]/30"
                    >
                      <div>
                        <p className="text-sm font-semibold text-[var(--color-text-primary)]">{w.symbol}</p>
                        <p className="text-xs text-[var(--color-text-secondary)]">{w.name}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-semibold text-[var(--color-text-primary)]">
                          ${w.price.toFixed(2)}
                        </p>
                        <p
                          className={cn(
                            "text-xs font-medium",
                            positive ? "text-[var(--color-success)]" : "text-[var(--color-error)]"
                          )}
                        >
                          {positive ? "+" : ""}
                          {w.changePct.toFixed(2)}%
                        </p>
                      </div>
                    </Link>
                  </li>
                );
              })}
            </ul>
          </Card>
        </section>
      )}

      <footer className="flex items-center justify-between rounded-2xl border border-dashed border-[var(--color-border)] bg-[var(--color-surface)]/50 p-4 text-xs text-[var(--color-text-muted)]">
        <div className="flex items-center gap-2">
          <NewspaperIcon className="h-3.5 w-3.5" />
          <span>
            Use the search in the sidebar to jump to any stock, news headline, or page.
          </span>
        </div>
        <Link
          href="/methodology"
          className="font-medium text-[var(--color-primary)] hover:underline"
        >
          How scores are calculated →
        </Link>
      </footer>
    </>
  );
}

function DashboardTabState({ onTabChange }: { onTabChange: (tab: "overview" | "general") => void }) {
  const searchParams = useSearchParams();
  const tabParam = searchParams.get("tab");
  const activeTab: "overview" | "general" =
    tabParam === "general" ? "general" : "overview";

  useEffect(() => {
    onTabChange(activeTab);
  }, [activeTab, onTabChange]);

  return null;
}

export default function DashboardPage() {
  const addToast = useUXStore((s) => s.addToast);
  const [data, setData] = useState<DashboardSnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"overview" | "general">("overview");

  const load = useCallback(async (mode: "initial" | "refresh") => {
    if (mode === "initial") setLoading(true);
    setError(null);
    try {
      const [general, legacy] = await Promise.allSettled([
        fetchGeneralDashboard(),
        fetchDashboardData(),
      ]);

      if (general.status === "rejected" && legacy.status === "rejected") {
        const msg =
          (general.reason instanceof Error && general.reason.message) ||
          (legacy.reason instanceof Error && legacy.reason.message) ||
          "Failed to load dashboard data";
        setError(msg);
        if (mode === "initial") {
          addToast({ type: "error", message: msg });
        }
        return;
      }

      const g: GeneralDashboardResponse | null =
        general.status === "fulfilled" ? general.value : null;
      const l =
        legacy.status === "fulfilled"
          ? legacy.value
          : null;

      const dimensions = Object.entries(g?.dimensions ?? {}).map(([key, value]) => ({
        key,
        label: key.charAt(0).toUpperCase() + key.slice(1).replace(/_/g, " "),
        weight: 0,
        data: value as DimensionSummary,
      }));

      const coeffs = g?.coefficients ?? [];
      const dimMap = new Map(dimensions.map((d) => [d.key, d]));
      for (const c of coeffs) {
        const existing = dimMap.get(c.key);
        if (existing) existing.weight = c.weight;
      }

      // Compute the true market-wide average across ALL dimension scores
      // (not just the first dimension — the old code picked an arbitrary one).
      const allDimScores = Object.values(g?.dimensions ?? {})
        .map((d) => (d && typeof d.avg_score === "number" ? d.avg_score : 0))
        .filter((v) => v > 0);
      const marketAvgScore = allDimScores.length > 0
        ? allDimScores.reduce((a, b) => a + b, 0) / allDimScores.length
        : 0;

      const merged: DashboardSnapshot = {
        stats: [
          { label: "Universe", value: String(g?.summary?.total_symbols ?? l?.marketStats?.[0]?.value ?? "—") },
          { label: "Avg Score", value: marketAvgScore > 0 ? fmtScore(marketAvgScore) : "—" },
          {
            label: "Top Scorer",
            value: g?.top_performers?.[0]
              ? `${g.top_performers[0].symbol} ${fmtScore(g.top_performers[0].overall_score)}`
              : "—",
          },
          {
            label: "Latest Snapshot",
            value: g?.latest_date ? new Date(g.latest_date).toLocaleDateString("en-US", { month: "short", day: "numeric" }) : "—",
          },
        ],
        topPerformers: (g?.top_performers ?? []).slice(0, 5).map((p) => ({
          symbol: p.symbol,
          name: p.name,
          score: p.overall_score,
        })),
        bottomPerformers: (g?.bottom_performers ?? []).slice(0, 5).map((p) => ({
          symbol: p.symbol,
          name: p.name,
          score: p.overall_score,
        })),
        movers: l?.topMovers ?? [],
        watchlist: l?.watchlist ?? [],
        news: l?.news ?? [],
        dimensions: dimMap.size > 0
          ? Array.from(dimMap.values())
          : [
              { key: "fundamental", label: "Fundamental", weight: 0.2, data: undefined },
              { key: "technical", label: "Technical", weight: 0.2, data: undefined },
              { key: "sentiment", label: "Sentiment", weight: 0.15, data: undefined },
              { key: "risk", label: "Risk", weight: 0.15, data: undefined },
              { key: "macro", label: "Macro", weight: 0.15, data: undefined },
              { key: "ai", label: "AI", weight: 0.15, data: undefined },
            ],
        latestDate: g?.latest_date ?? null,
      };
      setData(merged);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to load dashboard";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [addToast]);

  const initialLoadRef = useRef(true);
  useEffect(() => {
    if (initialLoadRef.current) {
      initialLoadRef.current = false;
      void load("initial");
    }
  }, [load]);

  if (loading) {
    return (
      <NewDashboardShell title="Dashboard">
        <PageLoading />
      </NewDashboardShell>
    );
  }

  if (error && !data) {
    return (
      <NewDashboardShell title="Dashboard">
        <div className="flex min-h-[40vh] items-center justify-center">
          <ErrorMessage
            message={error}
            actions={[{ label: "Retry", onAction: () => load("initial") }]}
            moreHelpSteps={[
              "Check that the backend API is running on port 3000",
              "Verify your authentication token is still valid",
              "Try again in a few seconds",
            ]}
            helpTitle="Troubleshooting steps"
          />
        </div>
      </NewDashboardShell>
    );
  }

  if (!data) {
    return (
      <NewDashboardShell title="Dashboard">
        <PageLoading />
      </NewDashboardShell>
    );
  }

  return (
    <NewDashboardShell title="Dashboard">
      <div className="flex flex-col gap-6 animate-in fade-in duration-500">
        <Suspense fallback={<div className="h-10 w-full" />}>
          <DashboardTabNav
            tabs={[
              { id: "overview", label: "Overview", href: "/dashboard" },
              { id: "general", label: "Analytical", href: "/dashboard?tab=general" },
            ]}
          />
        </Suspense>
        <Suspense fallback={<div className="h-10 w-full" />}>
          <DashboardTabState onTabChange={setActiveTab} />
        </Suspense>
{activeTab === "general" ? (
          <Suspense fallback={<div className="h-64 w-full" />}>
            <GeneralDashboardTab />
          </Suspense>
        ) : (
          <DashboardOverview data={data} load={load} />
        )}
      </div>
    </NewDashboardShell>
  );
}
