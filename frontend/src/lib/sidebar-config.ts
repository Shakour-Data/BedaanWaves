export interface NavItem {
  label: string;
  href: string;
  icon: string;
  marker?: string;
  badge?: string;
}

export interface NavCategory {
  label: string;
  icon: string;
  items: NavItem[];
}

export const sidebarCategories: NavCategory[] = [
  {
    label: "Platform",
    icon: "LayoutDashboard",
    items: [
      { label: "Home", href: "/", icon: "House", marker: "HM" },
      { label: "Dashboard", href: "/dashboard", icon: "LayoutDashboard", marker: "DB" },
      { label: "About", href: "/about", icon: "Info", marker: "AB" },
      { label: "Services", href: "/services", icon: "Sparkles", marker: "SV" },
      { label: "Blog", href: "/blog", icon: "Book", marker: "BL" },
      { label: "Contact", href: "/contact", icon: "Mail", marker: "CT" },
    ],
  },
  {
    label: "Analytics",
    icon: "BarChart3",
    items: [
      { label: "Dashboard", href: "/dashboard", icon: "LayoutDashboard", marker: "DB" },
      { label: "Analytical Dashboard", href: "/dashboard?tab=general", icon: "AreaChart", marker: "AN" },
      { label: "Leaderboard", href: "/leaderboard", icon: "Trophy", marker: "LB" },
      { label: "Biggest Movers", href: "/movers", icon: "TrendingUpDown", marker: "MV" },
      { label: "Stocks", href: "/stocks", icon: "Briefcase", marker: "S" },
      { label: "Analysis", href: "/analysis", icon: "PieChart", marker: "A" },
      { label: "Scoring", href: "/scoring", icon: "Brain", marker: "SC" },
      { label: "Scoring Filter", href: "/scoring-filter", icon: "Filter", marker: "SF" },
      { label: "Portfolio", href: "/portfolio", icon: "Wallet", marker: "P" },
      { label: "Rankings", href: "/ranking", icon: "BarChart3", marker: "RN" },
      { label: "Compare", href: "/compare", icon: "GitCompare", marker: "CP" },
      { label: "Design System", href: "/design-system", icon: "Palette", marker: "DS" },
    ],
  },
  {
    label: "Markets",
    icon: "Globe",
    items: [
      { label: "NASDAQ", href: "/dashboard", icon: "Activity", marker: "NQ" },
      { label: "Neark Index", href: "/nerk", icon: "Globe", marker: "NK" },
    ],
  },
  {
    label: "Intelligence",
    icon: "Eye",
    items: [
      { label: "News", href: "/news", icon: "Newspaper", marker: "NW" },
      { label: "Alerts", href: "/alerts", icon: "Bell", marker: "AL" },
      { label: "Search", href: "/search-demo", icon: "Search", marker: "SR" },
      { label: "Watchlist", href: "/watchlist", icon: "Eye", marker: "WL" },
    ],
  },
  {
    label: "Resources",
    icon: "BookOpen",
    items: [
      { label: "Methodology", href: "/methodology", icon: "BookOpen", marker: "M" },
      { label: "Help", href: "/help", icon: "HelpCircle", marker: "H" },
    ],
  },
];

export const sidebarBottomItems: NavItem[] = [
  { label: "Settings", href: "/settings", icon: "Settings", marker: "ST" },
  { label: "Profile", href: "/settings/profile", icon: "User", marker: "PR" },
];
