import { API_BASE_URL } from './utils';

export interface SSEEvent<T = unknown> {
  type: string;
  event: string;
  data: T;
  timestamp: number;
  eventId?: string;
  sequence: number | null;
  data_age_ms: number | null;
}

export interface SSEConnectionOptions<T = unknown> {
  endpoint: string;
  onMessage?: (event: SSEEvent<T>) => void;
  onError?: (error: Event) => void;
  onOpen?: () => void;
  onDisconnect?: () => void;
  onReconnect?: (attempt: number) => void;
  reconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  headers?: Record<string, string>;
}

export interface SSEConnection {
  eventSource: EventSource | null;
  disconnect: () => void;
  reconnect: () => void;
  isConnected: boolean;
}

const activeConnections: Map<string, SSEConnection> = new Map();

function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('token');
}

export function createSSEConnection<T = unknown>(
  key: string,
  options: SSEConnectionOptions<T>
): SSEConnection {
  if (activeConnections.has(key)) {
    const existing = activeConnections.get(key)!;
    existing.disconnect();
  }

  const {
    endpoint,
    onMessage,
    onError,
    onOpen,
    onDisconnect,
    onReconnect,
    reconnect = true,
    reconnectInterval = 5000,
    maxReconnectAttempts = 10 } = options;

  let eventSource: EventSource | null = null;
  let reconnectAttempts = 0;
  let isConnected = false;
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null;

  const clearReconnectTimer = () => {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
  };

  const scheduleReconnect = () => {
    if (reconnect && reconnectAttempts < maxReconnectAttempts) {
      reconnectAttempts++;
      onReconnect?.(reconnectAttempts);
      clearReconnectTimer();
      const jitter = Math.random() * 0.3 * reconnectInterval;
      const delay = reconnectInterval + jitter;
      reconnectTimer = setTimeout(connect, delay);
    }
  };

  const connect = () => {
    if (eventSource) {
      eventSource.close();
    }

    const fullUrl = `${API_BASE_URL}${endpoint}`;
    const token = getAuthToken();

    const url = token
      ? `${fullUrl}${fullUrl.includes('?') ? '&' : '?'}token=${encodeURIComponent(token)}`
      : fullUrl;

    try {
      eventSource = new EventSource(url);
    } catch (err) {
      console.error('Failed to create EventSource:', err);
      scheduleReconnect();
      return;
    }

    eventSource.onopen = () => {
      isConnected = true;
      reconnectAttempts = 0;
      onOpen?.();
    };

    eventSource.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data);
        const data = parsed.data ?? parsed;
        const sequence = typeof parsed.sequence === 'number' ? parsed.sequence : null;
        const data_age_ms = typeof parsed.data_age_ms === 'number' ? parsed.data_age_ms : null;
        const sseEvent: SSEEvent<T> = {
          type: event.type || 'message',
          event: parsed.event || event.type || 'message',
          data,
          timestamp: Date.now(),
          eventId: event.lastEventId || undefined,
          sequence,
          data_age_ms,
        };
        onMessage?.(sseEvent);
      } catch (err) {
        console.error('Failed to parse SSE message:', err, event.data);
      }
    };

    eventSource.addEventListener('quote', ((ev: MessageEvent<string>) => {
      try {
        const parsed = JSON.parse(ev.data);
        const data = parsed.data ?? parsed;
        const sequence = typeof parsed.sequence === 'number' ? parsed.sequence : null;
        const data_age_ms = typeof parsed.data_age_ms === 'number' ? parsed.data_age_ms : null;
        const sseEvent: SSEEvent<T> = {
          type: 'quote',
          event: parsed.event || 'quote',
          data,
          timestamp: Date.now(),
          eventId: ev.lastEventId || undefined,
          sequence,
          data_age_ms,
        };
        onMessage?.(sseEvent);
      } catch (err) {
        console.error('Failed to parse SSE quote event:', err, ev.data);
      }
    }) as EventListener);

    eventSource.addEventListener('intraday', ((ev: MessageEvent<string>) => {
      try {
        const parsed = JSON.parse(ev.data);
        const data = parsed.data ?? parsed;
        const sequence = typeof parsed.sequence === 'number' ? parsed.sequence : null;
        const data_age_ms = typeof parsed.data_age_ms === 'number' ? parsed.data_age_ms : null;
        const sseEvent: SSEEvent<T> = {
          type: 'intraday',
          event: parsed.event || 'intraday',
          data,
          timestamp: Date.now(),
          eventId: ev.lastEventId || undefined,
          sequence,
          data_age_ms,
        };
        onMessage?.(sseEvent);
      } catch (err) {
        console.error('Failed to parse SSE intraday event:', err, ev.data);
      }
    }) as EventListener);

    eventSource.addEventListener('market_pulse', ((ev: MessageEvent<string>) => {
      try {
        const parsed = JSON.parse(ev.data);
        const data = parsed.data ?? parsed;
        const sequence = typeof parsed.sequence === 'number' ? parsed.sequence : null;
        const data_age_ms = typeof parsed.data_age_ms === 'number' ? parsed.data_age_ms : null;
        const sseEvent: SSEEvent<T> = {
          type: 'market_pulse',
          event: parsed.event || 'market_pulse',
          data,
          timestamp: Date.now(),
          eventId: ev.lastEventId || undefined,
          sequence,
          data_age_ms,
        };
        onMessage?.(sseEvent);
      } catch (err) {
        console.error('Failed to parse SSE market_pulse event:', err, ev.data);
      }
    }) as EventListener);

    eventSource.addEventListener('score_delta', ((ev: MessageEvent<string>) => {
      try {
        const parsed = JSON.parse(ev.data);
        const data = parsed.data ?? parsed;
        const sequence = typeof parsed.sequence === 'number' ? parsed.sequence : null;
        const data_age_ms = typeof parsed.data_age_ms === 'number' ? parsed.data_age_ms : null;
        const sseEvent: SSEEvent<T> = {
          type: 'score_delta',
          event: parsed.event || 'score_delta',
          data,
          timestamp: Date.now(),
          eventId: ev.lastEventId || undefined,
          sequence,
          data_age_ms,
        };
        onMessage?.(sseEvent);
      } catch (err) {
        console.error('Failed to parse SSE score_delta event:', err, ev.data);
      }
    }) as EventListener);

    eventSource.addEventListener('news_item', ((ev: MessageEvent<string>) => {
      try {
        const parsed = JSON.parse(ev.data);
        const data = parsed.data ?? parsed;
        const sequence = typeof parsed.sequence === 'number' ? parsed.sequence : null;
        const data_age_ms = typeof parsed.data_age_ms === 'number' ? parsed.data_age_ms : null;
        const sseEvent: SSEEvent<T> = {
          type: 'news_item',
          event: parsed.event || 'news_item',
          data,
          timestamp: Date.now(),
          eventId: ev.lastEventId || undefined,
          sequence,
          data_age_ms,
        };
        onMessage?.(sseEvent);
      } catch (err) {
        console.error('Failed to parse SSE news_item event:', err, ev.data);
      }
    }) as EventListener);

    eventSource.addEventListener('health', ((ev: MessageEvent<string>) => {
      try {
        const parsed = JSON.parse(ev.data);
        const data = parsed.data ?? parsed;
        const sequence = typeof parsed.sequence === 'number' ? parsed.sequence : null;
        const data_age_ms = typeof parsed.data_age_ms === 'number' ? parsed.data_age_ms : null;
        const sseEvent: SSEEvent<T> = {
          type: 'health',
          event: parsed.event || 'health',
          data,
          timestamp: Date.now(),
          eventId: ev.lastEventId || undefined,
          sequence,
          data_age_ms,
        };
        onMessage?.(sseEvent);
      } catch (err) {
        console.error('Failed to parse SSE health event:', err, ev.data);
      }
    }) as EventListener);

    eventSource.addEventListener('ping', ((ev: MessageEvent<string>) => {
      try {
        const parsed = ev.data ? JSON.parse(ev.data) : {};
        const data = parsed.data ?? {};
        const sequence = typeof parsed.sequence === 'number' ? parsed.sequence : null;
        const data_age_ms = typeof parsed.data_age_ms === 'number' ? parsed.data_age_ms : null;
        const sseEvent: SSEEvent<T> = {
          type: 'ping',
          event: parsed.event || 'ping',
          data,
          timestamp: Date.now(),
          eventId: ev.lastEventId || undefined,
          sequence,
          data_age_ms,
        };
        onMessage?.(sseEvent);
      } catch {
        const sseEvent: SSEEvent<T> = {
          type: 'ping',
          event: 'ping',
          data: {} as T,
          timestamp: Date.now(),
          sequence: null,
          data_age_ms: null,
        };
        onMessage?.(sseEvent);
      }
    }) as EventListener);

    eventSource.onerror = (error) => {
      const wasConnected = isConnected;
      isConnected = false;
      onError?.(error);

      if (wasConnected) {
        onDisconnect?.();
      }

      eventSource?.close();
      scheduleReconnect();
    };
  };

  connect();

  const connection: SSEConnection = {
    get eventSource() {
      return eventSource;
    },
    disconnect: () => {
      clearReconnectTimer();
      eventSource?.close();
      eventSource = null;
      if (isConnected) {
        isConnected = false;
        onDisconnect?.();
      }
      activeConnections.delete(key);
    },
    reconnect: () => {
      clearReconnectTimer();
      reconnectAttempts = 0;
      connect();
    },
    get isConnected() {
      return isConnected;
    },
  };

  activeConnections.set(key, connection);
  return connection;
}

export function disconnectSSE(key: string): void {
  const connection = activeConnections.get(key);
  if (connection) {
    connection.disconnect();
  }
}

export function disconnectAllSSE(): void {
  activeConnections.forEach((conn) => conn.disconnect());
  activeConnections.clear();
}

export function getSSEConnection(key: string): SSEConnection | undefined {
  return activeConnections.get(key);
}

export function isSSEConnected(key: string): boolean {
  return activeConnections.get(key)?.isConnected ?? false;
}

export function getActiveConnectionKeys(): string[] {
  return Array.from(activeConnections.keys());
}
