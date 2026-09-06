import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { useEffect } from 'react'
import type { QueryClient } from '@tanstack/react-query'
import { useQueryClient } from '@tanstack/react-query'
import { ReactQueryProvider } from '@/providers/ReactQueryProvider'

describe('providers/ReactQueryProvider.tsx — TR9.1 staleTime defaults', () => {
  it('TR9.1 defaultOptions.queries.staleTime === 0 and gcTime === 5*60*1000', () => {
    const clientRef: { current: QueryClient | null } = { current: null }

    function Inspector() {
      const c = useQueryClient()
      useEffect(() => {
        clientRef.current = c
      }, [c])
      return <div data-testid="inspector-child">ok</div>
    }

    render(
      <ReactQueryProvider>
        <Inspector />
      </ReactQueryProvider>
    )

    expect(screen.getByTestId('inspector-child')).toBeInTheDocument()
    expect(clientRef.current).not.toBeNull()

    const defaultOptions = clientRef.current!.getDefaultOptions()
    expect(defaultOptions.queries?.staleTime).toBe(0)
    expect(defaultOptions.queries?.gcTime).toBe(5 * 60 * 1000)
  })
})
