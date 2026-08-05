import { useEffect, useRef, useState, useCallback } from 'react';
import { createSSEConnection, disconnectSSE, SSEEvent, SSEConnectionOptions } from '@/lib/sse';

export interface UseSSEReturn<T = unknown> {
  data: T | null;
  events: SSEEvent<T>[];
  isConnected: boolean;
  error: Event | null;
  reconnect: () => void;
  disconnect: () => void;
  clearEvents: () => void;
}

export function useSSE<T = unknown>(
  key: string,
  endpoint: string,
  options?: Omit<SSEConnectionOptions<T>, 'endpoint'>
): UseSSEReturn<T> {
  const [data, setData] = useState<T | null>(null);
  const [events, setEvents] = useState<SSEEvent<T>[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Event | null>(null);
  const connectionRef = useRef<ReturnType<typeof createSSEConnection<T>> | null>(null);
  const optionsRef = useRef(options);

  optionsRef.current = options;

  const handleMessage = useCallback((event: SSEEvent<T>) => {
    setData(event.data);
    setEvents((prev) => [...prev.slice(-99), event]);
  }, []);

  const handleOpen = useCallback(() => {
    setIsConnected(true);
    setError(null);
    optionsRef.current?.onOpen?.();
  }, []);

  const handleError = useCallback((err: Event) => {
    setIsConnected(false);
    setError(err);
    optionsRef.current?.onError?.(err);
  }, []);

  useEffect(() => {
    connectionRef.current = createSSEConnection<T>(key, {
      endpoint,
      onMessage: handleMessage,
      onOpen: handleOpen,
      onError: handleError,
      reconnect: options?.reconnect ?? true,
      reconnectInterval: options?.reconnectInterval ?? 5000,
      maxReconnectAttempts: options?.maxReconnectAttempts ?? 10,
      headers: options?.headers,
    });

    return () => {
      connectionRef.current?.disconnect();
      connectionRef.current = null;
    };
  }, [key, endpoint, handleMessage, handleOpen, handleError, options?.reconnect, options?.reconnectInterval, options?.maxReconnectAttempts, options?.headers]);

  const reconnect = useCallback(() => {
    connectionRef.current?.reconnect();
  }, []);

  const disconnect = useCallback(() => {
    disconnectSSE(key);
    connectionRef.current = null;
    setIsConnected(false);
  }, [key]);

  const clearEvents = useCallback(() => {
    setEvents([]);
  }, []);

  return {
    data,
    events,
    isConnected,
    error,
    reconnect,
    disconnect,
    clearEvents,
  };
}

export function useSSELatest<T = unknown>(
  key: string,
  endpoint: string,
  options?: Omit<SSEConnectionOptions<T>, 'endpoint'>
): T | null {
  const { data } = useSSE<T>(key, endpoint, options);
  return data;
}