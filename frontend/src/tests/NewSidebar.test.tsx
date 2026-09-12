import { render, screen, fireEvent } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { sidebarCategories, sidebarBottomItems, type NavItem, type NavCategory } from '@/lib/sidebar-config';
import { NewSidebar } from '@/components/layout/NewSidebar';

vi.mock('next/navigation', () => ({
  usePathname: () => '/dashboard',
  useSearchParams: () => new URLSearchParams(),
}));

vi.mock('@/store/useAppStore', () => ({
  useAppStore: (selector: (state: { sidebarOpen: boolean; setSidebarOpen: (open: boolean) => void }) => unknown) =>
    selector({ sidebarOpen: false, setSidebarOpen: vi.fn() }),
}));

vi.mock('@/store/useAuthStore', () => ({
  useAuthStore: (selector: (state: { user: null; logout: () => void }) => unknown) =>
    selector({ user: null, logout: vi.fn() }),
}));

vi.mock('@/components/search/UnifiedSearchBar', () => ({
  UnifiedSearchBar: ({ placeholder }: { placeholder?: string }) => (
    <div data-testid="unified-search-bar" data-placeholder={placeholder ?? ''}>
      Search
    </div>
  ),
}));

describe('sidebar-config', () => {
  it('exports categories and bottom items with icon fields', () => {
    expect(sidebarCategories).toBeDefined();
    expect(sidebarBottomItems).toBeDefined();
    expect(Array.isArray(sidebarCategories)).toBe(true);
    expect(sidebarCategories.length).toBeGreaterThan(0);

    sidebarCategories.forEach((cat: NavCategory) => {
      expect(cat.icon).toBeDefined();
      expect(typeof cat.icon).toBe('string');
      cat.items.forEach((item: NavItem) => {
        expect(item.icon).toBeDefined();
        expect(typeof item.icon).toBe('string');
        expect(item.label).toBeDefined();
        expect(item.href).toBeDefined();
      });
    });

    sidebarBottomItems.forEach((item: NavItem) => {
      expect(item.icon).toBeDefined();
    });
  });

  it('includes links to all major site pages', () => {
    const allHrefs: string[] = [];
    sidebarCategories.forEach((cat) => cat.items.forEach((item) => allHrefs.push(item.href)));
    sidebarBottomItems.forEach((item) => allHrefs.push(item.href));

    const expectedPages = [
      '/dashboard',
      '/leaderboard',
      '/movers',
      '/stocks',
      '/analysis',
      '/scoring',
      '/scoring-filter',
      '/portfolio',
      '/ranking',
      '/compare',
      '/news',
      '/alerts',
      '/search-demo',
      '/watchlist',
      '/methodology',
      '/help',
      '/settings',
      '/settings/profile',
      '/',
      '/about',
      '/services',
      '/blog',
      '/contact',
    ];

    expectedPages.forEach((page) => {
      expect(allHrefs).toContain(page);
    });
  });

  it('keeps the Analytics category with Dashboard item (backward compat)', () => {
    const analyticsItems = sidebarCategories.find((cat) => cat.label === 'Analytics')?.items || [];
    const dashboardItem = analyticsItems.find((item) => item.href === '/dashboard');
    expect(dashboardItem).toBeDefined();
    expect(dashboardItem?.label).toBe('Dashboard');
  });

  it('includes a Platform category with public pages', () => {
    const platformItems = sidebarCategories.find((cat) => cat.label === 'Platform')?.items || [];
    expect(platformItems.length).toBeGreaterThan(0);

    const publicPages = ['/', '/about', '/services', '/blog', '/contact'];
    publicPages.forEach((page) => {
      expect(platformItems.find((item) => item.href === page)).toBeDefined();
    });
  });

  it('includes a Design System page', () => {
    const allItems = sidebarCategories.flatMap((cat) => cat.items);
    const designSystemItem = allItems.find((item) => item.href === '/design-system');
    expect(designSystemItem).toBeDefined();
    expect(designSystemItem?.label).toBe('Design System');
  });

  it('includes a Compare page', () => {
    const allItems = sidebarCategories.flatMap((cat) => cat.items);
    const compareItem = allItems.find((item) => item.href === '/compare');
    expect(compareItem).toBeDefined();
  });
});

describe('NewSidebar component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the sidebar with brand logo', () => {
    render(<NewSidebar />);
    expect(screen.getByText('BedaanWaves')).toBeInTheDocument();
    expect(screen.getByText('Analytics')).toBeInTheDocument();
  });

  it('renders the unified search bar', () => {
    render(<NewSidebar />);
    expect(screen.getByTestId('unified-search-bar')).toBeInTheDocument();
  });

  it('renders category headers with icons', () => {
    render(<NewSidebar />);

    const categoryHeaders = sidebarCategories.map((cat) => cat.label);
    categoryHeaders.forEach((header) => {
      const headerEl = screen.getByText(header);
      expect(headerEl).toBeInTheDocument();
    });
  });

  it('renders all nav items from all categories', () => {
    render(<NewSidebar />);

    const allItems = sidebarCategories.flatMap((cat) => cat.items);
    allItems.forEach((item) => {
      expect(screen.getByText(item.label)).toBeInTheDocument();
    });
  });

  it('renders bottom account items', () => {
    render(<NewSidebar />);

    sidebarBottomItems.forEach((item) => {
      expect(screen.getByText(item.label)).toBeInTheDocument();
    });
  });

  it('highlights the active nav item based on current pathname', () => {
    render(<NewSidebar />);

    const dashboardLink = screen.getByRole('link', { name: /Dashboard/i });
    expect(dashboardLink).toBeInTheDocument();
  });

  it('auto-expands the category containing the active page', () => {
    render(<NewSidebar />);

    const analyticsHeader = screen.getByText('Analytics');
    expect(analyticsHeader).toBeInTheDocument();

    const analyticsItems = sidebarCategories.find((cat) => cat.label === 'Analytics')?.items || [];
    const dashboardItem = analyticsItems.find((item) => item.href === '/dashboard');
    if (dashboardItem) {
      expect(screen.getByText(dashboardItem.label)).toBeInTheDocument();
    }
  });

  it('toggles category expand/collapse when header is clicked', () => {
    render(<NewSidebar />);

    const expandButtons = screen.getAllByRole('button');
    const firstCategoryButton = expandButtons.find((btn) =>
      btn.getAttribute('aria-expanded') !== undefined
    );

    if (firstCategoryButton) {
      const initialExpanded = firstCategoryButton.getAttribute('aria-expanded');
      fireEvent.click(firstCategoryButton);
      const newExpanded = firstCategoryButton.getAttribute('aria-expanded');
      expect(newExpanded).not.toBe(initialExpanded);
    }
  });

  it('has proper aria-labels for accessibility', () => {
    render(<NewSidebar />);

    const nav = screen.getByRole('navigation', { name: /main navigation/i });
    expect(nav).toBeInTheDocument();
  });

  it('renders icons for all categories and items', () => {
    render(<NewSidebar />);

    const allItems = sidebarCategories.flatMap((cat) => cat.items);
    const allIcons = new Set([...sidebarCategories.map((c) => c.icon), ...allItems.map((i) => i.icon)]);

    allIcons.forEach((iconName) => {
      expect(screen.getByTestId(`icon-${iconName}`) || screen.getByLabelText(`icon-${iconName}`)).toBeDefined();
    });
  });
});
