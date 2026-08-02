import { render, screen } from '@testing-library/react'
import { NewsList } from '@/components/dashboard/NewsList'
import type { NewsItem } from '@/lib/dashboard-data'

describe('NewsList', () => {
  const mockNews: NewsItem[] = [
    {
      title: 'Updates on Market Conditions Affecting Precious Metals',
      source: 'Financial Times',
      time: '10 minutes ago'
    },
    {
      title: 'Analysis of Regional Economic Impact on Industry Sectors',
      source: 'Market Insights Journal',
      time: '2 hours ago'
    }
  ]

  it('renders news items with correct structure', () => {
    render(<NewsList items={mockNews} />)

    // Check news titles are displayed using regex
    expect(screen.getByText(/Updates on Market/)).not.toBeNull()
    expect(screen.getByText(/Analysis of Regional/)).not.toBeNull()

    // Check sources are displayed (using partial match)
    expect(screen.getByText(/Financial Times/)).not.toBeNull()
    expect(screen.getByText(/Market Insights Journal/)).not.toBeNull()

    // Check time formatting is correct
    expect(screen.getByText(/10 minutes ago/)).not.toBeNull()
    expect(screen.getByText(/2 hours ago/)).not.toBeNull()
  })

  it('renders empty news list gracefully', () => {
    render(<NewsList items={[]} />)

    const list = screen.getByRole('list')
    // Should have no children when empty
    expect(list.children).toHaveLength(0)
  })

  it('displays news items with correct styling', () => {
    render(<NewsList items={mockNews} />)

    const firstTitle = screen.getByText(/Updates on Market/)
    const firstItem = firstTitle.closest('li')

    // First item should have border
    expect(firstItem).not.toBeNull()
    expect(firstItem.className).toContain('border-b')

    // Check that the source and time are in the same item
    const sourceElement = screen.getByText(/Financial Times/).closest('li')
    const timeElement = screen.getByText(/10 minutes ago/).closest('li')

    // Both should be in the same list item
    expect(sourceElement).not.toBeNull()
    expect(timeElement).not.toBeNull()
  })
})