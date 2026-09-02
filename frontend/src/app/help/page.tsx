"use client";

import { useState } from "react";
import Link from "next/link";
import { NewDashboardShell } from "@/components/layout/NewDashboardShell";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { TarotCard } from "@/components/ui/TarotCard";
import { cn } from "@/lib/cn";
import { t } from "@/lib/i18n";

const documentationSections = [
  { id: "frontend-pages", title: "Frontend Pages", description: "Next.js App Router pages and layouts", category: "frontend", icon: "📄" },
  { id: "component-guide", title: "Component Guide", description: "Reusable UI components and patterns", category: "frontend", icon: "🧩" },
  { id: "schema-overview", title: "Database Schema", description: "PostgreSQL tables and relationships", category: "database", icon: "🗄️" },
  { id: "api-reference", title: "API Reference", description: "FastAPI endpoints and authentication", category: "api", icon: "🔌" },
];

const frontendPages = [
  { name: "Dashboard", path: "/dashboard", description: "Main market overview with indices and stocks", status: "Live API" },
  { name: "Stocks", path: "/stocks", description: "Stock list with search and filters", status: "Live API" },
  { name: "Stock Detail", path: "/stocks/[symbol]", description: "Candlestick chart and scoring", status: "Live API" },
  { name: "Scoring", path: "/scoring", description: "6-dimensional AI scoring overview", status: "Live API" },
  { name: "Analysis", path: "/analysis", description: "Risk analysis and fundamentals", status: "Live API" },
  { name: "Portfolio", path: "/portfolio", description: "User portfolio tracking", status: "Live API" },
  { name: "News", path: "/news", description: "Market news aggregation", status: "Live API" },
  { name: "Alerts", path: "/alerts", description: "Price alerts", status: "Live API" },
  { name: "Ranking", path: "/ranking", description: "NASDAQ stock ranking table", status: "Live API" },
  { name: "Settings", path: "/settings", description: "Market preferences and notifications", status: "Live API" },
  { name: "Profile", path: "/settings/profile", description: "User profile management", status: "Live API" },
  { name: "Help", path: "/help", description: "Documentation and support", status: "Static" },
  { name: "Methodology", path: "/methodology", description: "Scoring methodology", status: "Static" },
  { name: "Login", path: "/login", description: "User authentication", status: "Live API" },
  { name: "Register", path: "/register", description: "New user registration", status: "Live API" },
];

const coreTables = [
  { name: "users", rows: 1250, columns: 12 },
  { name: "assets", rows: 4500, columns: 18 },
  { name: "price_history", rows: 2400000, columns: 8 },
  { name: "scoring_results", rows: 89000, columns: 15 },
  { name: "user_portfolios", rows: 5600, columns: 9 },
];

const uiComponents = [
  { name: "StockSearchBar", type: "Component", description: "Accessible combobox with fuzzy search and keyboard navigation" },
  { name: "CandlestickChart", type: "Component", description: "OHLCV candlestick chart with volume histogram" },
  { name: "StatCard", type: "Component", description: "Dashboard metric card with change badge" },
  { name: "NewSidebar", type: "Layout", description: "Responsive navigation sidebar with active state" },
  { name: "NewTopbar", type: "Layout", description: "Fixed header with search, notifications, and user menu" },
  { name: "Button", type: "Primitive", description: "Unified button with 5 variants and 3 sizes" },
  { name: "Card", type: "Primitive", description: "Consistent card container with title, footer, and hover effects" },
];

