import { render, screen } from '@testing-library/react'
import { StatCard, ChangeBadge } from '@/components/dashboard/StatCard'
import type { MarketStat } from '@/lib/dashboard-data'

describe('StatCard', () => {
  const mockStat: MarketStat = {
    label: 'شاخص کل',
    value: '۲٬۱۸۴٬۵۳۰',
    changePct: 1.24
  }

  it('renders stat card with label, value, and change', () => {
    render(<StatCard stat={mockStat} />)
    
    expect(screen.getByText('شاخص کل')).toBeInTheDocument()
    expect(screen.getByText('۲٬۱۸۴٬۵۳۰')).toBeInTheDocument()
    expect(screen.getByText(/▲ 1\.24%/)).toBeInTheDocument()
  })

  it('renders stat card without changePct when undefined', () => {
    const statWithoutChange: MarketStat = {
      label: 'نمادهای فعال',
      value: '۴۰۰'
    }
    
    render(<StatCard stat={statWithoutChange} />)
    
    expect(screen.getByText('نمادهای فعال')).toBeInTheDocument()
    expect(screen.getByText('۴۰۰')).toBeInTheDocument()
    expect(screen.queryByText(/▲|▼/)).not.toBeInTheDocument()
  })

  it('applies tarot-card class', () => {
    render(<StatCard stat={mockStat} />)
    
    const card = screen.getByRole('article')
    expect(card).toHaveClass('tarot-card')
  })
})

describe('ChangeBadge', () => {
  it('renders positive change with green styling', () => {
    render(<ChangeBadge value={2.5} />)
    
    expect(screen.getByText(/▲ 2\.50%/)).toBeInTheDocument()
    const badge = screen.getByText(/▲ 2\.50%/)
    expect(badge).toHaveClass('bg-success/15')
    expect(badge).toHaveClass('text-success')
  })

  it('renders negative change with red styling', () => {
    render(<ChangeBadge value={-1.75} />)
    
    expect(screen.getByText(/▼ 1\.75%/)).toBeInTheDocument()
    const badge = screen.getByText(/▼ 1\.75%/)
    expect(badge).toHaveClass('bg-primary/15')
    expect(badge).toHaveClass('text-primary')
  })

  it('renders zero change as positive', () => {
    render(<ChangeBadge value={0} />)
    
    expect(screen.getByText(/▲ 0\.00%/)).toBeInTheDocument()
    const badge = screen.getByText(/▲ 0\.00%/)
    expect(badge).toHaveClass('bg-success/15')
    expect(badge).toHaveClass('text-success')
  })
})