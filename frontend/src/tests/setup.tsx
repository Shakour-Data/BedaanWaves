/// <reference types="vitest/globals" />
import '@testing-library/jest-dom'

type EventSourceReadyState = 0 | 1 | 2

interface AttachSpy {
  onopen: () => ReturnType<typeof vi.fn>
  onmessage: () => ReturnType<typeof vi.fn>
  onerror: () => ReturnType<typeof vi.fn>
}

class MockEventSource {
  url: string
  withCredentials: boolean = false
  readyState: EventSourceReadyState = 0
  CONNECTING: EventSourceReadyState = 0
  OPEN: EventSourceReadyState = 1
  CLOSED: EventSourceReadyState = 2

  onopen: ((ev: Event) => any) | null = null
  onmessage: ((ev: MessageEvent) => any) | null = null
  onerror: ((ev: Event) => any) | null = null

  private _listeners: Map<string, Set<EventListener>> = new Map()

  constructor(url: string | URL, _eventSourceInitDict?: EventSourceInit) {
    this.url = typeof url === 'string' ? url : url.toString()
    this.readyState = this.CONNECTING
    ;(globalThis as any).__mockEventSources = (globalThis as any).__mockEventSources ?? []
    ;(globalThis as any).__mockEventSources.push(this)
  }

  mockOpen(): void {
    this.readyState = this.OPEN
    const ev = new Event('open')
    this.onopen?.(ev)
    this._listeners.get('open')?.forEach((l) => l(ev))
  }

  mockEmit(
    eventType: string,
    payloadObj: Record<string, any>,
    opts: { lastEventId?: string; delayMs?: number } = {}
  ): void {
    const fire = () => {
      const data = typeof payloadObj === 'string' ? payloadObj : JSON.stringify(payloadObj)
      const ev = new MessageEvent(eventType, {
        data,
        lastEventId: opts.lastEventId ?? String(payloadObj?.sequence ?? ''),
      })
      if (eventType === 'message') {
        this.onmessage?.(ev)
      }
      this._listeners.get(eventType)?.forEach((l) => l(ev as any))
      this._listeners.get('message')?.forEach((l) => l(ev as any))
    }
    if (opts.delayMs) {
      setTimeout(fire, opts.delayMs)
    } else {
      fire()
    }
  }

  mockError(): void {
    const ev = new Event('error')
    this.onerror?.(ev)
    this._listeners.get('error')?.forEach((l) => l(ev))
  }

  mockClose(): void {
    this.readyState = this.CLOSED
  }

  addEventListener(type: string, listener: EventListener, _options?: any): void {
    if (!this._listeners.has(type)) {
      this._listeners.set(type, new Set())
    }
    this._listeners.get(type)!.add(listener)
  }

  removeEventListener(type: string, listener: EventListener, _options?: any): void {
    this._listeners.get(type)?.delete(listener)
  }

  dispatchEvent(event: Event): boolean {
    this._listeners.get(event.type)?.forEach((l) => l(event))
    return !event.defaultPrevented
  }

  close(): void {
    this.readyState = this.CLOSED
  }

  attachSpy(): AttachSpy {
    const openFn = vi.fn()
    const msgFn = vi.fn()
    const errFn = vi.fn()
    const prevOpen = this.onopen
    const prevMsg = this.onmessage
    const prevErr = this.onerror
    this.onopen = (ev) => {
      openFn(ev)
      prevOpen?.(ev)
    }
    this.onmessage = (ev) => {
      msgFn(ev)
      prevMsg?.(ev)
    }
    this.onerror = (ev) => {
      errFn(ev)
      prevErr?.(ev)
    }
    return {
      onopen: () => openFn,
      onmessage: () => msgFn,
      onerror: () => errFn,
    }
  }
}

;(globalThis as any).EventSource = MockEventSource
;(globalThis as any).__getMockEventSources = () => (globalThis as any).__mockEventSources ?? []
;(globalThis as any).__clearMockEventSources = () => {
  ;(globalThis as any).__mockEventSources = []
}

beforeEach(() => {
  ;(globalThis as any).__clearMockEventSources()
})

afterEach(() => {
  vi.restoreAllMocks()
})
