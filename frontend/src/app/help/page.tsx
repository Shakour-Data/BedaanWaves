"use client";

import { DashboardShell } from "@/components/layout/DashboardShell";
import { TarotCard } from "@/components/ui/TarotCard";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { useState } from "react";

type DocumentationSection = {
  id: string;
  title: string;
  icon: string;
  description: string;
  contentType: "text" | "table" | "list";
  category: "frontend" | "database" | "api";
};

const documentationSections: DocumentationSection[] = [
  {
    id: "frontend-pages",
    title: "Frontend Pages",
    icon: "📄",
    description: "Complete list of all frontend pages with paths, features, and API integration status",
    contentType: "table",
    category: "frontend"
  },
  {
    id: "component-guide",
    title: "Component Reference",
    icon: "🧩",
    description: "All UI components with usage examples and properties",
    contentType: "list",
    category: "frontend"
  },
  {
    id: "data-flow",
    title: "Data Flow Architecture",
    icon: "🌊",
    description: "End-to-end data flow from backend to frontend display",
    contentType: "text",
    category: "frontend"
  },
  {
    id: "schema-overview",
    title: "Database Schema",
    icon: "🗄️",
    description: "Complete database table definitions and relationships",
    contentType: "text",
    category: "database"
  },
  {
    id: "api-endpoints",
    title: "API Endpoints",
    icon: "🔌",
    description: "Complete list of API endpoints with parameters and responses",
    contentType: "table",
    category: "api"
  },
];

const frontendPages = [
  { name: "Home Page", path: "/", description: "Landing page overview", status: "✅ Working" },
  { name: "Login Page", path: "/login", description: "Authentication interface", status: "✅ Working" },
  { name: "Register Page", path: "/register", description: "User registration", status: "✅ Working" },
  { name: "Dashboard", path: "/dashboard", description: "Market overview with statistics", status: "✅ Live API" },
  { name: "Stocks List", path: "/stocks", description: "Symbol list with prices", status: "✅ Live API" },
  { name: "Stock Detail", path: "/stocks/[symbol]", description: "Single asset analysis", status: "✅ Live API" },
  { name: "Analysis", path: "/analysis", description: "Multi-tab analysis interface", status: "✅ Live API" },
  { name: "Portfolio", path: "/portfolio", description: "Personal portfolio management", status: "✅ Live API" },
  { name: "Settings", path: "/settings", description: "Configuration and preferences", status: "✅ Working" },
  { name: "Settings Profile", path: "/settings/profile", description: "User profile management", status: "⚠️ Needs sync" },
  { name: "News", path: "/news", description: "Market news aggregation", status: "✅ Fixed" },
  { name: "Alerts", path: "/alerts", description: "System notifications", status: "✅ Live API" },
  { name: "Scoring", path: "/scoring", description: "6D scoring methodology", status: "✅ Working" },
  { name: "Methodology", path: "/methodology", description: "Analysis explanation guide", status: "✅ Working" },
  { name: "Help", path: "/help", description: "Platform documentation", status: "✅ Working" }
];

const uiComponents = [
  { name: "DashboardShell", type: "Layout", description: "Main layout wrapper with auth and navigation" },
  { name: "Sidebar", type: "Navigation", description: "Main navigation sidebar with page links" },
  { name: "Topbar", type: "Navigation", description: "Top navigation bar with theme/language controls" },
  { name: "TarotCard", type: "UI Component", description: "Styled card with hover effects and shadows" },
  { name: "PrimaryButton", type: "Button", description: "Primary action button with glow effect" },
  { name: "StatCard", type: "Data Display", description: "Statistical metrics display with icons" },
  { name: "AssetTable", type: "Data Table", description: "Financial symbol table with price columns" },
  { name: "SignalList", type: "Data Display", description: "ML trading signals visualization" },
  { name: "NewsList", type: "Data List", description: "News articles display with timestamps" }
];

const coreTables = [
  { name: "USER", description: "User accounts and authentication", rows: 50, columns: 15 },
  { name: "PREFERENCE", description: "User settings and preferences", rows: 50, columns: 12 },
  { name: "MARKET_DATA", description: "Real-time market price data", rows: 10000, columns: 20 },
  { name: "HISTORICAL_PRICES", description: "Historical price data for analysis", rows: 100000, columns: 15 },
  { name: "STOCK", description: "Master security list", rows: 1000, columns: 25 },
  { name: "INDICE", description: "Market indices and benchmarks", rows: 50, columns: 18 },
  { name: "SIGNAL", description: "ML trading signals", rows: 1000, columns: 20 },
  { name: "ALERT", description: "User notifications", rows: 1000, columns: 15 },
  { name: "FAVORITE", description: "User favorites tracking", rows: 500, columns: 10 },
  { name: "TRANSACTION_LOG", description: "Audit trail of all activities", rows: 5000, columns: 25 }
];

