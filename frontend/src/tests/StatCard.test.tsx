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
    
    expect(screen.getByText('شاخص کل')).not.toBeNull()
    expect(screen.getByText('۲٬۱۸۴٬۵۳۰')).not.toBeNull()
    // Allow both arrow up styles
    expect(screen.getByText(/▲ ?1\.24%|▲٪ ?1\.24%|1\.24٪/)).not.toBeNull()
  })

  it('renders stat card without changePct when undefined', () => {
    const statWithoutChange: MarketStat = {
      label: 'نمادهای فعال',
      value: '۴۰۰'
    }

    render(<StatCard stat={statWithoutChange} />)

    expect(screen.getByText('نمادهای فعال')).not.toBeNull()
    expect(screen.getByText('۴۰۰')).not.toBeNull()
    expect(screen.queryByText(/[▲▼]/)).toBeNull()
  })

  it('applies tarot-card class', () => {
    render(<StatCard stat={mockStat} />)

    const card = screen.getByRole('article')
    expect(card.className).toContain('tarot-card')
  })
})

describe('ChangeBadge', () => {
  it('renders positive change with green styling', () => {
    render(<ChangeBadge value={2.5} />)
    
    const badge = screen.getByText(/▲ ?2\.50%|▲٪ ?2\.50%|2\.50٪/)
    expect(badge).not.toBeNull()
    expect(badge.className).toContain('bg-success/15')
    expect(badge.className).toContain('text-success')
  })

  it('renders negative change with red styling', () => {
    render(<ChangeBadge value={-1.75} />)
    
    const badge = screen.getByText(/[▼‾] ?1\.75%|‾٪ ?1\.75%|1\.75٪|1,75%/)
    expect(badge).not.toBeNull()
    expect(badge.className).toContain('bg-primary/15')
    expect(badge.className).toContain('text-primary')
  })

  it('renders zero change as positive', () => {
    render(<ChangeBadge value={0} />)

    const badge = screen.getByText(/▲ ?0\.00%|▲٪ ?0\.00%|0\.00٪/)
    expect(badge).not.toBeNull()
    expect(badge.className).toContain('bg-success/15')
    expect(badge.className).toContain('text-success')
  })
})