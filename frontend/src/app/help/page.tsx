"use client";

import { DashboardShell } from "@/components/layout/DashboardShell";
import { TarotCard } from "@/components/ui/TarotCard";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import Link from "next/link";
import { useState } from "react";

// Page information
const pages = [
  {
    name: "Home",
    path: "/",
    icon: "🏠",
    description: "Landing page introducing the BedaanWaves platform and its four pillars of analysis",
    category: "Navigation"
  },
  {
    name: "Login",
    path: "/login",
    icon: "🔐",
    description: "Authentication page for existing users to access their accounts",
    category: "Authentication"
  },
  {
    name: "Register",
    path: "/register",
    icon: "📝",
    description: "Registration page for new users to create an account",
    category: "Authentication"
  },
  {
    name: "Dashboard",
    path: "/dashboard",
    icon: "📊",
    description: "Main dashboard showing market overview, top movers, watchlist, signals, and news",
    category": "Core Features"
  },
  {
    name: "Stocks List",
    path: "/stocks",
    icon: "🏢",
    description: "Complete list of tradeable symbols with real-time prices and market filtering",
    category": "Market Data"
  },
  {
    name: "Stock Detail",
    path: "/stocks/[symbol]",
    icon: "🔍",
    description: "Detailed view of individual assets with charts, technical analysis, and fundamentals",
    category": "Market Data"
  },
  {
    name: "Portfolio",
    path: "/portfolio",
    icon: "💼",
    description: "Personal portfolio management with holdings, performance tracking, and allocation",
    category": "Personal Finance"
  },
  {
    name: "Analysis",
    path: "/analysis",
    icon: "🔮",
    description": "Multi-tab analysis interface covering technical, fundamental, 6D scoring, and sentiment analysis",
    category": "Analysis Tools"
  },
  {
    name: "Scoring",
    path: "/scoring",
    icon: "🧮",
    description": "Detailed explanation of the 6-dimensional scoring system with 305-node hierarchy",
    category": "Education"
  },
  {
    name: "Methodology",
    path: "/methodology",
    icon: "📚",
    description": "Comprehensive guide to all analysis types including scoring, ranking, technical, fundamental, and more",
    category": "Education"
  },
  {
    name: "News",
    path: "/news",
    icon: "📰",
    description": "Market news aggregation with filtering capabilities and trending topics",
    category": "Market Data"
  },
  {
    name: "Alerts",
    path: "/alerts",
    icon: "🔔",
    description": "System alerts and notifications management including price alerts and ML signals",
    category": "Notifications"
  },
  {
    name: "Settings",
    path: "/settings",
    icon: "⚙️",
    description": "System-wide configuration including theme, language, notifications, and quick actions",
    category": "User Settings"
  },
  {
    name: "Profile Settings",
    path: "/settings/profile",
    icon: "👤",
    description": "User profile management and security settings including password changes",
    category": "User Settings"
  }
];

// Component information
const components = [
  {
    name: "DashboardShell",
    path: "@/components/layout/DashboardShell",
    description": "Main layout wrapper that provides authentication checks, theming, sidebar, and topbar",
    category": "Layout"
  },
  {
    name: "Sidebar",
    path: "@/components/layout/Sidebar",
    description": "Navigation sidebar with links to all main pages, user info, and logout functionality",
    category": "Layout"
  },
  {
    name: "Topbar",
    path: "@/components/layout/Topbar",
    description": "Top navigation bar with search, theme toggle, and user profile controls",
    category": "Layout"
  },
  {
    name: "TarotCard",
    path: "@/components/ui/TarotCard",
    description": "Styled card component with hover effects, shadows, and consistent padding used throughout the UI",
    category": "UI Components"
  },
  {
    name: "PrimaryButton",
    path: "@/components/ui/PrimaryButton",
    description": "Primary call-to-action button with glow effect and hover animation",
    category": "UI Components"
  },
  {
    name: "StatCard",
    path: "@/components/dashboard/StatCard",
    description": "Statistical card component for displaying key metrics with labels and values",
    category": "Dashboard Components"
  },
  {
    name: "AssetTable",
    path: "@/components/dashboard/AssetTable",
    description": "Table component for displaying financial assets with symbols, names, prices, and changes",
    category": "Dashboard Components"
  },
  {
    name: "SignalList",
    path: "@/components/dashboard/SignalList",
    description": "List component for displaying ML trading signals with symbols, types, confidence, and models",
    category": "Dashboard Components"
  },
  {
    name: "NewsList",
    path: "@/components/dashboard/NewsList",
    description": "List component for displaying news articles with headlines, timestamps, and sources",
    category": "Dashboard Components"
  }
];

