import { useMemo } from "react";
import { cn } from "@/lib/cn";
import { useLiveData, type LiveStreamKey } from "@/hooks/useLiveData";

export interface OrderBookLevel {
  rank: number;
  price: number;
  volume: number;
  order_count: number;
}

export interface OrderBookData {
  symbol?: string;
  bids?: OrderBookLevel[];
  asks?: OrderBookLevel[];
  spread?: number | null;
  spread_pct?: number | null;
  freshness_ts?: string;
}

export interface OrderBookProps {
  symbol: string;
  maxDepth?: number;
  showCumulative?: boolean;
  compact?: boolean;
  onData?: (data: OrderBookData) => void;
}

interface OrderBookRowProps {
  level: { price: number; volume: number; rank: number; order_count?: number };
  isBid: boolean;
  maxVolume: number;
  showCumulative: boolean;
  cumulative: number;
}

function OrderBookRow({
  level,
  isBid,
  maxVolume,
  showCumulative,
  cumulative,
}: OrderBookRowProps) {
  const pct = maxVolume > 0 ? (level.volume / maxVolume) * 100 : 0;
  const cumPct = maxVolume > 0 ? (cumulative / maxVolume) * 100 : 0;

  return (
    <div
      className={cn(
        "relative grid grid-cols-[60px_1fr_80px] items-center gap-2 rounded px-1 py-0.5 text-xs tabular-nums",
        isBid ? "text-green-500" : "text-red-500",
      )}
    >
      {!isBid && (
        <div className="text-right text-[var(--color-text-secondary)]">
          #{level.rank}
        </div>
      )}
      {isBid && (
        <div className="text-right text-[var(--color-text-secondary)]">
          #{level.rank}
        </div>
      )}
      <div className="relative flex items-center">
        <span className="z-10 font-medium tabular-nums">{level.price.toFixed(2)}</span>
        {showCumulative ? (
          <div
            className={cn(
              "absolute inset-0 rounded-sm opacity-20",
              isBid ? "bg-green-500" : "bg-red-500",
            )}
            style={{
              width: `${Math.min(100, cumPct)}%`,
              left: isBid ? "auto" : "0",
              right: isBid ? "0" : "auto",
            }}
          />
        ) : (
          <div
            className={cn(
              "absolute inset-0 rounded-sm opacity-20",
              isBid ? "bg-green-500" : "bg-red-500",
            )}
            style={{
              width: `${Math.min(100, pct)}%`,
              left: isBid ? "auto" : "0",
              right: isBid ? "0" : "auto",
            }}
          />
        )}
      </div>
      <div className="text-right">
        <span className="text-[var(--color-text-secondary)]">
          {showCumulative && (
            <span className="opacity-60 mr-1">
              {cumulative.toLocaleString()}
            </span>
          )}
          {level.volume.toLocaleString()}
        </span>
      </div>
    </div>
  );
}

