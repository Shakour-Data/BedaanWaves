export interface NavItem {
  label: string;
  href: string;
  marker: string;
}

export interface NavCategory {
  label: string;
  items: NavItem[];
}

export const sidebarCategories: NavCategory[] = [
  {
    label: "Analytics",
    items: [
      { label: "Dashboard", href: "/dashboard", marker: "DB" },
      { label: "Leaderboard", href: "/leaderboard", marker: "LB" },
      { label: "Biggest Movers", href: "/movers", marker: "MV" },
      { label: "Stocks", href: "/stocks", marker: "S" },
      { label: "Analysis", href: "/analysis", marker: "A" },
      { label: "Scoring", href: "/scoring", marker: "SC" },
      { label: "Scoring Filter", href: "/scoring-filter", marker: "SF" },
      { label: "Portfolio", href: "/portfolio", marker: "P" },
      { label: "Rankings", href: "/ranking", marker: "RN" },
    ],
  },
  {
    label: "Markets",
    items: [
      { label: "NASDAQ", href: "/dashboard", marker: "NQ" },
      { label: "Neark", href: "/nerk", marker: "NK" },
    ],
  },
  {
    label: "Intelligence",
    items: [
      { label: "News", href: "/news", marker: "NW" },
      { label: "Alerts", href: "/alerts", marker: "AL" },
      { label: "Search", href: "/search-demo", marker: "SR" },
      { label: "Watchlist", href: "/watchlist", marker: "WL" },
    ],
  },
  {
    label: "Resources",
    items: [
      { label: "Methodology", href: "/methodology", marker: "M" },
      { label: "Help", href: "/help", marker: "H" },
    ],
  },
];

export const sidebarBottomItems: NavItem[] = [
  { label: "Settings", href: "/settings", marker: "ST" },
  { label: "Profile", href: "/settings/profile", marker: "PR" },
];
