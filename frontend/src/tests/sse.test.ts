import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  createSSEConnection,
  disconnectSSE,
  getActiveConnectionKeys,
  getSSEConnection,
  disconnectAllSSE,
} from '@/lib/sse'

function getLastMockES(): any {
  const list = (globalThis as any).__getMockEventSources()
  return list[list.length - 1]
}

describe('lib/sse.ts', () => {
  beforeEach(() => {
    disconnectAllSSE()
    ;(globalThis as any).__clearMockEventSources()
  })

  afterEach(() => {
    disconnectAllSSE()
  })

  describe('reconnect attempts with jitter exponential backoff', () => {
    it('advancing 5s intervals triggers N reconnections after error', () => {
      const reconnectSpy = vi.fn()
      const onOpenSpy = vi.fn()

      const conn = createSSEConnection('sse-test:reconnect', {
        endpoint: '/stream',
        reconnect: true,
        reconnectInterval: 5_000,
        maxReconnectAttempts: 5,
        onReconnect: reconnectSpy,
        onOpen: onOpenSpy,
      })

      const es1 = getLastMockES()
      expect(es1.readyState).toBe(0)

      es1.mockOpen()
      expect(onOpenSpy).toHaveBeenCalledTimes(1)
      expect(conn.isConnected).toBe(true)

      es1.mockError()
      expect(conn.isConnected).toBe(false)
      expect(reconnectSpy).toHaveBeenCalledTimes(1)
      expect(reconnectSpy).toHaveBeenLastCalledWith(1)

      const initialCount = (globalThis as any).__getMockEventSources().length

      for (let i = 1; i <= 3; i++) {
        vi.advanceTimersByTime(5_000 + 2_000)
        const sourcesAfter = (globalThis as any).__getMockEventSources()
        expect(sourcesAfter.length).toBe(initialCount + i)
        const newEs = sourcesAfter[sourcesAfter.length - 1]
        newEs.mockError()
      }

      expect(reconnectSpy).toHaveBeenCalledTimes(4)

      conn.disconnect()
    })

    it('maxReconnectAttempts stops further reconnection scheduling', () => {
      const reconnectSpy = vi.fn()
      const onDisconnectSpy = vi.fn()

      const conn = createSSEConnection('sse-test:max-attempts', {
        endpoint: '/stream',
        reconnect: true,
        reconnectInterval: 5_000,
        maxReconnectAttempts: 2,
        onReconnect: reconnectSpy,
        onDisconnect: onDisconnectSpy,
      })

      let es = getLastMockES()
      es.mockOpen()
      es.mockError()
      expect(reconnectSpy).toHaveBeenCalledWith(1)

      vi.advanceTimersByTime(10_000)
      es = getLastMockES()
      es.mockError()
      expect(reconnectSpy).toHaveBeenCalledWith(2)

      const countBefore = (globalThis as any).__getMockEventSources().length
      vi.advanceTimersByTime(30_000)
      const countAfter = (globalThis as any).__getMockEventSources().length
      expect(countAfter).toBeLessThanOrEqual(countBefore + 1)

      conn.disconnect()
    })
  })

  describe('disconnect removes from activeConnections', () => {
    it('disconnect() deletes key from activeConnections map', () => {
      const conn = createSSEConnection('sse-test:disconnect', {
        endpoint: '/stream',
        reconnect: false,
      })

      expect(getActiveConnectionKeys()).toContain('sse-test:disconnect')
      expect(getSSEConnection('sse-test:disconnect')).toBe(conn)

      conn.disconnect()

      expect(getActiveConnectionKeys()).not.toContain('sse-test:disconnect')
      expect(getSSEConnection('sse-test:disconnect')).toBeUndefined()
    })

    it('disconnectSSE() helper deletes key', () => {
      createSSEConnection('sse-test:disconnect-helper', {
        endpoint: '/stream',
        reconnect: false,
      })

      expect(getActiveConnectionKeys()).toContain('sse-test:disconnect-helper')
      disconnectSSE('sse-test:disconnect-helper')
      expect(getActiveConnectionKeys()).not.toContain('sse-test:disconnect-helper')
    })
  })

  describe('same key reused -> first disconnected', () => {
    it('two createSSEConnection with same key disconnects the first', () => {
      const onDisconnectA = vi.fn()
      const onOpenA = vi.fn()

      const connA = createSSEConnection('sse-test:same-key', {
        endpoint: '/stream-a',
        reconnect: false,
        onDisconnect: onDisconnectA,
        onOpen: onOpenA,
      })

      const esA = getLastMockES()
      esA.mockOpen()
      expect(onOpenA).toHaveBeenCalledTimes(1)
      expect(connA.isConnected).toBe(true)

      const onOpenB = vi.fn()
      const onDisconnectB = vi.fn()
      const connB = createSSEConnection('sse-test:same-key', {
        endpoint: '/stream-b',
        reconnect: false,
        onOpen: onOpenB,
        onDisconnect: onDisconnectB,
      })

      expect(onDisconnectA).toHaveBeenCalledTimes(1)
      expect(connA.isConnected).toBe(false)

      const esB = getLastMockES()
      esB.mockOpen()
      expect(onOpenB).toHaveBeenCalledTimes(1)
      expect(connB.isConnected).toBe(true)

      expect(getSSEConnection('sse-test:same-key')).toBe(connB)

      connB.disconnect()
    })
  })

  describe('onMessage parses typed envelopes', () => {
    it('receives quote event via addEventListener path', () => {
      const messages: any[] = []
      const conn = createSSEConnection<{ price: number }>('sse-test:quote', {
        endpoint: '/stream',
        reconnect: false,
        onMessage: (ev) => messages.push(ev),
      })

      const es = getLastMockES()
      es.mockOpen()

      es.mockEmit('quote', {
        event: 'quote',
        sequence: 42,
        data_age_ms: 150,
        data: { price: 123.45 },
      })

      expect(messages.length).toBe(1)
      expect(messages[0].type).toBe('quote')
      expect(messages[0].event).toBe('quote')
      expect(messages[0].sequence).toBe(42)
      expect(messages[0].data_age_ms).toBe(150)
      expect(messages[0].data).toEqual({ price: 123.45 })

      conn.disconnect()
    })

    it('message event (default onmessage) parses envelope', () => {
      const messages: any[] = []
      const conn = createSSEConnection<{ v: number }>('sse-test:msg', {
        endpoint: '/stream',
        reconnect: false,
        onMessage: (ev) => messages.push(ev),
      })

      const es = getLastMockES()
      es.mockOpen()
      es.mockEmit('message', { sequence: 3, data: { v: 9 } })

      expect(messages[0].sequence).toBe(3)
      expect(messages[0].data).toEqual({ v: 9 })

      conn.disconnect()
    })
  })
})