export default function HelpPage() {
  const [activeTab, setActiveTab] = useState("pages");

  return (
    <DashboardShell title="Help & Documentation">
      <div className="flex flex-col gap-6">
        {/* Header */}
        <TarotCard icon="📚" title="BedaanWaves Help & Documentation">
          <p className="text-muted-foreground text-justify">
            Welcome to the BedaanWaves help center. This page provides comprehensive documentation about all pages, components, and features of the platform. Use the tabs below to navigate between different sections of the documentation.
          </p>
        </TarotCard>

        {/* Tabs */}
        <div className="flex gap-2 flex-wrap">
          <button
            onClick={() => setActiveTab("pages")}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-colors whitespace-nowrap ${
              activeTab === "pages"
                ? "bg-secondary text-secondary-foreground"
                : "bg-muted text-muted-foreground hover:bg-muted/80"
            }`}
          >
            Pages
          </button>
          <button
            onClick={() => setActiveTab("components")}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-colors whitespace-nowrap ${
              activeTab === "components"
                ? "bg-secondary text-secondary-foreground"
                : "bg-muted text-muted-foreground hover:bg-muted/80"
            }`}
          >
            Components
          </button>
          <button
            onClick={() => setActiveTab("navigation")}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-colors whitespace-nowrap ${
              activeTab === "navigation"
                ? "bg-secondary text-secondary-foreground"
                : "bg-muted text-muted-foreground hover:bg-muted/80"
            }`}
          >
            Navigation
          </button>
        </div>

        {/* Pages Tab */}
        {activeTab === "pages" && (
          <TarotCard icon="📄" title="Application Pages">
            <div className="space-y-4">
              {pages.map((page) => (
                <div key={page.path} className="border p-4 rounded-lg">
                  <div className="flex items-start gap-4">
                    <div className="flex-shrink-0">
                      <span className="text-3xl">{page.icon}</span>
                    </div>
                    <div className="flex-1">
                      <h3 className="font-semibold mb-1">{page.name}</h3>
                      <p className="text-sm text-muted-foreground mb-2">
                        <span className="font-medium">Path:</span> <code className="bg-muted/20 px-1 py-0.5 rounded">{page.path}</code>
                      </p>
                      <p className="text-muted-foreground">{page.description}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </TarotCard>
        )}

        {/* Components Tab */}
        {activeTab === "components" && (
          <TarotCard icon="⚙️" title="UI Components">
            <div className="space-y-4">
              {components.map((component) => (
                <div key={component.path} className="border p-4 rounded-lg">
                  <div className="flex items-start gap-4">
                    <div className="flex-shrink-0">
                      <span className="text-2xl">🔧</span>
                    </div>
                    <div className="flex-1">
                      <h3 className="font-semibold mb-1">{component.name}</h3>
                      <p className="text-sm text-muted-foreground mb-2">
                        <span className="font-medium">Path:</span> <code className="bg-muted/20 px-1 py-0.5 rounded">{component.path}</code>
                      </p>
                      <p className="text-muted-foreground">{component.description}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </TarotCard>
        )}

        {/* Navigation Tab */}
        {activeTab === "navigation" && (
          <TarotCard icon="🧭" title="Navigation Structure">
            <div className="space-y-4">
              {/* Main Navigation */}
              <div className="border p-4 rounded-lg">
                <h3 className="font-semibold mb-3">Main Navigation</h3>
                <div className="space-y-2">
                  {[
                    { label: "Dashboard", path: "/dashboard", icon: "🏠" },
                    { label: "Stocks", path: "/stocks", icon: "📈" },
                    { label: "Portfolio", path: "/portfolio", icon: "💼" },
                    { label: "Analysis", path: "/analysis", icon: "🔍" },
                    { label: "News", path: "/news", icon: "📰" },
                    { label: "Alerts", path: "/alerts", icon: "🔔" },
                    { label: "Settings", path: "/settings", icon: "⚙️" }
                  ].map((item) => (
                    <div key={item.path} className="flex items-center gap-3 p-2 hover:bg-muted/50 transition-colors rounded-lg">
                      <span className="text-xl">{item.icon}</span>
                      <div>
                        <div className="font-medium">{item.label}</div>
                        <p className="text-xs text-muted-foreground">{item.path}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Authentication Flow */}
              <div className="border p-4 rounded-lg">
                <h3 className="font-semibold mb-3">Authentication Flow</h3>
                <div className="space-y-2">
                  <div className="flex items-center gap-3 p-2 hover:bg-muted/50 transition-colors rounded-lg">
                    <span className="text-xl">🔐</span>
                    <div>
                      <div className="font-medium">Login</div>
                      <p className="text-xs text-muted-foreground">/login</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 p-2 hover:bg-muted/50 transition-colors rounded-lg">
                    <span className="text-xl">📝</span>
                    <div>
                      <div className="font-medium">Register</div>
                      <p className="text-xs text-muted-foreground">/register</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Educational Resources */}
              <div className="border p-4 rounded-lg">
                <h3 className="font-semibold mb-3">Educational Resources</h3>
                <div className="space-y-2">
                  <div className="flex items-center gap-3 p-2 hover:bg-muted/50 transition-colors rounded-lg">
                    <span className="text-xl">🧮</span>
                    <div>
                      <div className="font-medium">6D Scoring System</div>
                      <p className="text-xs text-muted-foreground">/scoring</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 p-2 hover:bg-muted/50 transition-colors rounded-lg">
                    <span className="text-xl">📚</span>
                    <div>
                      <div className="font-medium">Methodology Guide</div>
                      <p className="text-xs text-muted-foreground">/methodology</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </TarotCard>
        )}

        {/* Quick Links */}
        <div className="flex flex-col md:flex-row gap-3">
          <Link href="/">
            <PrimaryButton className="w-full cursor-pointer">Return to Home</PrimaryButton>
          </Link>
          <Link href="/dashboard">
            <PrimaryButton className="w-full cursor-pointer">Go to Dashboard</PrimaryButton>
          </Link>
        </div>
      </div>
    </DashboardShell>
  );
}