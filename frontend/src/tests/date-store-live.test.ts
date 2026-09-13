import { describe, it, expect, beforeEach, beforeAll } from 'vitest'
import { useDateStore } from '@/store/useDateStore'

beforeAll(async () => {
  vi.useRealTimers()
  try { localStorage.removeItem('date-storage') } catch {}
  const p = (useDateStore as any).persist
  if (p) {
    if (typeof p.rehydrate === 'function') {
      try { await p.rehydrate() } catch {}
    }
    if (typeof p.onFinishHydration === 'function' && typeof p.hasHydrated === 'function' && !p.hasHydrated()) {
      await new Promise<void>((resolve) => {
        const unsub = p.onFinishHydration(() => { try { unsub() } catch {}; resolve() })
        setTimeout(() => { try { unsub() } catch {}; resolve() }, 1500)
      })
    }
  }
  await new Promise((r) => setTimeout(r, 50))
  useDateStore.getState().reset()
  vi.useFakeTimers()
})

describe('store/useDateStore.ts — TR9.2 live tick driver', () => {
  beforeEach(async () => {
    useDateStore.getState().reset()
    for (let i = 0; i < 5; i++) await Promise.resolve()
    while (useDateStore.getState().selectedDate !== null || useDateStore.getState().useLatestDate !== true) {
      useDateStore.setState({ selectedDate: null, latestAvailableDate: null, useLatestDate: true })
      for (let i = 0; i < 5; i++) await Promise.resolve()
      break
    }
  })

  describe('TR9.2 — useLatestDate=true mode responds to stream ticks', () => {
    it('setLiveLatestFromStream with ISO timestamp updates getEffectiveDate', () => {
      const store = useDateStore.getState()
      expect(store.useLatestDate).toBe(true)
      expect(typeof store.setLiveLatestFromStream).toBe('function')

      store.setLiveLatestFromStream('2026-09-06T12:00:00Z')
      const s = useDateStore.getState()

      expect(s.latestAvailableDate).toBe('2026-09-06')
      expect(s.selectedDate).toBe('2026-09-06')
      expect(s.getEffectiveDate()).toBe('2026-09-06')
    })

    it('toggle useLatestDate=false then setLiveLatestFromStream → selectedDate untouched', () => {
      useDateStore.getState().setSelectedDate('2026-08-15')
      const afterSet = useDateStore.getState()
      expect(afterSet.useLatestDate).toBe(false)
      expect(afterSet.selectedDate).toBe('2026-08-15')
      expect(afterSet.latestAvailableDate).toBeNull()

      afterSet.setLiveLatestFromStream('2026-09-06T12:00:00Z')
      const s = useDateStore.getState()

      expect(s.latestAvailableDate).toBe('2026-09-06')
      expect(s.selectedDate).toBe('2026-08-15')
      expect(s.getEffectiveDate()).toBe('2026-08-15')
    })

    it('date-only input (no T) still works', () => {
      useDateStore.getState().setLiveLatestFromStream('2026-07-04')
      const s = useDateStore.getState()
      expect(s.latestAvailableDate).toBe('2026-07-04')
      expect(s.getEffectiveDate()).toBe('2026-07-04')
    })

    it('same date twice does not trigger re-render churn (idempotent)', () => {
      const store = useDateStore.getState()
      store.setLiveLatestFromStream('2026-09-06T00:00:00Z')
      const firstSelected = useDateStore.getState().selectedDate
      store.setLiveLatestFromStream('2026-09-06T23:59:59Z')
      const s = useDateStore.getState()
      expect(s.selectedDate).toBe(firstSelected)
      expect(s.latestAvailableDate).toBe('2026-09-06')
    })

    it('switching useLatestDate back to true picks up latestAvailableDate', () => {
      useDateStore.getState().setSelectedDate('2026-01-01')
      const afterSel = useDateStore.getState()
      expect(afterSel.useLatestDate).toBe(false)

      afterSel.setLiveLatestFromStream('2026-12-25T10:00:00Z')
      const afterStream = useDateStore.getState()
      expect(afterStream.getEffectiveDate()).toBe('2026-01-01')

      afterStream.setUseLatestDate(true)
      const s = useDateStore.getState()
      expect(s.useLatestDate).toBe(true)
      expect(s.selectedDate).toBe('2026-12-25')
      expect(s.getEffectiveDate()).toBe('2026-12-25')
    })

    it('setLiveLatestFromStream with empty input is no-op', () => {
      useDateStore.getState().setLiveLatestFromStream('')
      const s = useDateStore.getState()
      expect(s.latestAvailableDate).toBeNull()
      expect(s.selectedDate).toBeNull()
    })
  })
})