export default function HelpPage() {
  const [activeCategory, setActiveCategory] = useState("frontend");
  const [activeSection, setActiveSection] = useState("frontend-pages");

  const filteredSections = documentationSections.filter(
    (s) => s.category === activeCategory
  );

  return (
    <NewDashboardShell title={t("app.help.title", "en")}>
      <div className="flex flex-col gap-6">
        <div>
          <h1 className="text-2xl font-bold text-foreground">{t("app.help.title", "en")}</h1>
          <p className="text-muted-foreground">{t("app.help.subtitle", "en")}</p>
        </div>

        <div className="flex flex-wrap gap-3">
          {[
            { id: "frontend", label: t("app.help.categories.frontend", "en"), icon: "🌐" },
            { id: "database", label: t("app.help.categories.database", "en"), icon: "🗄️" },
            { id: "api", label: t("app.help.categories.api", "en"), icon: "🔌" }
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
              className={cn(
                "px-6 py-3 rounded-lg text-sm font-medium transition-all flex items-center gap-2",
                activeCategory === cat.id
                  ? "bg-error text-white shadow-lg"
                  : "bg-muted text-muted-foreground hover:bg-muted/80"
              )}
            >
              <span className="text-xl">{cat.icon}</span>
              <span>{cat.label}</span>
            </button>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          <div className="lg:col-span-1 flex flex-col gap-6">
            <TarotCard icon="📂" title={t("app.help.index_title", "en")}>
              <div className="space-y-2">
                {filteredSections.map((section) => (
                  <button
                    key={section.id}
                    onClick={() => setActiveSection(section.id)}
                    className={cn(
                      "w-full text-right p-3 rounded-lg transition-all text-sm",
                      activeSection === section.id
                        ? "bg-primary-light border border-primary text-primary"
                        : "hover:bg-muted/50 text-muted-foreground"
                    )}
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-lg">{section.icon}</span>
                      <div className="text-right">
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

            <TarotCard icon="🚀" title={t("app.help.quick_access", "en")}>
              <div className="space-y-3">
                <Link href="/dashboard" passHref>
                  <Button className="w-full cursor-pointer">
                    {t("app.help.go_dashboard", "en")}
                  </Button>
                </Link>
                <Link href="/scoring" passHref>
                  <Button className="w-full cursor-pointer">
                    {t("app.help.view_scoring", "en")}
                  </Button>
                </Link>
              </div>
            </TarotCard>
          </div>

          <div className="lg:col-span-3">
            {activeSection === "frontend-pages" && (
              <TarotCard icon="📄" title={t("app.help.sections.frontend_pages.title", "en")}>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm border-collapse">
                    <thead>
                      <tr className="border-b-2 border-border">
                        <th className="text-right p-3 font-semibold">{t("app.help.table.page", "en")}</th>
                        <th className="text-right p-3 font-semibold">{t("app.help.table.path", "en")}</th>
                        <th className="text-right p-3 font-semibold">
                          {t("app.help.table.description", "en")}
                        </th>
                        <th className="text-right p-3 font-semibold">{t("app.help.table.status", "en")}</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                      {frontendPages.map((page, i) => (
                        <tr key={i} className="transition-colors hover:bg-muted/30">
                          <td className="p-3 font-medium">{page.name}</td>
                          <td className="p-3 font-mono text-xs">{page.path}</td>
                          <td className="p-3 text-xs text-muted-foreground">
                            {page.description}
                          </td>
                          <td className="p-3">
                            <Badge variant={page.status === "Live API" ? "success" : page.status === "Needs sync" || page.status === "نیاز به همگام‌سازی" ? "warning" : "info"}>
                              {page.status}
                            </Badge>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="mt-4 p-3 bg-muted/50 rounded-lg">
                  <p className="text-xs text-muted-foreground flex gap-4 flex-wrap">
                    <span><strong>{t("app.help.stats.total_pages", "en")}</strong> 15</span>
                    <span><strong>{t("app.help.stats.live_api", "en")}</strong> 10</span>
                    <span><strong>{t("app.help.stats.static", "en")}</strong> 5</span>
                    <span><strong>{t("app.help.stats.needs_sync", "en")}</strong> 1</span>
                  </p>
                </div>
              </TarotCard>
            )}

            {activeSection === "component-guide" && (
              <TarotCard icon="🧩" title={t("app.help.sections.component_guide.title", "en")}>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {uiComponents.map((comp, i) => (
                    <div
                      key={i}
                      className="border border-border rounded-lg p-4 hover:bg-muted/50 transition-colors"
                    >
                      <div className="flex items-start gap-3">
                        <div className="w-8 h-8 rounded bg-error/10 flex items-center justify-center text-error font-bold text-sm">
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

            {activeSection === "schema-overview" && (
              <TarotCard icon="🗄️" title={t("app.help.sections.schema_overview.title", "en")}>
                <div className="space-y-4">
                  {coreTables.map((table, i) => (
                    <div key={i} className="border border-border rounded-lg p-3">
                      <div className="flex items-center justify-between mb-1">
                        <h4 className="font-semibold text-sm">{table.name}</h4>
                        <div className="text-xs text-muted-foreground">
                          {table.rows.toLocaleString()} rows |{" "}
                          {table.columns} columns
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </TarotCard>
            )}

            {activeSection === "api-reference" && (
              <TarotCard icon="🔌" title={t("app.help.sections.api_reference.title", "en")}>
                <p className="text-muted-foreground">
                  API documentation is available in the backend codebase under <code className="px-1.5 py-0.5 rounded bg-muted text-xs">backend/app/</code>.
                  All endpoints require Bearer token authentication.
                </p>
              </TarotCard>
            )}
          </div>
        </div>
      </div>
    </NewDashboardShell>
  );
}
