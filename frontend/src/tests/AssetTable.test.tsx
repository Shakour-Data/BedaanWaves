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
    expect(screen.getByText('نماد')).toBeInTheDocument()
    expect(screen.getByText('نام')).toBeInTheDocument()
    expect(screen.getByText('بازار')).toBeInTheDocument()
    expect(screen.getByText('قیمت')).toBeInTheDocument()
    expect(screen.getByText('تغییر')).toBeInTheDocument()
    
    // Check asset data is rendered
    expect(screen.getByText('TEST1')).toBeInTheDocument()
    expect(screen.getByText('Test Asset 1')).toBeInTheDocument()
    expect(screen.getByText('بورس')).toBeInTheDocument()
    // Check for the actual rendered content - the component formats the number
    const priceElement = screen.getByText(/1,000/)
    expect(priceElement).toBeInTheDocument()
    expect(screen.getByText(/▲ 2.50%/)).toBeInTheDocument()
    
    expect(screen.getByText('TEST2')).toBeInTheDocument()
    expect(screen.getByText('Test Asset 2')).toBeInTheDocument()
    expect(screen.getByText('کریپتو')).toBeInTheDocument()
    expect(screen.getByText(/50,000/)).toBeInTheDocument()
    expect(screen.getByText(/▼ 1.20%/)).toBeInTheDocument()
  })

  it('handles empty assets array', () => {
    render(<AssetTable rows={[]} />)
    
    expect(screen.getByText('نماد')).toBeInTheDocument()
    // tbody should be empty
    const tbodyRows = screen.getAllByRole('row')
    // Should only have header row
    expect(tbodyRows).toHaveLength(1)
  })
})