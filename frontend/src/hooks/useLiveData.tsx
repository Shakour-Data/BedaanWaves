import { useCallback, useEffect, useRef, useState } from 'react';
import {
  createSSEConnection,
  disconnectSSE,
  getSSEConnection,
  type SSEEvent,
} from '@/lib/sse';
import { apiClient } from '@/lib/api';
import {
  useLiveStore,
  type LiveStreamKey,
  type ConnectionHealth,
  getStreamEndpoint,
  getSnapshotEndpoint,
  isStaleByAge,
  STALE_THRESHOLD_MS,
  DISCONNECT_THRESHOLD_MS,
} from '@/store/useLiveStore';

export type { LiveStreamKey, ConnectionHealth } from '@/store/useLiveStore';
export type { SSEEvent } from '@/lib/sse';

export interface UseLiveDataOptions<T> {
  initialData?: T | null;
  enabled?: boolean;
  onData?: (data: T, event: SSEEvent<T>) => void;
  onHealthChange?: (health: ConnectionHealth) => void;
}

export interface UseLiveDataReturn<T> {
  data: T | null;
  latest: T | null;
  connectionHealth: ConnectionHealth;
  lastDataAgeMs: number | null;
  lastSequence: number | null;
  lastEventTimestamp: number | null;
  isStale: boolean;
  manualResync: () => Promise<boolean>;
}

const HEALTH_TRANSITION_MS = 2_000;

