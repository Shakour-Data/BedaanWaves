import { render, screen, fireEvent } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { sidebarCategories, sidebarBottomItems, type NavItem, type NavCategory } from '@/lib/sidebar-config';
import { Sidebar } from '@/components/layout/Sidebar';

vi.mock('next/navigation', () => ({
  usePathname: () => '/dashboard',
  useSearchParams: () => new URLSearchParams(),
}));

const mockSetSidebarOpen = vi.fn();
const mockLogout = vi.fn();

const mockAppStore = {
  sidebarOpen: false,
  setSidebarOpen: mockSetSidebarOpen,
  toggleSidebar: vi.fn(),
  theme: 'dark' as const,
  setTheme: vi.fn(),
  toggleTheme: vi.fn(),
};

const mockAuthStore = {
  user: null,
  logout: mockLogout,
  isAuthenticated: false,
  loading: false,
  token: null,
  refreshToken: null,
  login: vi.fn(),
  register: vi.fn(),
};

vi.mock('@/store/useAppStore', () => ({
  useAppStore: (selector?: (state: typeof mockAppStore) => unknown) => {
    if (selector) return selector(mockAppStore);
    return mockAppStore;
  },
}));

vi.mock('@/store/useAuthStore', () => ({
  useAuthStore: (selector?: (state: typeof mockAuthStore) => unknown) => {
    if (selector) return selector(mockAuthStore);
    return mockAuthStore;
  },
}));

vi.mock('@/components/search/UnifiedSearchBar', () => ({
  UnifiedSearchBar: ({ placeholder }: { placeholder?: string }) => (
    <div data-testid="unified-search-bar" data-placeholder={placeholder ?? ''}>
      Search
    </div>
  ),
}));

function expandAllCategories() {
  const toggleButtons = screen.getAllByRole('button');
  toggleButtons.forEach((btn) => {
    if (btn.getAttribute('aria-expanded') === 'false') {
      fireEvent.click(btn);
    }
  });
}

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

  it('keeps the Platform category with Dashboard item (backward compat)', () => {
    const platformItems = sidebarCategories.find((cat) => cat.label === 'Platform')?.items || [];
    const dashboardItem = platformItems.find((item) => item.href === '/dashboard');
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

  it('all categories have an icon field', () => {
    sidebarCategories.forEach((cat) => {
      expect(cat.icon).toBeTruthy();
    });
  });

  it('all items have an icon field', () => {
    const allItems = [...sidebarBottomItems];
    sidebarCategories.forEach((cat) => allItems.push(...cat.items));
    allItems.forEach((item) => {
      expect(item.icon).toBeTruthy();
    });
  });
});

describe('NewSidebar component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the sidebar with brand logo', () => {
    render(<Sidebar />);
    expect(screen.getByText('BedaanWaves')).toBeInTheDocument();
  });

  it('renders the unified search bar', () => {
    render(<Sidebar />);
    expect(screen.getByTestId('unified-search-bar')).toBeInTheDocument();
  });

  it('renders all category headers', () => {
    render(<Sidebar />);

    sidebarCategories.forEach((cat) => {
      const headerEls = screen.getAllByText(cat.label);
      expect(headerEls.length).toBeGreaterThanOrEqual(1);
    });
  });

  it('renders bottom account items', () => {
    render(<Sidebar />);

    sidebarBottomItems.forEach((item) => {
      expect(screen.getAllByText(item.label).length).toBeGreaterThanOrEqual(1);
    });
  });

  it('renders items from expanded categories', () => {
    render(<Sidebar />);
    expandAllCategories();

    const allItems = sidebarCategories.flatMap((cat) => cat.items);
    allItems.forEach((item) => {
      const linkEls = screen.getAllByRole('link', { name: item.label });
      expect(linkEls.length).toBeGreaterThanOrEqual(1);
    });
  });

  it('renders nav items from the auto-expanded category on initial load', () => {
    render(<Sidebar />);

    const dashboardLinks = screen.getAllByRole('link', { name: 'Dashboard' });
    expect(dashboardLinks.length).toBeGreaterThanOrEqual(1);
  });

  it('toggles category expand/collapse when header is clicked', () => {
    render(<Sidebar />);

    const toggleButtons = screen.getAllByRole('button');
    const categoryToggle = toggleButtons.find((btn) => btn.getAttribute('aria-expanded') === 'false');

    expect(categoryToggle).toBeDefined();

    if (categoryToggle) {
      const initialExpanded = categoryToggle.getAttribute('aria-expanded');
      fireEvent.click(categoryToggle);
      const afterFirstClick = categoryToggle.getAttribute('aria-expanded');
      expect(afterFirstClick).not.toBe(initialExpanded);

      fireEvent.click(categoryToggle);
      const afterSecondClick = categoryToggle.getAttribute('aria-expanded');
      expect(afterSecondClick).toBe(initialExpanded);
    }
  });

  it('has proper aria-labels for accessibility', () => {
    render(<Sidebar />);

    const nav = screen.getByRole('navigation', { name: /main navigation/i });
    expect(nav).toBeInTheDocument();

    const expandedState = nav.getAttribute('aria-label');
    expect(expandedState).toBe('Main navigation');
  });

  it('renders icons for category headers (always visible)', () => {
    render(<Sidebar />);

    sidebarCategories.forEach((cat) => {
      expect(screen.getAllByTestId(`icon-${cat.icon}`).length).toBeGreaterThan(0);
    });
  });

  it('renders icons for items in expanded categories', () => {
    render(<Sidebar />);
    expandAllCategories();

    const allItems = sidebarCategories.flatMap((cat) => cat.items);
    allItems.forEach((item) => {
      expect(screen.getAllByTestId(`icon-${item.icon}`).length).toBeGreaterThan(0);
    });
  });

  it('renders SVG icon elements', () => {
    render(<Sidebar />);
    const svgElements = document.querySelectorAll('svg');
    expect(svgElements.length).toBeGreaterThan(0);
  });

  it('closes sidebar on mobile when a nav item is clicked', () => {
    render(<Sidebar />);

    const dashboardLinks = screen.getAllByRole('link', { name: 'Dashboard' });
    fireEvent.click(dashboardLinks[0]);
    expect(mockSetSidebarOpen).toHaveBeenCalledWith(false);
  });

  it('renders the Account section label', () => {
    render(<Sidebar />);
    const accountLabels = screen.getAllByText('Account');
    expect(accountLabels.length).toBeGreaterThanOrEqual(1);
  });

  it('renders a quick search hint in the footer', () => {
    render(<Sidebar />);
    const quickSearchText = screen.getByText(/Quick search/i);
    expect(quickSearchText).toBeInTheDocument();
  });
});
