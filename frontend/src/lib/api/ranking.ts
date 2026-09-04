import { apiClient } from "@/lib/api";
import { num } from "@/lib/utils";

export type Grade = "A_STRONG_BUY" | "B_BUY" | "C_HOLD" | "D_SELL" | "E_STRONG_SELL";

export type RankingSortField =
  | "overall_score"
  | "fundamental"
  | "technical"
  | "sentiment"
  | "risk"
  | "macro"
  | "ai";

export type SortOrder = "asc" | "desc";

export interface DimensionScores {
  fundamental: number;
  technical: number;
  sentiment: number;
  risk: number;
  macro: number;
  ai: number;
}

export interface NasdaqRanking {
  symbol: string;
  name: string;
  rank: number;
  overall_score: number;
  grade: Grade;
  fundamental: number;
  technical: number;
  sentiment: number;
  risk: number;
  macro: number;
  ai: number;
}

export interface FetchNasdaqRankingsParams {
  limit?: number;
  offset?: number;
  sort_by?: RankingSortField;
  order?: SortOrder;
}

interface RawNasdaqRanking extends Partial<NasdaqRanking> {
  symbol: string;
  name?: string;
  rank?: number;
  overall_score?: number;
  grade?: Grade;
}

interface NasdaqRankingEnvelope {
  status?: string;
  total?: number;
  limit?: number;
  offset?: number;
  data?: RawNasdaqRanking[];
  items?: RawNasdaqRanking[];
}

function normalize(item: RawNasdaqRanking): NasdaqRanking {
  return {
    symbol: item.symbol,
    name: item.name ?? item.symbol,
    rank: num(item.rank),
    overall_score: num(item.overall_score),
    grade: item.grade ?? "C_HOLD",
    fundamental: num(item.fundamental),
    technical: num(item.technical),
    sentiment: num(item.sentiment),
    risk: num(item.risk),
    macro: num(item.macro),
    ai: num(item.ai) };
}

function normalizeList(rows: RawNasdaqRanking[] | undefined): NasdaqRanking[] {
  return (rows ?? []).map(normalize);
}

export async function fetchNasdaqRankings(
  params: FetchNasdaqRankingsParams = {}
): Promise<{ items: NasdaqRanking[]; total: number }> {
  const qs = new URLSearchParams();
  if (params.limit !== undefined) qs.set("limit", String(params.limit));
  if (params.offset !== undefined) qs.set("offset", String(params.offset));
  if (params.sort_by) qs.set("sort_by", params.sort_by);
  if (params.order) qs.set("order", params.order);
  const query = qs.toString();

  const res = await apiClient.get<NasdaqRankingEnvelope | RawNasdaqRanking[]>(
    `/ranking/nasdaq${query ? `?${query}` : ""}`
  );

  const body = res.data;

  if (Array.isArray(body)) {
    const items = normalizeList(body);
    return { items, total: items.length };
  }

  const items = normalizeList(body.data ?? body.items);
  const total = num(body.total) || items.length;
  return { items, total };
}
