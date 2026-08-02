import { render, screen } from '@testing-library/react'
import { SignalList } from '@/components/dashboard/SignalList'
import type { SignalRow } from '@/lib/dashboard-data'

const TYPE_STYLE: Record<SignalRow['type'], { bg: string; text: string }> = {
  BUY: { bg: 'bg-success/15', text: 'text-success' },
  SELL: { bg: 'bg-primary/15', text: 'text-primary' },
  HOLD: { bg: 'bg-accent/30', text: 'text-accent-foreground' },
}

describe('SignalList', () => {
  const mockSignals: SignalRow[] = [
    {
      symbol: 'TEST1',
      type: 'BUY',
      confidence: 85.5,
      model: 'ScoringService-6D'
    },
    {
      symbol: 'TEST2',
      type: 'SELL',
      confidence: 72.3,
      model: 'RiskAnalysisService'
    },
    {
      symbol: 'TEST3',
      type: 'HOLD',
      confidence: 55.0,
      model: 'MomentumService'
    }
  ]

  it('renders signal list with correct data', () => {
    render(<SignalList signals={mockSignals} />)

    // Check symbols are rendered
    expect(screen.getByText('TEST1')).not.toBeNull()
    expect(screen.getByText('TEST2')).not.toBeNull()
    expect(screen.getByText('TEST3')).not.toBeNull()

    // Check signal types are translated
    expect(screen.getByText('خرید')).not.toBeNull()
    expect(screen.getByText('فروش')).not.toBeNull()
    expect(screen.getByText('نگهداری')).not.toBeNull()

    // Check confidence values are formatted - use more specific text to avoid duplicates
    expect(screen.getByText(/اطمینان 85\.5/)).not.toBeNull()
    expect(screen.getByText(/اطمینان 72\.3/)).not.toBeNull()
    expect(screen.getByText(/اطمینان 55\.0/)).not.toBeNull()

    // Check model names are displayed
    expect(screen.getByText('ScoringService-6D')).not.toBeNull()
    expect(screen.getByText('RiskAnalysisService')).not.toBeNull()
    expect(screen.getByText('MomentumService')).not.toBeNull()
  })

  it('handles empty signals array', () => {
    render(<SignalList signals={[]} />)

    // Should render an empty list
    const list = screen.getByRole('list')
    expect(list.children).toHaveLength(0)
  })

  it('displays correct styling for BUY signals', () => {
    const buySignal = [{ ...mockSignals[0], type: 'BUY' as const }]
    render(<SignalList signals={buySignal} />)

    const badge = screen.getByText('خرید')
    expect(badge.className).toContain(TYPE_STYLE.BUY.bg)
    expect(badge.className).toContain(TYPE_STYLE.BUY.text)
  })

  it('displays correct styling for SELL signals', () => {
    const sellSignal = [{ ...mockSignals[1], type: 'SELL' as const }]
    render(<SignalList signals={sellSignal} />)

    const badge = screen.getByText('فروش')
    expect(badge.className).toContain(TYPE_STYLE.SELL.bg)
    expect(badge.className).toContain(TYPE_STYLE.SELL.text)
  })

  it('displays correct styling for HOLD signals', () => {
    const holdSignal = [{ ...mockSignals[2], type: 'HOLD' as const }]
    render(<SignalList signals={holdSignal} />)

    const badge = screen.getByText('نگهداری')
    expect(badge.className).toContain(TYPE_STYLE.HOLD.bg)
    expect(badge.className).toContain(TYPE_STYLE.HOLD.text)
  })
})