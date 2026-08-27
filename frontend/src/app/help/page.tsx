"use client";

import { DashboardShell } from "@/components/layout/DashboardShell";
import { TarotCard } from "@/components/ui/TarotCard";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { useState } from "react";
import Link from "next/link";
import {
  CodeIcon,
  DatabaseIcon,
  HelpIcon,
  MethodologyIcon,
} from "@/components/icons/Icons";

type DocumentationSection = {
  id: string;
  title: string;
  Icon: React.ComponentType<{ className?: string }>;
  description: string;
  contentType: "text" | "table" | "list";
  category: "frontend" | "database" | "api";
};

const documentationSections: DocumentationSection[] = [
  {
    id: "frontend-pages",
    title: "صفحات فرانت‌اند",
    Icon: CodeIcon,
    description: "لیست کامل تمام صفحات فرانت‌اند با مسیرها، ویژگی‌ها و وضعیت یکپارچگی API",
    contentType: "table",
    category: "frontend",
  },
  {
    id: "component-guide",
    title: "راهنمای کامپوننت‌ها",
    Icon: CodeIcon,
    description: "تمام کامپوننت‌های UI با مثال‌های استفاده و ویژگی‌ها",
    contentType: "list",
    category: "frontend",
  },
  {
    id: "data-flow",
    title: "معماری جریان داده",
    Icon: CodeIcon,
    description: "جریان داده از ابتدا تا انتها از بک‌اند به نمایش فرانت‌اند",
    contentType: "text",
    category: "frontend",
  },
  {
    id: "schema-overview",
    title: "schema پایگاه داده",
    Icon: DatabaseIcon,
    description: "تعریف کامل جداول پایگاه داده و روابط",
    contentType: "text",
    category: "database",
  },
  {
    id: "api-endpoints",
    title: "نقاط پایانی API",
    Icon: MethodologyIcon,
    description: "لیست کامل نقاط پایانی API با پارامترها و پاسخ‌ها",
    contentType: "table",
    category: "api",
  },
];

const frontendPages = [
  { name: "صفحه اصلی", path: "/", description: "صفحه فرود", status: "فعال" },
  { name: "ورود", path: "/login", description: "رابط احراز هویت", status: "فعال" },
  { name: "ثبت نام", path: "/register", description: "ثبت نام کاربر", status: "فعال" },
  { name: "داشبورد", path: "/dashboard", description: "نمای کلی بازار", status: "API زنده" },
  { name: "لیست سهام", path: "/stocks", description: "فهرست نمادها با قیمت", status: "API زنده" },
  { name: "جزئیات نماد", path: "/stocks/[symbol]", description: "تجزیه و تحلیل تک نماد", status: "API زنده" },
  { name: "تحلیل", path: "/analysis", description: "رابط تحلیل چند زبانه", status: "API زنده" },
  { name: "پورتفولیو", path: "/portfolio", description: "مدیریت پورتفولیو شخصی", status: "API زنده" },
  { name: "تنظیمات", path: "/settings", description: "پیکربندی و ترجیحات", status: "فعال" },
  { name: "پروفایل", path: "/settings/profile", description: "مدیریت پروفایل کاربر", status: "نیاز به هماهنگی" },
  { name: "اخبار", path: "/news", description: "تجمیع اخبار بازار", status: "درست شده" },
  { name: "هشدارها", path: "/alerts", description: "اعلان‌های سیستم", status: "API زنده" },
  { name: "امتیازدهی", path: "/scoring", description: "روش‌شناسی امتیازدهی ۶ بعدی", status: "فعال" },
  { name: "روش‌شناسی", path: "/methodology", description: "راهنمای توضیح تحلیل", status: "فعال" },
  { name: "راهنما", path: "/help", description: "مستندات پلتفرم", status: "فعال" },
];

const uiComponents = [
  { name: "DashboardShell", type: "چیدمان", description: "پوسته اصلی چیدمان با احراز هویت و ناوبری" },
  { name: "Sidebar", type: "ناوبری", description: "نوار کناری اصلی با لینک‌های صفحه" },
  { name: "Topbar", type: "ناوبری", description: "نوار بالایی با کنترل‌های تم و زبان" },
  { name: "TarotCard", type: "کامپوننت UI", description: "کارت استایل شده با افکت‌های هاور و سایه" },
  { name: "PrimaryButton", type: "دکمه", description: "دکمه عمل اصلی با افکت درخشان" },
  { name: "StatCard", type: "نمایش داده", description: "نمایش آمار با آیکون" },
  { name: "AssetTable", type: "جدول داده", description: "جدول نمادهای مالی با ستون‌های قیمت" },
  { name: "SignalList", type: "نمایش داده", description: "تجسم سیگنال‌های معاملاتی ML" },
  { name: "NewsList", type: "لیست داده", description: "نمایش مقالات خبری با زمان‌بندی" },
];

