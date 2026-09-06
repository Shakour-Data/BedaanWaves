/// <reference types="vitest/globals" />
import '@testing-library/jest-dom'

type EventSourceReadyState = 0 | 1 | 2

interface AttachSpy {
  onopen: () => ReturnType<typeof vi.fn>
  onmessage: () => ReturnType<typeof vi.fn>
  onerror: () => ReturnType<typeof vi.fn>
}

interface TestGlobals {
  EventSource: typeof MockEventSource
  __mockEventSources: MockEventSource[]
  __getMockEventSources: () => MockEventSource[]
  __clearMockEventSources: () => void
}

function getTestGlobals(): TestGlobals {
  return globalThis as unknown as TestGlobals
}

class MockEventSource {
  url: string
  withCredentials: boolean = false
  readyState: EventSourceReadyState = 0
  CONNECTING: EventSourceReadyState = 0
  OPEN: EventSourceReadyState = 1
  CLOSED: EventSourceReadyState = 2

  onopen: ((ev: Event) => void) | null = null
  onmessage: ((ev: MessageEvent) => void) | null = null
  onerror: ((ev: Event) => void) | null = null

  private _listeners: Map<string, Set<EventListener>> = new Map()

  constructor(url: string | URL) {
    this.url = typeof url === 'string' ? url : url.toString()
    this.readyState = this.CONNECTING
    const g = getTestGlobals()
    g.__mockEventSources = g.__mockEventSources ?? []
    g.__mockEventSources.push(this)
  }

  mockOpen(): void {
    this.readyState = this.OPEN
    const ev = new Event('open')
    this.onopen?.(ev)
    this._listeners.get('open')?.forEach((l) => l(ev))
  }

  mockEmit(
    eventType: string,
    payloadObj: Record<string, unknown>,
    opts: { lastEventId?: string; delayMs?: number } = {}
  ): void {
    const fire = () => {
      const data = typeof payloadObj === 'string' ? payloadObj : JSON.stringify(payloadObj)
      const ev = new MessageEvent(eventType, {
        data,
        lastEventId: opts.lastEventId ?? String((payloadObj as Record<string, unknown>).sequence ?? ''),
      })
      if (eventType === 'message') {
        this.onmessage?.(ev)
      }
      this._listeners.get(eventType)?.forEach((l) => l(ev))
      this._listeners.get('message')?.forEach((l) => l(ev))
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

  addEventListener(type: string, listener: EventListener, _options?: boolean | AddEventListenerOptions): void {
    void _options;
    if (!this._listeners.has(type)) {
      this._listeners.set(type, new Set())
    }
    this._listeners.get(type)!.add(listener)
  }

  removeEventListener(type: string, listener: EventListener, _options?: boolean | AddEventListenerOptions): void {
    void _options;
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

const g = getTestGlobals()
g.EventSource = MockEventSource
g.__getMockEventSources = () => g.__mockEventSources ?? []
g.__clearMockEventSources = () => {
  g.__mockEventSources = []
}

beforeEach(() => {
  g.__clearMockEventSources()
})

afterEach(() => {
  vi.restoreAllMocks()
})