export function useLiveData<T = unknown>(
  key: LiveStreamKey,
  options: UseLiveDataOptions<T> = {}
): UseLiveDataReturn<T> {
  const { initialData = null, enabled = true, onData, onHealthChange } = options;

  const streamEntry = useLiveStore((state) => state.streams[key]);
  const setStreamData = useLiveStore((state) => state.setStreamData);
  const setConnectionHealth = useLiveStore((state) => state.setConnectionHealth);
  const incrementRef = useLiveStore((state) => state.incrementRef);
  const decrementRef = useLiveStore((state) => state.decrementRef);
  const resetStream = useLiveStore((state) => state.resetStream);
  const getRefCount = useLiveStore((state) => state.getRefCount);

  const lastSequenceRef = useRef<number | null>(null);
  const resyncInProgressRef = useRef(false);
  const healthTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const staleTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const lastHealthRef = useRef<ConnectionHealth>('syncing');
  const disconnectCountRef = useRef(0);
  const onDataRef = useRef(onData);
  const onHealthChangeRef = useRef(onHealthChange);
  const keyRef = useRef(key);
  const enabledRef = useRef(enabled);

  useEffect(() => {
    onDataRef.current = onData;
    onHealthChangeRef.current = onHealthChange;
    keyRef.current = key;
    enabledRef.current = enabled;
  }, [onData, onHealthChange, key, enabled]);

  const data = (streamEntry?.data as T | null) ?? initialData;
  const latest = (streamEntry?.latest as T | null) ?? initialData;
  const connectionHealth = streamEntry?.connectionHealth ?? 'syncing';
  const lastDataAgeMs = streamEntry?.lastDataAgeMs ?? null;
  const lastSequence = streamEntry?.lastSequence ?? null;
  const lastEventTimestamp = streamEntry?.lastEventTimestamp ?? null;

  const isStale = isStaleByAge(lastDataAgeMs, lastEventTimestamp);

  const runSnapshotResync = useCallback(async (k: LiveStreamKey): Promise<boolean> => {
    if (resyncInProgressRef.current) return false;
    resyncInProgressRef.current = true;
    setConnectionHealth(k, 'syncing');

    try {
      const endpoint = getSnapshotEndpoint(k);
      if (!endpoint) {
        setConnectionHealth(k, 'disconnected');
        return false;
      }

      const res = await apiClient.get<{ event?: string; sequence?: number; data_age_ms?: number; data?: T }>(endpoint, {
        timeout: 15_000,
      });
      const body = res.data;
      const snapshotData = (body?.data ?? body) as T;
      const sequence = typeof body?.sequence === 'number' ? body.sequence : null;
      const dataAgeMs = typeof body?.data_age_ms === 'number' ? body.data_age_ms : null;

      lastSequenceRef.current = sequence;
      setStreamData(k, snapshotData, snapshotData, sequence, dataAgeMs);
      setConnectionHealth(k, 'live');
      disconnectCountRef.current = 0;
      return true;
    } catch (err) {
      console.warn(`[useLiveData] snapshot resync failed for ${k}:`, err);
      setConnectionHealth(k, 'disconnected');
      return false;
    } finally {
      resyncInProgressRef.current = false;
    }
  }, [setStreamData, setConnectionHealth]);

  const manualResync = useCallback(async () => {
    lastSequenceRef.current = null;
    resetStream(key);
    return runSnapshotResync(key);
  }, [key, resetStream, runSnapshotResync]);

  const applyHealth = useCallback(
    (k: LiveStreamKey, health: ConnectionHealth) => {
      if (lastHealthRef.current === health) return;
      lastHealthRef.current = health;
      setConnectionHealth(k, health);
      onHealthChangeRef.current?.(health);
    },
    [setConnectionHealth]
  );

  useEffect(() => {
    if (!enabled) return;
    const k = key;

    incrementRef(k);

    const currentRefCount = getRefCount(k);

    const handleMessage = (event: SSEEvent<T>) => {
      const prevSeq = lastSequenceRef.current;
      const currSeq = event.sequence;

      if (prevSeq !== null && currSeq !== null) {
        const gap = currSeq - prevSeq - 1;
        if (gap > 2 && !resyncInProgressRef.current) {
          console.warn(
            `[useLiveData] sequence gap for ${k}: prev=${prevSeq}, curr=${currSeq}, gap=${gap}. Triggering resync.`
          );
          void runSnapshotResync(k);
        }
      }

      if (currSeq !== null) {
        lastSequenceRef.current = currSeq;
      }

      disconnectCountRef.current = 0;

      if (healthTimerRef.current) {
        clearTimeout(healthTimerRef.current);
        healthTimerRef.current = null;
      }
      applyHealth(k, 'live');

      setStreamData(k, event.data, event.data, event.sequence, event.data_age_ms);
      onDataRef.current?.(event.data, event);
    };

    const handleOpen = () => {
      disconnectCountRef.current = 0;
      if (getRefCount(k) <= 1 || !useLiveStore.getState().streams[k]) {
        applyHealth(k, 'syncing');
      }
      if (healthTimerRef.current) {
        clearTimeout(healthTimerRef.current);
      }
      healthTimerRef.current = setTimeout(() => {
        applyHealth(k, 'live');
      }, HEALTH_TRANSITION_MS);
    };

    const handleError = () => {
      if (lastHealthRef.current !== 'reconnecting') {
        applyHealth(k, 'reconnecting');
      }
    };

    const handleDisconnect = () => {
      disconnectCountRef.current += 1;
      if (disconnectCountRef.current >= 3) {
        applyHealth(k, 'disconnected');
      } else {
        applyHealth(k, 'reconnecting');
      }
    };

    const handleReconnect = (attempt: number) => {
      applyHealth(k, 'reconnecting');
      if (attempt >= 3) {
        setTimeout(() => applyHealth(k, 'disconnected'), 5_000);
      }
    };

    const tickStale = () => {
      const entry = useLiveStore.getState().streams[k];
      const health = lastHealthRef.current;
      if (health === 'live') {
        const ts = entry?.lastEventTimestamp ?? null;
        const age = entry?.lastDataAgeMs ?? null;
        if (ts !== null && Date.now() - ts > DISCONNECT_THRESHOLD_MS) {
          applyHealth(k, 'stale');
        } else if (isStaleByAge(age, ts) && (ts === null || Date.now() - ts > STALE_THRESHOLD_MS)) {
          applyHealth(k, 'stale');
        }
      }
    };

    const existingEntry = useLiveStore.getState().streams[k];
    if (currentRefCount <= 1 || !existingEntry) {
      applyHealth(k, 'syncing');
      lastSequenceRef.current = null;
      void runSnapshotResync(k);
    } else if (existingEntry) {
      lastSequenceRef.current = existingEntry.lastSequence;
      lastHealthRef.current = existingEntry.connectionHealth;
    }

    if (!getSSEConnection(k)) {
      const endpoint = getStreamEndpoint(k);
      if (endpoint) {
        createSSEConnection<T>(k, {
          endpoint,
          onMessage: handleMessage,
          onOpen: handleOpen,
          onError: handleError,
          onDisconnect: handleDisconnect,
          onReconnect: handleReconnect,
          reconnect: true,
          reconnectInterval: 5_000,
          maxReconnectAttempts: 20,
        });
      }
    } else {
      const conn = getSSEConnection(k);
      if (conn && conn.eventSource && conn.eventSource.readyState === 2) {
        conn.reconnect();
      }
    }

    staleTimerRef.current = setInterval(tickStale, 5_000);

    return () => {
      decrementRef(k);
      clearInterval(staleTimerRef.current!);
      staleTimerRef.current = null;
      if (healthTimerRef.current) {
        clearTimeout(healthTimerRef.current);
        healthTimerRef.current = null;
      }

      const newRefCount = getRefCount(k);
      if (newRefCount <= 0) {
        disconnectSSE(k);
      }
    };
  }, [key, enabled, incrementRef, decrementRef, getRefCount, setStreamData, applyHealth, runSnapshotResync]);

  return {
    data,
    latest,
    connectionHealth,
    lastDataAgeMs,
    lastSequence,
    lastEventTimestamp,
    isStale,
    manualResync,
  };
}

