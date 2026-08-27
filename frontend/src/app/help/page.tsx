"use client";

import { DashboardShell } from "@/components/layout/DashboardShell";
import { TarotCard } from "@/components/ui/TarotCard";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { useState } from "react";
import Link from "next/link";
import { t } from "@/lib/i18n";
import { useAuthStore } from "@/store/useAuthStore";

type DocumentationSection = {
  id: string;
  title: string;
  icon: string;
  description: string;
  contentType: "text" | "table" | "list";
  category: "frontend" | "database" | "api";
};

export default function HelpPage() {
  
  const [activeCategory, setActiveCategory] = useState("frontend");
  const [activeSection, setActiveSection] = useState("frontend-pages");

  const documentationSections: DocumentationSection[] = [
    {
      id: "frontend-pages",
      title: t("app.help.sections.frontend_pages.title", "en"),
      icon: "📄",
      description: t("app.help.sections.frontend_pages.desc", "en"),
      contentType: "table",
      category: "frontend"
    },
    {
      id: "component-guide",
      title: t("app.help.sections.component_guide.title", "en"),
      icon: "🧩",
      description: t("app.help.sections.component_guide.desc", "en"),
      contentType: "list",
      category: "frontend"
    },
    {
      id: "data-flow",
      title: t("app.help.sections.data_flow.title", "en"),
      icon: "🔄",
      description: t("app.help.sections.data_flow.desc", "en"),
      contentType: "text",
      category: "frontend"
    },
    {
      id: "schema-overview",
      title: t("app.help.sections.schema_overview.title", "en"),
      icon: "🗄️",
      description: t("app.help.sections.schema_overview.desc", "en"),
      contentType: "text",
      category: "database"
    },
    {
      id: "api-endpoints",
      title: t("app.help.sections.api_endpoints.title", "en"),
      icon: "🔌",
      description: t("app.help.sections.api_endpoints.desc", "en"),
      contentType: "table",
      category: "api"
    },
  ];

  const frontendPages = [
    { name: false ? "صفحه اصلی" : "Home Page", path: "/", description: false ? "بررسی اجمالی صفحه لندینگ" : "Landing page overview", status: false ? "فعال" : "Working" },
    { name: false ? "صفحه ورود" : "Login Page", path: "/login", description: false ? "رابط احراز هویت" : "Authentication interface", status: false ? "فعال" : "Working" },
    { name: false ? "صفحه ثبت‌نام" : "Register Page", path: "/register", description: false ? "ثبت‌نام کاربر" : "User registration", status: false ? "فعال" : "Working" },
    { name: false ? "داشبورد" : "Dashboard", path: "/dashboard", description: false ? "مرور بازار با آمار" : "Market overview with statistics", status: "Live API" },
    { name: false ? "لیست سهام" : "Stocks List", path: "/stocks", description: false ? "لیست نمادها با قیمت‌ها" : "Symbol list with prices", status: "Live API" },
    { name: false ? "جزئیات سهم" : "Stock Detail", path: "/stocks/[symbol]", description: false ? "تحلیل دارایی تکی" : "Single asset analysis", status: "Live API" },
    { name: false ? "تحلیل" : "Analysis", path: "/analysis", description: false ? "رابط تحلیل چند تب" : "Multi-tab analysis interface", status: "Live API" },
    { name: false ? "پورتفولیو" : "Portfolio", path: "/portfolio", description: false ? "مدیریت پورتفولیو شخصی" : "Personal portfolio management", status: "Live API" },
    { name: false ? "تنظیمات" : "Settings", path: "/settings", description: false ? "پیکربندی و ترجیحات" : "Configuration and preferences", status: false ? "فعال" : "Working" },
    { name: false ? "پروفایل تنظیمات" : "Settings Profile", path: "/settings/profile", description: false ? "مدیریت پروفایل کاربر" : "User profile management", status: false ? "نیاز به همگام‌سازی" : "Needs sync" },
    { name: false ? "اخبار" : "News", path: "/news", description: false ? "تجمیع اخبار بازار" : "Market news aggregation", status: false ? "اصلاح شده" : "Fixed" },
    { name: false ? "هشدارها" : "Alerts", path: "/alerts", description: false ? "اعلان‌های سیستم" : "System notifications", status: "Live API" },
    { name: false ? "امتیازدهی" : "Scoring", path: "/scoring", description: false ? "متدولوژی امتیازدهی 6D" : "6D scoring methodology", status: false ? "فعال" : "Working" },
    { name: false ? "روش‌شناسی" : "Methodology", path: "/methodology", description: false ? "راهنمای توضیح تحلیل" : "Analysis explanation guide", status: false ? "فعال" : "Working" },
    { name: false ? "راهنما" : "Help", path: "/help", description: false ? "مستندات پلتفرم" : "Platform documentation", status: false ? "فعال" : "Working" }
  ];

  const uiComponents = [
    { name: "DashboardShell", type: false ? "طرح‌بندی" : "Layout", description: false ? "لفاف طرح اصلی با احراز هویت و ناوبری" : "Main layout wrapper with auth and navigation" },
    { name: "Sidebar", type: false ? "ناوبری" : "Navigation", description: false ? "نوار کناری ناوبری اصلی با لینک‌های صفحه" : "Main navigation sidebar with page links" },
    { name: "Topbar", type: false ? "ناوبری" : "Navigation", description: false ? "نوار ناوبری بالایی با کنترل‌های تم/زبان" : "Top navigation bar with theme/language controls" },
    { name: "TarotCard", type: false ? "کامپوننت رابط کاربری" : "UI Component", description: false ? "کارت طراحی شده با جلوه‌های هاور و سایه‌ها" : "Styled card with hover effects and shadows" },
    { name: "PrimaryButton", type: false ? "دکمه" : "Button", description: false ? "دکمه اقدام اصلی با جلوه درخشش" : "Primary action button with glow effect" },
    { name: "StatCard", type: false ? "نمایش داده" : "Data Display", description: false ? "نمایش معیارهای آماری با آیکون‌ها" : "Statistical metrics display with icons" },
    { name: "AssetTable", type: false ? "جدول داده" : "Data Table", description: false ? "جدول نمادهای مالی با ستون‌های قیمت" : "Financial symbol table with price columns" },
    { name: "SignalList", type: false ? "نمایش داده" : "Data Display", description: false ? "تجسم سیگنال‌های معاملاتی ML" : "ML trading signals visualization" },
    { name: "NewsList", type: false ? "لیست داده" : "Data List", description: false ? "نمایش مقالات خبری با برچسب زمانی" : "News articles display with timestamps" }
  ];

  const coreTables = [
    { name: "USER", description: false ? "حساب‌های کاربری و احراز هویت" : "User accounts and authentication", rows: 50, columns: 15 },
    { name: "PREFERENCE", description: false ? "تنظیمات و ترجیحات کاربر" : "User settings and preferences", rows: 50, columns: 12 },
    { name: "MARKET_DATA", description: false ? "داده‌های قیمت لحظه‌ای بازار" : "Real-time market price data", rows: 10000, columns: 20 },
    { name: "HISTORICAL_PRICES", description: false ? "داده‌های قیمت تاریخی برای تحلیل" : "Historical price data for analysis", rows: 100000, columns: 15 },
    { name: "STOCK", description: false ? "لیست اصلی اوراق بهادار" : "Master security list", rows: 1000, columns: 25 },
    { name: "INDICE", description: false ? "شاخص‌های بازار و معیارها" : "Market indices and benchmarks", rows: 50, columns: 18 },
    { name: "SIGNAL", description: false ? "سیگنال‌های معاملاتی ML" : "ML trading signals", rows: 1000, columns: 20 },
    { name: "ALERT", description: false ? "اعلان‌های کاربر" : "User notifications", rows: 1000, columns: 15 },
    { name: "FAVORITE", description: false ? "ردیابی موارد علاقه کاربر" : "User favorites tracking", rows: 500, columns: 10 },
    { name: "TRANSACTION_LOG", description: false ? "ردپای حسابرسی تمامی فعالیت‌ها" : "Audit trail of all activities", rows: 5000, columns: 25 }
  ];

  const filteredSections = documentationSections.filter(
    (section) => section.category === activeCategory
  );

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case "frontend":
        return "🌐";
      case "database":
        return "🗄️";
      case "api":
        return "🔌";
      default:
        return "Help";
    }
  };

  return (
    <DashboardShell title={t("app.help.title", "en")}>
      <div className="flex flex-col gap-6">
        {/* Header */}
        <TarotCard icon="📘" title={t("app.help.overview_title", "en")}>
          <p className="text-muted-foreground text-justify">
            {t("app.help.overview_desc", "en")}
          </p>
        </TarotCard>

        {/* Category Tabs */}
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
              className={`px-6 py-3 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${
                activeCategory === cat.id
                  ? "bg-red-600 text-[var(--color-text-primary)] shadow-lg transform scale-105"
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
          <div className="lg:col-span-1 flex flex-col gap-6">
            <TarotCard icon="📂" title={t("app.help.index_title", "en")}>
              <div className="space-y-2">
                {filteredSections.map((section) => (
                  <button
                    key={section.id}
                    onClick={() => setActiveSection(section.id)}
                    className={`w-full text-right p-3 rounded-lg transition-all text-sm ${
                      activeSection === section.id
                        ? "bg-red-50 border border-red-500 text-red-900 dark:bg-red-900/20 dark:text-red-100"
                        : "hover:bg-muted/50 text-muted-foreground"
                    }`}
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

            {/* Quick Access */}
            <TarotCard icon="🚀" title={t("app.help.quick_access", "en")}>
              <div className="space-y-3">
                <Link href="/dashboard" passHref>
                  <PrimaryButton className="w-full cursor-pointer">
                    {t("app.help.go_dashboard", "en")}
                  </PrimaryButton>
                </Link>
                <Link href="/scoring" passHref>
                  <PrimaryButton className="w-full cursor-pointer">
                    {t("app.help.view_scoring", "en")}
                  </PrimaryButton>
                </Link>
              </div>
            </TarotCard>
          </div>

          {/* Main Documentation Area */}
          <div className="lg:col-span-3">
            {/* Frontend Pages Table */}
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
                                page.status === "Live API"
                                  ? "bg-green-500/20 text-green-700"
                                  : page.status === "Needs sync" || page.status === "نیاز به همگام‌سازی"
                                  ? "bg-yellow-500/20 text-yellow-700"
                                  : "bg-blue-500/20 text-blue-700"
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
                  <p className="text-xs text-muted-foreground flex gap-4 flex-wrap">
                    <span><strong>{t("app.help.stats.total_pages", "en")}</strong> 15</span>
                    <span><strong>{t("app.help.stats.live_api", "en")}</strong> 10</span>
                    <span><strong>{t("app.help.stats.static", "en")}</strong> 5</span>
                    <span><strong>{t("app.help.stats.needs_sync", "en")}</strong> 1</span>
                  </p>
                </div>
              </TarotCard>
            )}

            {/* Component Reference */}
            {activeSection === "component-guide" && (
              <TarotCard icon="🧩" title={t("app.help.sections.component_guide.title", "en")}>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {uiComponents.map((comp, i) => (
                    <div
                      key={i}
                      className="border rounded-lg p-4 hover:bg-muted/50 transition-colors"
                    >
                      <div className="flex items-start gap-3">
                        <div className="w-8 h-8 rounded bg-red-100 dark:bg-red-900 flex items-center justify-center text-red-600 font-bold text-sm">
                          {comp.name.charAt(0)}
                        </div>
                        <div className="flex-1">
                          <h4 className="font-semibold text-sm mb-1">{comp.name}</h4>
                          <p className="text-xs text-muted-foreground mb-1">
                            {false ? "نوع:" : "Type:"} {comp.type}
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
              <TarotCard icon="🗄️" title={t("app.help.sections.schema_overview.title", "en")}>
                <div className="space-y-4">
                  {coreTables.map((table, i) => (
                    <div key={i} className="border rounded-lg p-3">
                      <div className="flex items-center justify-between mb-1">
                        <h4 className="font-semibold text-sm">{table.name}</h4>
                        <div className="text-xs text-muted-foreground">
                          {table.rows.toLocaleString()} {false ? "ردیف" : "rows"} |{" "}
                          {table.columns} {false ? "ستون" : "columns"}
                        </div>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        {table.description}
                      </p>
                    </div>
                  ))}
                  <div className="mt-4 p-3 bg-muted/50 rounded-lg">
                    <h5 className="font-medium text-sm mb-2">{false ? "روابط" : "Relationships"}</h5>
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
              <TarotCard icon="🔄" title={t("app.help.sections.data_flow.title", "en")}>
                <div className="space-y-4">
                  <p className="text-sm text-muted-foreground">
                    {false 
                      ? "خط لوله داده کامل انتها به انتها از سرویس‌های بک‌اِند تا نمایش در فرانت‌اِند:"
                      : "Complete end-to-end data pipeline from backend services to frontend display:"}
                  </p>
                  <div className="space-y-3">
                    {[
                      {
                        step: 1,
                        title: false ? "دریافت API" : "API Reception",
                        desc: false ? "فرانت‌اِند نقاط دسترسی امن REST را فراخوانی می‌کند" : "Frontend calls secured REST endpoints"
                      },
                      {
                        step: 2,
                        title: false ? "پردازش داده‌ها" : "Data Processing",
                        desc: false ? "تجزیه و تبدیل پاسخ‌ها" : "Response parsing and transformation"
                      },
                      {
                        step: 3,
                        title: false ? "به‌روزرسانی وضعیت" : "State Update",
                        desc: false ? "هوک‌های React وضعیت کامپوننت را به‌روز می‌کنند" : "React hooks update component state"
                      },
                      {
                        step: 4,
                        title: false ? "رندر" : "Render",
                        desc: false ? "تولید رابط کاربری پویا با رندر مشروط" : "Dynamic UI generation with conditional rendering"
                      }
                    ].map((s) => (
                      <div
                        key={s.step}
                        className="flex items-start gap-3 p-3 border rounded-lg"
                      >
                        <div className="w-6 h-6 rounded-full bg-red-500 text-[var(--color-text-primary)] flex items-center justify-center text-sm font-bold">
                          {s.step}
                        </div>
                        <div className="text-right">
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

            {/* API Endpoints */}
            {activeSection === "api-endpoints" && (
              <TarotCard icon="🔌" title={t("app.help.sections.api_endpoints.title", "en")}>
                <div className="space-y-3">
                  <div className="border rounded p-3">
                    <div className="font-medium text-sm mb-2">
                      /analysis/scoring
                    </div>
                    <p className="text-xs text-muted-foreground">
                      POST - {false ? "امتیازدهی جامع 6D برای یک نماد" : "Comprehensive 6D scoring for a ticker"}
                    </p>
                  </div>
                  <div className="border rounded p-3">
                    <div className="font-medium text-sm mb-2">
                      /analysis/scoring/rank
                    </div>
                    <p className="text-xs text-muted-foreground">
                      POST - {false ? "امتیازدهی و رتبه‌بندی چندین سهم" : "Score and rank multiple stocks"}
                    </p>
                  </div>
                  {[
                    { path: "/market/symbols", method: "GET", desc: false ? "دریافت لیست نمادها" : "Get symbol list" },
                    { path: "/market/latest-prices", method: "GET", desc: false ? "دریافت آخرین قیمت‌ها" : "Get latest prices" },
                    { path: "/analysis/signals-summary", method: "GET", desc: false ? "خلاصه سیگنال‌های تحلیل" : "Analysis signals summary" },
                    { path: "/news/market", method: "GET", desc: false ? "اخبار بازار" : "Market news" }
                  ].map((api, i) => (
                    <div key={i} className="border rounded p-3">
                      <div className="flex justify-between items-center mb-1">
                        <div className="font-medium text-sm">
                          {api.method} {api.path}
                        </div>
                      </div>
                      <p className="text-xs text-muted-foreground">{api.desc}</p>
                    </div>
                  ))}
                </div>
              </TarotCard>
            )}

            {!activeSection && (
              <TarotCard icon="Help" title={false ? "انتخاب یک بخش" : "Select a Section"}>
                <p className="text-muted-foreground text-center py-8">
                  {false 
                    ? "یک بخش از مستندات را از پنل سمت راست انتخاب کنید تا اطلاعات دقیق را مشاهده کنید."
                    : "Select a documentation section from the left panel to view detailed information."}
                </p>
              </TarotCard>
            )}
          </div>
        </div>
      </div>
    </DashboardShell>
  );
}