export function OrderBook({
  symbol,
  maxDepth = 5,
  showCumulative = true,
  compact = false,
  onData,
}: OrderBookProps) {
  const streamKey = `orderbook:${symbol}` as LiveStreamKey;

  const liveData = useLiveData<OrderBookData>(streamKey, {
    onData: (data) => {
      onData?.(data);
    },
  });

  const snapshot = liveData.data;

  const displayBids = useMemo(() => {
    const bids = snapshot?.bids || [];
    return [...bids]
      .sort((a, b) => b.price - a.price)
      .slice(0, maxDepth)
      .map((l) => ({
        rank: l.rank,
        price: l.price,
        volume: l.volume,
        order_count: l.order_count || 0,
      }));
  }, [snapshot, maxDepth]);

  const displayAsks = useMemo(() => {
    const asks = snapshot?.asks || [];
    return [...asks]
      .sort((a, b) => a.price - b.price)
      .slice(0, maxDepth)
      .map((l) => ({
        rank: l.rank,
        price: l.price,
        volume: l.volume,
        order_count: l.order_count || 0,
      }));
  }, [snapshot, maxDepth]);

  const maxVolume = useMemo(() => {
    const all = [...displayBids, ...displayAsks];
    if (all.length === 0) return 1;
    return Math.max(...all.map((l) => l.volume), 1);
  }, [displayBids, displayAsks]);

  const bidCumulative: number[] = useMemo(() => {
    const cum: number[] = [];
    let total = 0;
    for (const l of displayBids) {
      total += l.volume;
      cum.push(total);
    }
    return cum;
  }, [displayBids]);

  const askCumulative: number[] = useMemo(() => {
    const cum: number[] = [];
    let total = 0;
    for (const l of displayAsks) {
      total += l.volume;
      cum.push(total);
    }
    return cum;
  }, [displayAsks]);

  const spread = snapshot?.spread;
  const spreadPct = snapshot?.spread_pct;

  if (!snapshot || (!displayBids.length && !displayAsks.length)) {
    return (
      <div
        className={cn(
          "flex items-center justify-center rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)]/30",
          compact ? "p-4" : "p-8",
        )}
      >
        <div className="flex flex-col items-center gap-2 text-[var(--color-text-secondary)]">
          <div className="text-xs">No order book data available</div>
        </div>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "flex flex-col rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)]/50",
        compact ? "p-3" : "p-4",
      )}
    >
      <div className={cn("flex items-center justify-between mb-3", compact && "mb-2")}>
        <div className="flex items-center gap-2">
          <span className="font-semibold text-[var(--color-text-primary)]">
            {snapshot.symbol || symbol} Order Book
          </span>
          <span className={cn("text-xs", compact && "text-xs")}>
            Top {maxDepth} Levels
          </span>
        </div>
        <div className="flex items-center gap-2 text-xs text-[var(--color-text-secondary)]">
          {spread !== undefined && spread !== null && (
            <span>Spread: {spread.toFixed(2)}</span>
          )}
          {spreadPct !== undefined && spreadPct !== null && (
            <span>({spreadPct.toFixed(2)}%)</span>
          )}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-px text-[10px] font-medium text-[var(--color-text-secondary)] uppercase">
        <div>Bid</div>
        <div className="text-center">Price</div>
        <div className="text-right">Ask</div>
      </div>

      <div className="relative grid grid-cols-3">
        <div className="space-y-0.5">
          {displayBids.map((level, i) => {
            return (
              <OrderBookRow
                key={`bid-${level.rank}`}
                level={level}
                isBid={true}
                maxVolume={maxVolume}
                showCumulative={showCumulative}
                cumulative={bidCumulative[i]}
              />
            );
          })}
        </div>

        <div className="border-l border-r border-[var(--color-border)] px-1">
          <div className="flex items-center justify-center h-5 text-center text-[var(--color-text-secondary]">
            {displayBids.length > 0 && displayAsks.length > 0
              ? displayBids[0].price.toFixed(2)
              : "-"}
          </div>
          <div className="border-t border-[var(--color-border)]" />
          <div className="flex items-center justify-center h-5 text-center text-[var(--color-text-secondary]">
            {displayBids.length > 0 && displayAsks.length > 0
              ? displayAsks[0].price.toFixed(2)
              : "-"}
          </div>
        </div>

        <div className="space-y-0.5">
          {displayAsks.map((level, i) => {
            return (
              <OrderBookRow
                key={`ask-${level.rank}`}
                level={level}
                isBid={false}
                maxVolume={maxVolume}
                showCumulative={showCumulative}
                cumulative={askCumulative[i]}
              />
            );
          })}
        </div>
      </div>

      <div className="mt-2 border-t border-[var(--color-border)] pt-2 flex justify-between items-center text-xs">
        <div className="flex gap-4">
          <span className="text-[var(--color-text-secondary)]">
            Bid Vol: {(displayBids.reduce((s, l) => s + l.volume, 0)).toLocaleString()}
          </span>
          <span className="text-[var(--color-text-secondary)]">
            Ask Vol: {(displayAsks.reduce((s, l) => s + l.volume, 0)).toLocaleString()}
          </span>
        </div>
        <span className={cn(
          "text-xs",
          liveData.connectionHealth === "live"
            ? "text-[var(--color-success)]"
            : "text-[var(--color-text-secondary)]",
        )}>
          {liveData.connectionHealth.toUpperCase()}
        </span>
      </div>
    </div>
  );
}
