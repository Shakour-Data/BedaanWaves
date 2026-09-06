import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act, cleanup } from '@testing-library/react'
import { useLiveData, type LiveStreamKey, type ConnectionHealth } from '@/hooks/useLiveData'
import {
  disconnectAllSSE,
  getActiveConnectionKeys,
  getSSEConnection,
} from '@/lib/sse'
import { useLiveStore, STALE_THRESHOLD_MS } from '@/store/useLiveStore'
import * as apiModule from '@/lib/api'

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

function getAllMockES(): MockES[] {
  return getTestGlobals().__getMockEventSources() ?? []
}

async function flushAll(ticks = 12, timerMs = 100) {
  for (let i = 0; i < ticks; i++) {
    for (let j = 0; j < 5; j++) {
      await Promise.resolve()
    }
    act(() => {
      vi.advanceTimersByTime(timerMs)
    })
    for (let j = 0; j < 5; j++) {
      await Promise.resolve()
    }
  }
}

describe('hooks/useLiveData.tsx', () => {
  let apiGetSpy: ReturnType<typeof vi.spyOn>

  beforeEach(() => {
    disconnectAllSSE()
    getTestGlobals().__clearMockEventSources()
    cleanup()
    useLiveStore.setState({ streams: {} })
    vi.useFakeTimers()

    apiGetSpy = vi
      .spyOn(apiModule.apiClient, 'get')
      .mockImplementation(async (url: string) => {
        return Promise.resolve({
          data: {
            event: 'snapshot',
            sequence: 100,
            data_age_ms: 120,
            data: { snapshotFromApi: true, url },
          },
          status: 200,
          statusText: 'OK',
          headers: {},
          config: {},
        } as unknown)
      })
  })

  afterEach(() => {
    apiGetSpy?.mockRestore()
    cleanup()
  })

  describe('TR7.1 — Gap detection triggers resync once', () => {
    it('sequence 1→2→6 (gap=5-2-1? gap=6-2-1=3>2) triggers snapshot GET once; baseline seq reset',
      { timeout: 20000 },
      async () => {
        const key: LiveStreamKey = 'quote:TR71'

        const { result } = renderHook(() => useLiveData<{ p: number }>(key, { enabled: true }))
        await flushAll(8, 200)

        const initCalls = apiGetSpy.mock.calls.filter((c) =>
          String(c[0]).includes('/live/quote/TR71/snapshot')
        )
        expect(initCalls.length).toBeGreaterThanOrEqual(1)
        apiGetSpy.mockClear()

        const es = getLastMockES()
        act(() => es.mockOpen())
        await flushAll(4)

        act(() =>
          es.mockEmit('quote', { event: 'quote', sequence: 1, data_age_ms: 50, data: { p: 1 } })
        )
        await flushAll()
        expect(result.current.lastSequence).toBe(1)

        act(() =>
          es.mockEmit('quote', { event: 'quote', sequence: 2, data_age_ms: 50, data: { p: 2 } })
        )
        await flushAll()
        expect(result.current.lastSequence).toBe(2)

        act(() =>
          es.mockEmit('quote', { event: 'quote', sequence: 6, data_age_ms: 50, data: { p: 6 } })
        )
        await flushAll(12, 500)

        expect(apiGetSpy).toHaveBeenCalledTimes(1)
        expect(String(apiGetSpy.mock.calls[0][0])).toContain('/live/quote/TR71/snapshot')

        const storeState = useLiveStore.getState().streams[key]
        expect(storeState?.lastSequence).toBe(100)
      }
    )

    it('gap exactly 2 (seq 1→4: gap=4-1-1=2) does NOT trigger resync',
      { timeout: 20000 },
      async () => {
        const key: LiveStreamKey = 'quote:TR71NOGAP'

        const { result } = renderHook(() => useLiveData<{ p: number }>(key, { enabled: true }))
        await flushAll(8, 200)
        expect(apiGetSpy).toHaveBeenCalled()
        apiGetSpy.mockClear()

        const es = getLastMockES()
        act(() => es.mockOpen())
        await flushAll(4)

        act(() =>
          es.mockEmit('quote', { event: 'quote', sequence: 1, data_age_ms: 10, data: { p: 1 } })
        )
        await flushAll()

        act(() =>
          es.mockEmit('quote', { event: 'quote', sequence: 4, data_age_ms: 10, data: { p: 4 } })
        )
        await flushAll(8, 200)

        expect(apiGetSpy).toHaveBeenCalledTimes(0)
        expect(result.current.lastSequence).toBe(4)
      }
    )
  })

  describe('TR7.2 — connectionHealth FSM transitions', () => {
    it('open→live→stale→onerror→reconnecting→3 failures→disconnected',
      { timeout: 30000 },
      async () => {
        const key: LiveStreamKey = 'market'
        const healthChanges: ConnectionHealth[] = []

        const { result } = renderHook(() =>
          useLiveData<{ tick: number }>(key, {
            enabled: true,
            onHealthChange: (h) => healthChanges.push(h),
          })
        )
        await flushAll(8, 200)
        apiGetSpy.mockClear()

        const es = getLastMockES()
        act(() => es.mockOpen())
        await flushAll(4, 600)
        expect(result.current.connectionHealth).toBe('live')

        act(() =>
          es.mockEmit('market_pulse', {
            event: 'market_pulse',
            sequence: 1,
            data_age_ms: 50,
            data: { tick: 1 },
          })
        )
        await flushAll()

        act(() => {
          vi.advanceTimersByTime(STALE_THRESHOLD_MS + 2_000)
        })
        await flushAll(6, 2_000)

        const foundStale =
          healthChanges.includes('stale') || result.current.connectionHealth === 'stale'
        expect(foundStale).toBe(true)

        act(() => es.mockError())
        await flushAll()

        const foundReconnecting =
          result.current.connectionHealth === 'reconnecting' ||
          healthChanges.includes('reconnecting')
        expect(foundReconnecting).toBe(true)

        for (let i = 0; i < 3; i++) {
          act(() => {
            vi.advanceTimersByTime(10_000)
          })
          await flushAll()
          const latest = getLastMockES()
          if (latest && latest !== es) {
            act(() => latest.mockError())
          } else {
            act(() => es.mockError())
          }
          await flushAll()
        }

        act(() => {
          vi.advanceTimersByTime(15_000)
        })
        await flushAll(8, 2_000)

        const disconnectedSeen =
          result.current.connectionHealth === 'disconnected' ||
          healthChanges.includes('disconnected')
        expect(disconnectedSeen).toBe(true)
      }
    )
  })

  describe('TR7.3 — Connection sharing across hook mounts', () => {
    it('two renderHook calls with same key share single activeConnections entry',
      { timeout: 30000 },
      async () => {
        const key: LiveStreamKey = 'scores'

        const h1 = renderHook(() => useLiveData(key, { enabled: true }))
        await flushAll(8, 200)
        expect(apiGetSpy).toHaveBeenCalled()
        expect(getActiveConnectionKeys()).toContain(key)

        const esCountBefore = getAllMockES().length

        const h2 = renderHook(() => useLiveData(key, { enabled: true }))
        await flushAll()

        expect(getActiveConnectionKeys().filter((k) => k === key)).toHaveLength(1)
        const conn = getSSEConnection(key)
        expect(conn).toBeDefined()
        expect(getAllMockES().length).toBe(esCountBefore)

        const es = getLastMockES()
        act(() => es.mockOpen())
        await flushAll()

        act(() =>
          es.mockEmit('score_delta', {
            event: 'score_delta',
            sequence: 7,
            data_age_ms: 10,
            data: { s: 90 },
          })
        )
        await flushAll(8)
        expect(h1.result.current.lastSequence).toBe(7)
        expect(h2.result.current.lastSequence).toBe(7)

        h1.unmount()
        await flushAll()
        expect(getActiveConnectionKeys()).toContain(key)

        h2.unmount()
        await flushAll()
        expect(getActiveConnectionKeys()).not.toContain(key)
      }
    )

    it('different keys use separate activeConnections entries',
      { timeout: 30000 },
      async () => {
        const k1: LiveStreamKey = 'quote:AAA'
        const k2: LiveStreamKey = 'quote:BBB'

        const h1 = renderHook(() => useLiveData(k1, { enabled: true }))
        await flushAll(8, 200)
        const afterK1 = apiGetSpy.mock.calls.length
        expect(afterK1).toBeGreaterThanOrEqual(1)

        const h2 = renderHook(() => useLiveData(k2, { enabled: true }))
        await flushAll(8, 200)
        expect(apiGetSpy.mock.calls.length).toBeGreaterThanOrEqual(2)

        const keys = getActiveConnectionKeys()
        expect(keys).toContain(k1)
        expect(keys).toContain(k2)
        expect(getSSEConnection(k1)).not.toBe(getSSEConnection(k2))

        h1.unmount()
        h2.unmount()
        await flushAll()

        expect(getActiveConnectionKeys()).not.toContain(k1)
        expect(getActiveConnectionKeys()).not.toContain(k2)
      }
    )
  })

  describe('latest and data fields populated from store', () => {
    it('latest reflects most recent emitted event data',
      { timeout: 20000 },
      async () => {
        const key: LiveStreamKey = 'news'
        const { result } = renderHook(() =>
          useLiveData<{ title: string }>(key, { enabled: true })
        )
        await flushAll(8, 200)
        expect(apiGetSpy).toHaveBeenCalled()

        const es = getLastMockES()
        act(() => es.mockOpen())
        await flushAll()

        act(() =>
          es.mockEmit('news_item', {
            event: 'news_item',
            sequence: 1,
            data_age_ms: 10,
            data: { title: 'first' },
          })
        )
        await flushAll()
        expect(result.current.latest).toEqual({ title: 'first' })

        act(() =>
          es.mockEmit('news_item', {
            event: 'news_item',
            sequence: 2,
            data_age_ms: 10,
            data: { title: 'second' },
          })
        )
        await flushAll()
        expect(result.current.latest).toEqual({ title: 'second' })
        expect(result.current.lastDataAgeMs).toBe(10)
      }
    )
  })
})
