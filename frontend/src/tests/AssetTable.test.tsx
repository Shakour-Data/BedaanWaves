import { render, screen } from '@testing-library/react'
import { AssetTable } from '@/components/dashboard/AssetTable'
import type { AssetRow } from '@/lib/dashboard-data'

describe('AssetTable', () => {
  const mockAssets: AssetRow[] = [
    {
      symbol: 'TEST1',
      name: 'Test Asset 1',
      market: 'TSE',
      price: 1000,
      changePct: 2.5
    },
    {
      symbol: 'TEST2',
      name: 'Test Asset 2',
      market: 'BINANCE',
      price: 50000,
      changePct: -1.2
    }
  ]

  it('renders asset table with correct data', () => {
    render(<AssetTable rows={mockAssets} />)

    // Check headers are present
    expect(screen.getByText('نماد')).not.toBeNull()
    expect(screen.getByText('نام')).not.toBeNull()
    expect(screen.getByText('بازار')).not.toBeNull()
    expect(screen.getByText('قیمت')).not.toBeNull()
    expect(screen.getByText('تغییر')).not.toBeNull()

    // Check asset data is rendered
    expect(screen.getByText('TEST1')).not.toBeNull()
    expect(screen.getByText('Test Asset 1')).not.toBeNull()
    expect(screen.getByText('بورس')).not.toBeNull()
    
    // Updated for Persian number formatting
    const priceElement = screen.getByText(/۱٬۰۰۰/)
    expect(priceElement).not.toBeNull()

    const changeElement = screen.getByText(/▲ 2\.50٪/)
    expect(changeElement).not.toBeNull()

    expect(screen.getByText('TEST2')).not.toBeNull()
    expect(screen.getByText('Test Asset 2')).not.toBeNull()
    expect(screen.getByText('بازار')).not.toBeNull()

    const priceElement2 = screen.getByText(/۵۰٬۰۰۰/)
    expect(priceElement2).not.toBeNull()

    const changeElement2 = screen.getByText(/▼ 1\.20٪/)
    expect(changeElement2).not.toBeNull()
  })

  it('handles empty assets array', () => {
    render(<AssetTable rows={[]} />)

    expect(screen.getByText('نماد')).not.toBeNull()
    // tbody should be empty
    const tbodyRows = screen.getAllByRole('row')
    // Should only have header row
    expect(tbodyRows).toHaveLength(1)
  })
})