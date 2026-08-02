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
    expect(screen.getByText('TEST1')).toBeInTheDocument()
    expect(screen.getByText('TEST2')).toBeInTheDocument()
    expect(screen.getByText('TEST3')).toBeInTheDocument()
    
    // Check signal types are translated
    expect(screen.getByText('خرید')).toBeInTheDocument()
    expect(screen.getByText('فروش')).toBeInTheDocument()
    expect(screen.getByText('نگهداری')).toBeInTheDocument()
    
    // Check confidence values are formatted - use partial match
    expect(screen.getByText(/اطمینان/)).toBeInTheDocument()
    expect(screen.getByText(/85\.5%/)).toBeInTheDocument()
    expect(screen.getByText(/72\.3%/)).toBeInTheDocument()
    expect(screen.getByText(/55\.0%/)).toBeInTheDocument()
    
    // Check model names are displayed
    expect(screen.getByText('ScoringService-6D')).toBeInTheDocument()
    expect(screen.getByText('RiskAnalysisService')).toBeInTheDocument()
    expect(screen.getByText('MomentumService')).toBeInTheDocument()
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
    expect(badge).toHaveClass(TYPE_STYLE.BUY.bg)
    expect(badge).toHaveClass(TYPE_STYLE.BUY.text)
  })

  it('displays correct styling for SELL signals', () => {
    const sellSignal = [{ ...mockSignals[1], type: 'SELL' as const }]
    render(<SignalList signals={sellSignal} />)
    
    const badge = screen.getByText('فروش')
    expect(badge).toHaveClass(TYPE_STYLE.SELL.bg)
    expect(badge).toHaveClass(TYPE_STYLE.SELL.text)
  })

  it('displays correct styling for HOLD signals', () => {
    const holdSignal = [{ ...mockSignals[2], type: 'HOLD' as const }]
    render(<SignalList signals={holdSignal} />)
    
    const badge = screen.getByText('نگهداری')
    expect(badge).toHaveClass(TYPE_STYLE.HOLD.bg)
    expect(badge).toHaveClass(TYPE_STYLE.HOLD.text)
  })
})