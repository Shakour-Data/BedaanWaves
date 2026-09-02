import { render, screen } from '@testing-library/react'
import { AssetTable } from '@/components/dashboard/AssetTable'
import type { AssetRow } from '@/lib/dashboard-data'

describe('AssetTable', () => {
  const mockAssets: AssetRow[] = [
    {
      symbol: 'AAPL',
      name: 'Apple Inc.',
      market: 'NASDAQ',
      price: 150,
      changePct: 2.5
    },
    {
      symbol: 'MSFT',
      name: 'Microsoft',
      market: 'NASDAQ',
      price: 380,
      changePct: -1.2
    }
  ]

  it('renders asset table with correct data', () => {
    render(<AssetTable rows={mockAssets} />)

    // Check headers are present
    expect(screen.getByText('Symbol')).not.toBeNull()
    expect(screen.getByText('Name')).not.toBeNull()
    expect(screen.getByText('Market')).not.toBeNull()
    expect(screen.getByText('Price')).not.toBeNull()
    expect(screen.getByText('Change')).not.toBeNull()

    // Check asset data is rendered
    expect(screen.getByText('AAPL')).not.toBeNull()
    expect(screen.getByText('Apple Inc.')).not.toBeNull()
    expect(screen.getAllByText('NASDAQ')).toHaveLength(2)

    const priceElement = screen.getByText(/150/)
    expect(priceElement).not.toBeNull()

    const changeElement = screen.getByText(/2\.50%/)
    expect(changeElement).not.toBeNull()

    expect(screen.getByText('MSFT')).not.toBeNull()
    expect(screen.getByText('Microsoft')).not.toBeNull()

    const priceElement2 = screen.getByText(/380/)
    expect(priceElement2).not.toBeNull()

    const changeElement2 = screen.getByText(/1\.20%/)
    expect(changeElement2).not.toBeNull()
  })

  it('handles empty assets array', () => {
    render(<AssetTable rows={[]} />)

    expect(screen.getByText('Symbol')).not.toBeNull()
    // tbody should be empty
    const tbodyRows = screen.getAllByRole('row')
    // Should only have header row
    expect(tbodyRows).toHaveLength(1)
  })
})