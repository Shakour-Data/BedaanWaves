export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:3000/api/v1";

export interface SSEEvent<T = unknown> {
  type: string;
  data: T;
  timestamp: number;
  eventId?: string;
}

export interface SSEConnectionOptions<T = unknown> {
  endpoint: string;
  onMessage?: (event: SSEEvent<T>) => void;
  onError?: (error: Event) => void;
  onOpen?: () => void;
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

let activeConnections: Map<string, SSEConnection> = new Map();

function getAuthHeaders(): Record<string, string> {
  const token = typeof window !== 'undefined' 
    ? localStorage.getItem('access_token') 
    : '';
  return token ? { Authorization: `Bearer ${token}` } : {};
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
    reconnect = true,
    reconnectInterval = 5000,
    maxReconnectAttempts = 10,
  } = options;

  let eventSource: EventSource | null = null;
  let reconnectAttempts = 0;
  let isConnected = false;

  const connect = () => {
    if (eventSource) {
      eventSource.close();
    }

    const fullUrl = `${API_BASE_URL}${endpoint}`;
    const headers = { ...getAuthHeaders(), ...options.headers };

    const params = new URLSearchParams();
    Object.entries(headers).forEach(([key, value]) => {
      params.append(key, value);
    });

    const urlWithAuth = `${fullUrl}?${params.toString()}`;

    try {
      eventSource = new EventSource(urlWithAuth);
    } catch (err) {
      console.error('Failed to create EventSource:', err);
      if (reconnect && reconnectAttempts < maxReconnectAttempts) {
        setTimeout(connect, reconnectInterval);
        reconnectAttempts++;
      }
      return;
    }

    eventSource.onopen = () => {
      isConnected = true;
      reconnectAttempts = 0;
      onOpen?.();
    };

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        const sseEvent: SSEEvent<T> = {
          type: event.type || 'message',
          data: data.data ?? data,
          timestamp: Date.now(),
          eventId: event.lastEventId || undefined,
        };
        onMessage?.(sseEvent);
      } catch (err) {
        console.error('Failed to parse SSE message:', err, event.data);
      }
    };

    eventSource.onerror = (error) => {
      isConnected = false;
      onError?.(error);
      
      if (reconnect && reconnectAttempts < maxReconnectAttempts) {
        eventSource?.close();
        setTimeout(connect, reconnectInterval);
        reconnectAttempts++;
      }
    };
  };

  connect();

  const connection: SSEConnection = {
    get eventSource() {
      return eventSource;
    },
    disconnect: () => {
      eventSource?.close();
      eventSource = null;
      isConnected = false;
      activeConnections.delete(key);
    },
    reconnect: () => {
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