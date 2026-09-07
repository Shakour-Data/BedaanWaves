import { create } from 'zustand';

export type LiveStreamKey =
  | 'market'
  | 'scores'
  | 'news'
  | `quote:${string}`
  | `intraday:${string}:${string}`
  | `orderbook:${string}`;

export type ConnectionHealth =
  | 'live'
  | 'stale'
  | 'disconnected'
  | 'reconnecting'
  | 'syncing';

interface LiveStreamEntry {
  data: unknown;
  latest: unknown;
  connectionHealth: ConnectionHealth;
  lastDataAgeMs: number | null;
  lastSequence: number | null;
  lastEventTimestamp: number | null;
  refCount: number;
}

interface LiveStoreState {
  streams: Record<string, LiveStreamEntry>;
  setStreamData: (
    key: LiveStreamKey,
    data: unknown,
    latest: unknown,
    sequence: number | null,
    dataAgeMs: number | null
  ) => void;
  setConnectionHealth: (key: LiveStreamKey, health: ConnectionHealth) => void;
  incrementRef: (key: LiveStreamKey) => void;
  decrementRef: (key: LiveStreamKey) => void;
  getRefCount: (key: LiveStreamKey) => number;
  removeStream: (key: LiveStreamKey) => void;
  resetStream: (key: LiveStreamKey) => void;
  getStream: (key: LiveStreamKey) => LiveStreamEntry | undefined;
}

const emptyEntry = (): LiveStreamEntry => ({
  data: null,
  latest: null,
  connectionHealth: 'syncing',
  lastDataAgeMs: null,
  lastSequence: null,
  lastEventTimestamp: null,
  refCount: 0,
});

export const useLiveStore = create<LiveStoreState>((set, get) => ({
  streams: {},

  setStreamData: (key, data, latest, sequence, dataAgeMs) => {
    set((state) => {
      const existing = state.streams[key] ?? emptyEntry();
      return {
        streams: {
          ...state.streams,
          [key]: {
            ...existing,
            data,
            latest,
            lastSequence: sequence,
            lastDataAgeMs: dataAgeMs,
            lastEventTimestamp: Date.now(),
            connectionHealth: existing.connectionHealth === 'syncing' ? 'live' : existing.connectionHealth,
          },
        },
      };
    });
  },

  setConnectionHealth: (key, health) => {
    set((state) => {
      const existing = state.streams[key] ?? emptyEntry();
      return {
        streams: {
          ...state.streams,
          [key]: {
            ...existing,
            connectionHealth: health,
          },
        },
      };
    });
  },

  incrementRef: (key) => {
    set((state) => {
      const existing = state.streams[key] ?? emptyEntry();
      return {
        streams: {
          ...state.streams,
          [key]: {
            ...existing,
            refCount: existing.refCount + 1,
          },
        },
      };
    });
  },

  decrementRef: (key) => {
    set((state) => {
      const existing = state.streams[key] ?? emptyEntry();
      const newCount = Math.max(0, existing.refCount - 1);
      return {
        streams: {
          ...state.streams,
          [key]: {
            ...existing,
            refCount: newCount,
          },
        },
      };
    });
  },

  getRefCount: (key) => {
    return get().streams[key]?.refCount ?? 0;
  },

  removeStream: (key) => {
    set((state) => {
      const next = { ...state.streams };
      delete next[key];
      return { streams: next };
    });
  },

  resetStream: (key) => {
    set((state) => {
      const existing = state.streams[key];
      return {
        streams: {
          ...state.streams,
          [key]: {
            ...emptyEntry(),
            refCount: existing?.refCount ?? 0,
          },
        },
      };
    });
  },

  getStream: (key) => {
    return get().streams[key];
  },
}));

export function useLiveStream<T = unknown>(key: LiveStreamKey) {
  return useLiveStore((state) => {
    const entry = state.streams[key];
    return {
      data: entry?.data as T | null,
      latest: entry?.latest as T | null,
      connectionHealth: entry?.connectionHealth ?? 'syncing' as ConnectionHealth,
      lastDataAgeMs: entry?.lastDataAgeMs ?? null,
      lastSequence: entry?.lastSequence ?? null,
      lastEventTimestamp: entry?.lastEventTimestamp ?? null,
      refCount: entry?.refCount ?? 0,
    };
  });
}

export const STALE_THRESHOLD_MS = 30_000;
export const DISCONNECT_THRESHOLD_MS = 90_000;

export function isStaleByAge(ageMs: number | null, timestamp: number | null): boolean {
  if (ageMs !== null && ageMs > STALE_THRESHOLD_MS) return true;
  if (timestamp !== null && Date.now() - timestamp > STALE_THRESHOLD_MS) return true;
  return false;
}

export function getStreamEndpoint(key: LiveStreamKey): string {
  if (key === 'market') return '/live-sse/market/stream';
  if (key === 'scores') return '/live-sse/scores/stream?scope=NASDAQ';
  if (key === 'news') return '/live-sse/news/stream';
  if (key.startsWith('orderbook:')) {
    const symbol = key.slice('orderbook:'.length);
    return `/live-sse/orderbook/${encodeURIComponent(symbol)}/stream`;
  }
  if (key.startsWith('quote:')) {
    const symbol = key.slice('quote:'.length);
    return `/live-sse/quote/${encodeURIComponent(symbol)}/stream`;
  }
  if (key.startsWith('intraday:')) {
    const rest = key.slice('intraday:'.length);
    const colon = rest.indexOf(':');
    if (colon === -1) {
      return `/live-sse/intraday/${encodeURIComponent(rest)}/stream?interval=5m`;
    }
    const symbol = rest.slice(0, colon);
    const interval = rest.slice(colon + 1);
    return `/live-sse/intraday/${encodeURIComponent(symbol)}/stream?interval=${encodeURIComponent(interval)}`;
  }
  return '';
}

export function getSnapshotEndpoint(key: LiveStreamKey): string {
  if (key === 'market') return '/live/market';
  if (key === 'scores') return '/live/scores?scope=NASDAQ';
  if (key === 'news') return '/live/news';
  if (key.startsWith('orderbook:')) {
    const symbol = key.slice('orderbook:'.length);
    return `/live/orderbook/${encodeURIComponent(symbol)}`;
  }
  if (key.startsWith('quote:')) {
    const symbol = key.slice('quote:'.length);
    return `/live/quote/${encodeURIComponent(symbol)}/snapshot`;
  }
  if (key.startsWith('intraday:')) {
    const rest = key.slice('intraday:'.length);
    const colon = rest.indexOf(':');
    if (colon === -1) {
      return `/live/intraday/${encodeURIComponent(rest)}?interval=5m`;
    }
    const symbol = rest.slice(0, colon);
    const interval = rest.slice(colon + 1);
    return `/live/intraday/${encodeURIComponent(symbol)}?interval=${encodeURIComponent(interval)}`;
  }
  return '';
}