const coreTables = [
  { name: "USER", description: "حساب‌های کاربری و احراز هویت", rows: 50, columns: 15 },
  { name: "PREFERENCE", description: "تنظیمات و ترجیحات کاربر", rows: 50, columns: 12 },
  { name: "MARKET_DATA", description: "داده‌های قیمت لحظه‌ای بازار", rows: 10000, columns: 20 },
  { name: "HISTORICAL_PRICES", description: "داده‌های قیمت تاریخی برای تحلیل", rows: 100000, columns: 15 },
  { name: "STOCK", description: "لیست اصلی اوراق", rows: 1000, columns: 25 },
  { name: "INDICE", description: "شاخص‌های بازار و معیارها", rows: 50, columns: 18 },
  { name: "SIGNAL", description: "سیگنال‌های معاملاتی ML", rows: 1000, columns: 20 },
  { name: "ALERT", description: "اعلان‌های کاربر", rows: 1000, columns: 15 },
  { name: "FAVORITE", description: "ردیابی علاقه‌مندی‌های کاربر", rows: 500, columns: 10 },
  { name: "TRANSACTION_LOG", description: "ردیابی تمام فعالیت‌ها", rows: 5000, columns: 25 },
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
        return CodeIcon;
      case "database":
        return DatabaseIcon;
      case "api":
        return MethodologyIcon;
      default:
        return HelpIcon;
    }
  };

  return (
    <DashboardShell title="راهنما و مستندات">
      <div className="flex flex-col gap-6">
        {/* Header */}
        <TarotCard title="سیستم مستندات تعاملی">
          <p className="text-muted-foreground text-justify">
            به سیستم مستندات جامع BedaanWaves خوش آمدید. این مرکز راهنمای یکپارچه
            اطلاعات دقیقی در مورد تمام صفحات فرانت‌اند، کامپوننت‌ها، ساختار پایگاه داده
            و یکپارچگی‌های API ارائه می‌دهد. از سیستم ناوبری برای کاوش مناطق مشخص
            مستندات استفاده کنید.
          </p>
        </TarotCard>

        {/* Category Tabs */}
        <div className="flex flex-wrap gap-3">
          {[
            { id: "frontend", label: "مستندات فرانت‌اند", Icon: CodeIcon },
            { id: "database", label: "مستندات پایگاه داده", Icon: DatabaseIcon },
            { id: "api", label: "مستندات API", Icon: MethodologyIcon },
          ].map((cat) => (
            <button
              key={cat.id}
              onClick={() => {
                setActiveCategory(cat.id);
                const firstSection = documentationSections.find(
                  (s) => s.category === cat.id,
                );
                if (firstSection) setActiveSection(firstSection.id);
              }}
              className={`px-6 py-3 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${
                activeCategory === cat.id
                  ? "bg-blue-500 text-white shadow-lg"
                  : "bg-muted text-muted-foreground hover:bg-muted/80"
              }`}
            >
              <cat.Icon className="h-5 w-5" />
              <span>{cat.label}</span>
            </button>
          ))}
        </div>

        {/* Main Content Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Left Navigation */}
          <div className="lg:col-span-1">
            <TarotCard title="فهرست مستندات">
              <div className="space-y-2">
                {filteredSections.map((section) => (
                  <button
                    key={section.id}
                    onClick={() => setActiveSection(section.id)}
                    className={`w-full text-right p-3 rounded-lg transition-all text-sm ${
                      activeSection === section.id
                        ? "bg-blue-50 border border-blue-500 text-blue-900"
                        : "hover:bg-muted/50 text-muted-foreground"
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <section.Icon className="h-5 w-5" />
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
            <TarotCard title="دسترسی سریع">
              <div className="space-y-3">
                <Link href="/dashboard" passHref>
                  <PrimaryButton className="w-full">
                    رفتن به داشبورد
                  </PrimaryButton>
                </Link>
                <Link href="/scoring" passHref>
                  <PrimaryButton className="w-full">
                    مشاهده سیستم امتیازدهی
                  </PrimaryButton>
                </Link>
              </div>
            </TarotCard>
          </div>

          {/* Main Documentation Area */}
          <div className="lg:col-span-3">
            {/* Frontend Pages Table */}
            {activeSection === "frontend-pages" && (
              <TarotCard title="مستندات صفحات فرانت‌اند">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm border-collapse">
                    <thead>
                      <tr className="border-b-2 border-border">
                        <th className="text-right p-3 font-semibold">صفحه</th>
                        <th className="text-right p-3 font-semibold">مسیر</th>
                        <th className="text-right p-3 font-semibold">توضیحات</th>
                        <th className="text-right p-3 font-semibold">وضعیت</th>
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
                                page.status.includes("API زنده")
                                  ? "bg-green-500/20 text-green-700"
                                  : page.status.includes("نیاز")
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
                  <p className="text-xs text-muted-foreground">
                    <strong>کل صفحات:</strong> 15 |
                    <strong> API زنده:</strong> 10 |
                    <strong> استاتیک:</strong> 5 |
                    <strong> نیاز به هماهنگی:</strong> 1
                  </p>
                </div>
              </TarotCard>
            )}

            {/* Component Reference */}
            {activeSection === "component-guide" && (
              <TarotCard title="راهنمای کامپوننت‌های UI">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {uiComponents.map((comp, i) => (
                    <div
                      key={i}
                      className="border rounded-lg p-4 hover:bg-muted/50 transition-colors"
                    >
                      <div className="flex items-start gap-3">
                        <div className="w-8 h-8 rounded bg-blue-100 flex items-center justify-center text-blue-600 font-bold text-sm">
                          {comp.name.charAt(0)}
                        </div>
                        <div className="flex-1">
                          <h4 className="font-semibold text-sm mb-1">{comp.name}</h4>
                          <p className="text-xs text-muted-foreground mb-1">
                            نوع: {comp.type}
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
              <TarotCard title="نمای کلی Schema پایگاه داده">
                <div className="space-y-4">
                  {coreTables.map((table, i) => (
                    <div key={i} className="border rounded-lg p-3">
                      <div className="flex items-center justify-between mb-1">
                        <h4 className="font-semibold text-sm">{table.name}</h4>
                        <div className="text-xs text-muted-foreground">
                          {table.rows.toLocaleString()} ردیف | {table.columns} ستون
                        </div>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        {table.description}
                      </p>
                    </div>
                  ))}
                  <div className="mt-4 p-3 bg-muted/50 rounded-lg">
                    <h5 className="font-medium text-sm mb-2">روابط</h5>
                    <div className="text-xs space-y-1">
                      <div>• USER ↔ PREFERENCE: یک به یک</div>
                      <div>• USER ↔ ALERT: یک به چند</div>
                      <div>• MARKET_DATA ↔ HISTORICAL_PRICES: یک به چند</div>
                      <div>• STOCK ↔ SIGNAL: یک به چند</div>
                      <div>• INDUSTRY ↔ STOCK: یک به چند</div>
                    </div>
                  </div>
                </div>
              </TarotCard>
            )}

            {/* Data Flow */}
            {activeSection === "data-flow" && (
              <TarotCard title="معماری جریان داده">
                <div className="space-y-4">
                  <p className="text-sm text-muted-foreground">
                    خط کامل داده از سرویس‌های بک‌اند به نمایش فرانت‌اند:
                  </p>
                  <div className="space-y-3">
                    {[
                      {
                        step: 1,
                        title: "دریافت API",
                        desc: "فرانت‌اند نقاط پایانی REST امن را فراخوانی می‌کند",
                      },
                      {
                        step: 2,
                        title: "پردازش داده",
                        desc: "تجزیه و تبدیل پاسخ",
                      },
                      {
                        step: 3,
                        title: "به‌روزرسانی وضعیت",
                        desc: "قلاب‌های React وضعیت کامپوننت را به روز می‌کنند",
                      },
                      {
                        step: 4,
                        title: "رندر",
                        desc: "تولید UI پویا با رندر شرطی",
                      },
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
              <TarotCard title="نقاط پایانی API">
                <div className="space-y-3">
                  <div className="border rounded p-3">
                    <div className="font-medium text-sm mb-2">
                      /analysis/scoring
                    </div>
                    <p className="text-xs text-muted-foreground">
                      POST - امتیازدهی جامع ۶ بعدی برای یک تیکر
                    </p>
                  </div>
                  <div className="border rounded p-3">
                    <div className="font-medium text-sm mb-2">
                      /analysis/scoring/rank
                    </div>
                    <p className="text-xs text-muted-foreground">
                      POST - نمره و رتبه‌بندی چند سهام
                    </p>
                  </div>
                  {[
                    { path: "/market/symbols", method: "GET" },
                    { path: "/market/latest-prices", method: "GET" },
                    { path: "/analysis/signals-summary", method: "GET" },
                    { path: "/news/market", method: "GET" },
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
              <TarotCard title="یک بخش انتخاب کنید">
                <p className="text-muted-foreground text-center py-8">
                  یک بخش مستندات از پنل سمت چپ انتخاب کنید تا اطلاعات دقیق مشاهده شود.
                </p>
              </TarotCard>
            )}
          </div>
        </div>
      </div>
    </DashboardShell>
  );
}