export interface ConnectionIndicatorProps {
  health: ConnectionHealth;
  dataAgeMs: number | null;
  lastEventTs: number | null;
  label?: string;
}

const HEALTH_TEXT: Record<ConnectionHealth, string> = {
  live: 'LIVE',
  stale: 'STALE',
  disconnected: 'DISCONNECTED',
  reconnecting: 'RECONNECTING',
  syncing: 'SYNCING',
};

const HEALTH_BORDER: Record<ConnectionHealth, string> = {
  live: 'border-l-[var(--color-success)]',
  stale: 'border-l-[var(--color-warning)]',
  disconnected: 'border-l-[var(--color-error)]',
  reconnecting: 'border-l-[var(--color-primary)]',
  syncing: 'border-l-[var(--color-text-secondary)]',
};

const HEALTH_TEXT_COLOR: Record<ConnectionHealth, string> = {
  live: 'text-[var(--color-success)]',
  stale: 'text-[var(--color-warning)]',
  disconnected: 'text-[var(--color-error)]',
  reconnecting: 'text-[var(--color-primary)]',
  syncing: 'text-[var(--color-text-secondary)]',
};

export function LiveConnectionIndicator({
  health,
  dataAgeMs,
  lastEventTs,
  label,
}: ConnectionIndicatorProps) {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, []);
  let ageSeconds: number | null = null;
  if (typeof dataAgeMs === 'number') {
    ageSeconds = Math.round(dataAgeMs / 1000);
  } else if (lastEventTs !== null) {
    ageSeconds = Math.max(0, Math.round((now - lastEventTs) / 1000));
  }

  return (
    <div
      aria-live="polite"
      className={`inline-flex items-center gap-2 rounded-md border-l-2 ${HEALTH_BORDER[health]} bg-[var(--color-surface)]/60 px-2 py-1 text-xs pl-3`}
    >
      {label ? (
        <span className="text-[var(--color-text-secondary)]">{label}</span>
      ) : null}
      <span className={`font-bold tracking-wide ${HEALTH_TEXT_COLOR[health]}`}>
        {HEALTH_TEXT[health]}
      </span>
      {typeof ageSeconds === 'number' ? (
        <span
          className="text-[var(--color-text-secondary)] tabular-nums"
          data-age-seconds={ageSeconds}
          aria-label={`data age ${ageSeconds} seconds`}
        >
          ({ageSeconds}s ago)
        </span>
      ) : null}
    </div>
  );
}
