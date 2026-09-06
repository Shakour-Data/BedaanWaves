import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act, cleanup } from '@testing-library/react'
import { useSSE } from '@/hooks/useSSE'
import { disconnectAllSSE, getActiveConnectionKeys } from '@/lib/sse'

interface MockES {
  readyState: number
  url: string
  mockOpen(): void
  mockEmit(event: string, payload: Record<string, unknown>): void
  mockError(): void
  mockClose(): void
}

interface TestGlobals {
  __getMockEventSources: () => MockES[]
  __clearMockEventSources: () => void
}

function getTestGlobals(): TestGlobals {
  return globalThis as unknown as TestGlobals
}

function getLastMockES(): MockES {
  const list = getTestGlobals().__getMockEventSources()
  return list[list.length - 1]
}

describe('hooks/useSSE.ts', () => {
  beforeEach(() => {
    disconnectAllSSE()
    getTestGlobals().__clearMockEventSources()
    cleanup()
  })

  describe('onMessage sets latest data', () => {
    it('data state updates after SSE onmessage', () => {
      const { result } = renderHook(() =>
        useSSE<{ price: number }>('useSSE-test:data', '/stream-q', { reconnect: false })
      )

      expect(result.current.data).toBeNull()
      expect(result.current.isConnected).toBe(false)

      const es = getLastMockES()
      act(() => {
        es.mockOpen()
      })
      expect(result.current.isConnected).toBe(true)

      act(() => {
        es.mockEmit('message', {
          event: 'quote',
          sequence: 1,
          data: { price: 100.5 },
        })
      })

      expect(result.current.data).toEqual({ price: 100.5 })
      expect(result.current.events.length).toBe(1)
      expect(result.current.events[0].sequence).toBe(1)
    })

    it('quote event updates data via addEventListener path', () => {
      const { result } = renderHook(() =>
        useSSE<{ price: number }>('useSSE-test:quote', '/stream-q', { reconnect: false })
      )

      const es = getLastMockES()
      act(() => es.mockOpen())

      act(() => {
        es.mockEmit('quote', {
          event: 'quote',
          sequence: 10,
          data_age_ms: 50,
          data: { price: 200 },
        })
      })

      expect(result.current.data).toEqual({ price: 200 })
      expect(result.current.events[0].type).toBe('quote')
      expect(result.current.events[0].data_age_ms).toBe(50)
    })
  })

  describe('onError propagates', () => {
    it('error state is set and isConnected false after onerror', () => {
      const onErrorCb = vi.fn()
      const { result } = renderHook(() =>
        useSSE<{ v: number }>('useSSE-test:err', '/stream-e', {
          reconnect: false,
          onError: onErrorCb,
        })
      )

      const es = getLastMockES()
      act(() => es.mockOpen())
      expect(result.current.isConnected).toBe(true)

      act(() => es.mockError())

      expect(result.current.isConnected).toBe(false)
      expect(result.current.error).not.toBeNull()
      expect(onErrorCb).toHaveBeenCalled()
    })
  })

  describe('disconnect hook cleanup', () => {
    it('unmount disconnects and removes from activeConnections', () => {
      const onDisconnectCb = vi.fn()
      const { unmount } = renderHook(() =>
        useSSE<{ v: number }>('useSSE-test:cleanup', '/stream-c', {
          reconnect: false,
          onDisconnect: onDisconnectCb,
        })
      )

      expect(getActiveConnectionKeys()).toContain('useSSE-test:cleanup')

      const es = getLastMockES()
      act(() => es.mockOpen())

      unmount()

      expect(getActiveConnectionKeys()).not.toContain('useSSE-test:cleanup')
      expect(onDisconnectCb).toHaveBeenCalled()
    })

    it('explicit disconnect() action works', () => {
      const { result } = renderHook(() =>
        useSSE<{ v: number }>('useSSE-test:discall', '/stream-d', { reconnect: false })
      )

      const es = getLastMockES()
      act(() => es.mockOpen())

      expect(getActiveConnectionKeys()).toContain('useSSE-test:discall')
      expect(result.current.isConnected).toBe(true)

      act(() => {
        result.current.disconnect()
      })

      expect(getActiveConnectionKeys()).not.toContain('useSSE-test:discall')
      expect(result.current.isConnected).toBe(false)
    })
  })

  describe('reconnect action', () => {
    it('reconnect() creates new EventSource', () => {
      const { result } = renderHook(() =>
        useSSE<{ v: number }>('useSSE-test:reconnect', '/stream-r', { reconnect: false })
      )

      const countBefore = getTestGlobals().__getMockEventSources().length
      act(() => {
        result.current.reconnect()
      })
      const countAfter = getTestGlobals().__getMockEventSources().length
      expect(countAfter).toBeGreaterThan(countBefore)
    })
  })

  describe('clearEvents action', () => {
    it('clearEvents empties events array', () => {
      const { result } = renderHook(() =>
        useSSE<{ v: number }>('useSSE-test:clear', '/stream-c', { reconnect: false })
      )

      const es = getLastMockES()
      act(() => es.mockOpen())
      act(() => es.mockEmit('message', { sequence: 1, data: { v: 1 } }))
      act(() => es.mockEmit('message', { sequence: 2, data: { v: 2 } }))

      expect(result.current.events.length).toBe(2)

      act(() => {
        result.current.clearEvents()
      })

      expect(result.current.events.length).toBe(0)
    })
  })
})