export default function HelpPage() {
  const [activeCategory, setActiveCategory] = useState("frontend");
  const [activeSection, setActiveSection] = useState("frontend-pages");

  const filteredSections = documentationSections.filter(
    (section) => section.category === activeCategory
  );

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case "frontend":
        return "📱";
      case "database":
        return "🗄️";
      case "api":
        return "🔌";
      default:
        return "📚";
    }
  };

  return (
    <DashboardShell title="Help & Documentation">
      <div className="flex flex-col gap-6">
        {/* Header */}
        <TarotCard icon="📚" title="Interactive Documentation System">
          <p className="text-muted-foreground text-justify">
            Welcome to the BedaanWaves comprehensive documentation system. This
            integrated help center provides detailed information about all
            frontend pages, components, database structure, and API integrations.
            Use the navigation system to explore specific documentation areas.
          </p>
        </TarotCard>

        {/* Category Tabs */}
        <div className="flex flex-wrap gap-3">
          {[
            { id: "frontend", label: "Frontend Docs", icon: "📱" },
            { id: "database", label: "Database Docs", icon: "🗄️" },
            { id: "api", label: "API Docs", icon: "🔌" }
          ].map((cat) => (
            <button
              key={cat.id}
              onClick={() => {
                setActiveCategory(cat.id);
                const firstSection = documentationSections.find(
                  (s) => s.category === cat.id
                );
                if (firstSection) setActiveSection(firstSection.id);
              }}
              className={`px-6 py-3 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${
                activeCategory === cat.id
                  ? "bg-blue-500 text-white shadow-lg transform scale-105"
                  : "bg-muted text-muted-foreground hover:bg-muted/80"
              }`}
            >
              <span className="text-xl">{cat.icon}</span>
              <span>{cat.label}</span>
            </button>
          ))}
        </div>

        {/* Main Content Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Left Navigation */}
          <div className="lg:col-span-1">
            <TarotCard icon="📋" title="Documentation Index">
              <div className="space-y-2">
                {filteredSections.map((section) => (
                  <button
                    key={section.id}
                    onClick={() => setActiveSection(section.id)}
                    className={`w-full text-left p-3 rounded-lg transition-all text-sm ${
                      activeSection === section.id
                        ? "bg-blue-50 border border-blue-500 text-blue-900 dark:bg-blue-900/20 dark:text-blue-100"
                        : "hover:bg-muted/50 text-muted-foreground"
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-lg">{section.icon}</span>
                      <div>
                        <div className="font-medium">{section.title}</div>
                        <div className="text-xs opacity-70">
                          {section.description}
                        </div>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </TarotCard>

            {/* Quick Access */}
            <TarotCard icon="⚡" title="Quick Access">
              <div className="space-y-3">
                <Link href="/dashboard" passHref>
                  <PrimaryButton className="w-full cursor-pointer">
                    Go to Dashboard
                  </PrimaryButton>
                </Link>
                <Link href="/scoring" passHref>
                  <PrimaryButton className="w-full cursor-pointer">
                    View Scoring System
                  </PrimaryButton>
                </Link>
              </div>
            </TarotCard>
          </div>

          {/* Main Documentation Area */}
          <div className="lg:col-span-3">
            {/* Frontend Pages Table */}
            {activeSection === "frontend-pages" && (
              <TarotCard icon="📄" title="Frontend Pages Documentation">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm border-collapse">
                    <thead>
                      <tr className="border-b-2 border-border">
                        <th className="text-left p-3 font-semibold">Page</th>
                        <th className="text-left p-3 font-semibold">Path</th>
                        <th className="text-left p-3 font-semibold">
                          Description
                        </th>
                        <th className="text-left p-3 font-semibold">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {frontendPages.map((page, i) => (
                        <tr
                          key={i}
                          className="border-b border-border/50 hover:bg-muted/30"
                        >
                          <td className="p-3 font-medium">{page.name}</td>
                          <td className="p-3 font-mono text-xs">{page.path}</td>
                          <td className="p-3 text-xs text-muted-foreground">
                            {page.description}
                          </td>
                          <td className="p-3">
                            <span
                              className={`px-2 py-1 rounded text-xs font-medium ${
                                page.status.includes("✅")
                                  ? "bg-green-500/20 text-green-700"
                                  : page.status.includes("⚠️")
                                  ? "bg-yellow-500/20 text-yellow-700"
                                  : "bg-red-500/20 text-red-700"
                              }`}
                            >
                              {page.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="mt-4 p-3 bg-muted/50 rounded-lg">
                  <p className="text-xs text-muted-foreground">
                    <strong>Total Pages:</strong> 15 |
                    <strong> Live API:</strong> 10 |
                    <strong> Static:</strong> 5 |
                    <strong> Needs Sync:</strong> 1
                  </p>
                </div>
              </TarotCard>
            )}

            {/* Component Reference */}
            {activeSection === "component-guide" && (
              <TarotCard icon="🧩" title="UI Component Reference">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {uiComponents.map((comp, i) => (
                    <div
                      key={i}
                      className="border rounded-lg p-4 hover:bg-muted/50 transition-colors"
                    >
                      <div className="flex items-start gap-3">
                        <div className="w-8 h-8 rounded bg-blue-100 dark:bg-blue-900 flex items-center justify-center text-blue-600 font-bold text-sm">
                          {comp.name.charAt(0)}
                        </div>
                        <div className="flex-1">
                          <h4 className="font-semibold text-sm mb-1">{comp.name}</h4>
                          <p className="text-xs text-muted-foreground mb-1">
                            Type: {comp.type}
                          </p>
                          <p className="text-xs">{comp.description}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </TarotCard>
            )}

            {/* Database Schema */}
            {activeSection === "schema-overview" && (
              <TarotCard icon="🗄️" title="Database Schema Overview">
                <div className="space-y-4">
                  {coreTables.map((table, i) => (
                    <div key={i} className="border rounded-lg p-3">
                      <div className="flex items-center justify-between mb-1">
                        <h4 className="font-semibold text-sm">{table.name}</h4>
                        <div className="text-xs text-muted-foreground">
                          {table.rows.toLocaleString()} rows |{" "}
                          {table.columns} columns
                        </div>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        {table.description}
                      </p>
                    </div>
                  ))}
                  <div className="mt-4 p-3 bg-muted/50 rounded-lg">
                    <h5 className="font-medium text-sm mb-2">Relationships</h5>
                    <div className="text-xs space-y-1">
                      <div>• USER ↔ PREFERENCE: One-to-One</div>
                      <div>• USER ↔ ALERT: One-to-Many</div>
                      <div>• MARKET_DATA ↔ HISTORICAL_PRICES: One-to-Many</div>
                      <div>• STOCK ↔ SIGNAL: One-to-Many</div>
                      <div>• INDUSTRY ↔ STOCK: One-to-Many</div>
                    </div>
                  </div>
                </div>
              </TarotCard>
            )}

            {/* Data Flow */}
            {activeSection === "data-flow" && (
              <TarotCard icon="🌊" title="Data Flow Architecture">
                <div className="space-y-4">
                  <p className="text-sm text-muted-foreground">
                    Complete end-to-end data pipeline from backend services to
                    frontend display:
                  </p>
                  <div className="space-y-3">
                    {[
                      {
                        step: 1,
                        title: "API Reception",
                        desc: "Frontend calls secured REST endpoints"
                      },
                      {
                        step: 2,
                        title: "Data Processing",
                        desc: "Response parsing and transformation"
                      },
                      {
                        step: 3,
                        title: "State Update",
                        desc: "React hooks update component state"
                      },
                      {
                        step: 4,
                        title: "Render",
                        desc: "Dynamic UI generation with conditional rendering"
                      }
                    ].map((s) => (
                      <div
                        key={s.step}
                        className="flex items-start gap-3 p-3 border rounded-lg"
                      >
                        <div className="w-6 h-6 rounded-full bg-blue-500 text-white flex items-center justify-center text-sm font-bold">
                          {s.step}
                        </div>
                        <div>
                          <div className="font-medium text-sm">{s.title}</div>
                          <div className="text-xs text-muted-foreground">
                            {s.desc}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </TarotCard>
            )}

            {/* Fallback */}
            {activeSection === "api-endpoints" && (
              <TarotCard icon="🔌" title="API Endpoints">
                <div className="space-y-3">
                  <div className="border rounded p-3">
                    <div className="font-medium text-sm mb-2">
                      /analysis/scoring
                    </div>
                    <p className="text-xs text-muted-foreground">
                      POST - Comprehensive 6D scoring for a ticker
                    </p>
                  </div>
                  <div className="border rounded p-3">
                    <div className="font-medium text-sm mb-2">
                      /analysis/scoring/rank
                    </div>
                    <p className="text-xs text-muted-foreground">
                      POST - Score and rank multiple stocks
                    </p>
                  </div>
                  {[
                    { path: "/market/symbols", method: "GET" },
                    { path: "/market/latest-prices", method: "GET" },
                    { path: "/analysis/signals-summary", method: "GET" },
                    { path: "/news/market", method: "GET" }
                  ].map((api, i) => (
                    <div key={i} className="border rounded p-3">
                      <div className="font-medium text-sm">
                        {api.method} {api.path}
                      </div>
                    </div>
                  ))}
                </div>
              </TarotCard>
            )}

            {!activeSection && (
              <TarotCard icon="❓" title="Select a Section">
                <p className="text-muted-foreground text-center py-8">
                  Select a documentation section from the left panel to
                  view detailed information.
                </p>
              </TarotCard>
            )}
          </div>
        </div>
      </div>
    </DashboardShell>
  );
}