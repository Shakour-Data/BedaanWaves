import { render, screen } from '@testing-library/react'
import { StatCard, ChangeBadge } from '@/components/dashboard/StatCard'
import type { MarketStat } from '@/lib/dashboard-data'

describe('StatCard', () => {
  const mockStat: MarketStat = {
    label: 'Total Index',
    value: '2,184,530',
    changePct: 1.24
  }

  it('renders stat card with label, value, and change', () => {
    render(<StatCard stat={mockStat} />)

    expect(screen.getByText('Total Index')).not.toBeNull()
    expect(screen.getByText('2,184,530')).not.toBeNull()
    expect(screen.getByText(/1\.24%/)).not.toBeNull()
  })

  it('renders stat card without changePct when undefined', () => {
    const statWithoutChange: MarketStat = {
      label: 'Active Symbols',
      value: '400'
    }

    render(<StatCard stat={statWithoutChange} />)

    expect(screen.getByText('Active Symbols')).not.toBeNull()
    expect(screen.getByText('400')).not.toBeNull()
    expect(screen.queryByText(/%/)).toBeNull()
  })

  it('renders stat card container', () => {
    render(<StatCard stat={mockStat} />);

    const card = screen.getByText('Total Index').closest('div')
    expect(card).not.toBeNull()
  })
})

describe('ChangeBadge', () => {
  it('renders positive change with green styling', () => {
    render(<ChangeBadge value={2.5} />)

    const badge = screen.getByText(/2\.50%/).parentElement
    expect(badge).not.toBeNull()
    expect(badge!.className).toContain('bg-success/10')
    expect(badge!.className).toContain('text-success')
  })

  it('renders negative change with red styling', () => {
    render(<ChangeBadge value={-1.75} />)

    const badge = screen.getByText(/1\.75%/).parentElement
    expect(badge).not.toBeNull()
    expect(badge!.className).toContain('bg-error/10')
    expect(badge!.className).toContain('text-error')
  })

  it('renders zero change as positive', () => {
    render(<ChangeBadge value={0} />)

    const badge = screen.getByText(/0\.00%/).parentElement
    expect(badge).not.toBeNull()
    expect(badge!.className).toContain('bg-success/10')
    expect(badge!.className).toContain('text-success')
  })
})
