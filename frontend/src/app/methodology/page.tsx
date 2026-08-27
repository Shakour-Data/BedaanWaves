"use client";

import { DashboardShell } from "@/components/layout/DashboardShell";
import { TarotCard } from "@/components/ui/TarotCard";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import Link from "next/link";
import { useState } from "react";
import {
  ScoringIcon,
  TrendUpIcon,
  AnalysisIcon,
  ChartBarIcon,
  TargetIcon,
  AlertIcon,
  NewspaperIcon,
  CpuIcon,
} from "@/components/icons/Icons";

const analysisMethods = [
  {
    id: "scoring",
    title: "سیستم امتیازدهی ۶ بعدی",
    Icon: ScoringIcon,
    description: "ارزیابی جامع چند بعدی سهام",
    steps: [
      "جمع‌آوری داده‌ها در شش بعد (بنیادی، تکنیکال، احساسات، ریسک، ماکرو، هوش مصنوعی)",
      "محاسبه نمرات فردی (0-100) برای هر بعد",
      "اعمال وزن‌های بهینه‌شده ML به نمرات ابعاد",
      "محاسبه نمره نهایی وزنی و assign نمره (A-E)",
    ],
    details: "با استفاده از سلسله‌مراتب ۴ سطحی با ۳۰۵ گره برای ارزیابی سرمایه‌گذاری در شش بعد با وزن برابر استفاده می‌کند. یادگیری ماشین وزن‌ها را بر اساس عملکرد تاریخی به صورت پویا بهینه می‌کند.",
    apiEndpoints: [
      "/analysis/scoring",
      "/analysis/scoring/rank",
    ],
  },
  {
    id: "ranking",
    title: "سیستم رتبه‌بندی",
    Icon: TrendUpIcon,
    description: "رتبه‌بندی سهام بر اساس معیارهای عملکرد",
    steps: [
      "محاسبه نمرات ۶ بعدی برای تمام اوراق قابل قبول",
      "مرتب‌سازی بر اساس معیار انتخاب شده (نمره کلی یا بعد خاص)",
      "بازگشت N نتیجه برتر (پیش‌فرض: 10)",
    ],
    details: "کاربران می‌توانند بر اساس هر یک از شش بعد یا نمره ترکیبی رتبه‌بندی شوند. نتایج به مدت ۵ دقیقه کشیده می‌شوند تا بار API کاهش یابد.",
    apiEndpoints: [
      "/analysis/scoring/rank",
    ],
  },
  {
    id: "technical",
    title: "تحلیل تکنیکال",
    Icon: AnalysisIcon,
    description: "شاخص‌های مبتنی بر قیمت و حجم",
    steps: [
      "دریافت داده‌های قیمت/حجم تاریخی (حداقل 20 دوره)",
      "محاسبه شاخص‌ها (RSI، MACD، میانگین‌های متحرک، باندهای بولینگر)",
      "تولید سیگنال‌های معاملاتی بر اساس تقاطع‌ها و آستانه‌های شاخص",
    ],
    details: "بیش از ۵۰ شاخص تکنیکال از جمله نوسان‌سنج‌های مومنتوم، ابزارهای دنبال‌کننده روند و معیارهای نوسان ارائه می‌دهد.",
    apiEndpoints: [
      "/analysis/technical/{symbol}",
    ],
  },
  {
    id: "fundamental",
    title: "تحلیل بنیادی",
    Icon: ChartBarIcon,
    description: "تحلیل صورت‌های مالی",
    steps: [
      "دریافت آخرین صورت‌های مالی از CODAL، Yahoo Finance یا Alpha Vantage",
      "محاسبه نسبت‌های کلیدی (P/E، P/B، ROE، بدهی/حقوق، و غیره)",
      "ارزیابی کیفیت سود و پایداری رشد",
    ],
    details: "صورت‌های درآمدی، ترازنامه‌ها و جریان‌های نقدی را از چندین منبع داده جهانی تحلیل می‌کند.",
    apiEndpoints: [
      "/analysis/fundamental/{symbol}",
    ],
  },
  {
    id: "momentum",
    title: "تحلیل مومنتوم",
    Icon: TargetIcon,
    description: "شناسایی روند قیمت کوتاه‌مدت",
    steps: [
      "محاسبه تغییرات قیمت در چند بازه زمانی (۱ روز، ۱ هفته، ۱ ماه، ۳ ماه)",
      "شناسایی دارایی‌ها با قوی‌ترین مومنتوم نسبی",
      "فیلتر کردن سهام با روند صعودی ثابت",
    ],
    details: "بر قدرت نسبی و پایداری روند تمرکز می‌کند تا outperformers احتمالی را شناسایی کند.",
    apiEndpoints: [
      "/analysis/momentum/{symbol}",
    ],
  },
  {
    id: "risk",
    title: "تحلیل ریسک",
    Icon: AlertIcon,
    description: "ارزیابی ریسک نوسان و downside",
    steps: [
      "محاسبه بازده روزانه از داده‌های قیمت تاریخی",
      "محاسبه نوسان (انحراف معیار بازده‌ها)",
      "محاسبه ارزش در معرض ریسک (VaR) و VaR شرطی",
      "تعیین نسبت‌های شارپ، سورترینو و کالمر",
    ],
    details: "معیارهای جامع ریسک از جمله بیشینه افت، بتا و معیارهای ریسک دم را ارائه می‌دهد.",
    apiEndpoints: [
      "/analysis/risk/{symbol}",
      "/analysis/volatility/{symbol}",
    ],
  },
  {
    id: "sentiment",
    title: "تحلیل احساسات",
    Icon: NewspaperIcon,
    description: "احساسات بازار از اخبار و شبکه‌های اجتماعی",
    steps: [
      "جمع‌آوری اخبار مالی و memos شبکه‌های اجتماعی",
      "اعمال مدل‌های NLP برای استخراج نمرات احساس",
      "تجمع احساس بر اساس منبع و دوره زمانی",
    ],
    details: "از مدل‌های NLP مبتنی بر تبدیل‌گر برای تحلیل احساس متن از چندین منبع در زمان واقعی استفاده می‌کند.",
    apiEndpoints: [
      "/analysis/sentiment/{symbol}",
    ],
  },
  {
    id: "ai",
    title: "تحلیل هوش مصنوعی / ML",
    Icon: CpuIcon,
    description: "پیش‌بینی‌های مبتنی بر یادگیری ماشین",
    steps: [
      "آموزش مدل‌های LSTM/Prophet بر روی داده‌های قیمت تاریخی",
      "تولید پیش‌بینی قیمت برای چند افق زمانی",
      "تشخیص الگوهای نموداری و ناهنجاری‌ها با بینایی کامپیوتر",
    ],
    details: "پیش‌بینی سری زمانی، تشخیص الگو و تشخیص ناهنجاری را برای بینش‌های پیش‌بینانه ترکیب می‌کند.",
    apiEndpoints: [
      "/analysis/prediction/{symbol}",
    ],
  },
];

export default function MethodologyPage() {
  const [activeMethod, setActiveMethod] = useState("scoring");

  return (
    <DashboardShell title="روش‌شناسی تحلیل">
      <div className="flex flex-col gap-6">
        {/* Header */}
        <TarotCard title="نمای کلی روش‌شناسی">
          <p className="text-muted-foreground text-justify">
            BedaanWaves از رویکرد چندوجهی به تحلیل مالی استفاده می‌کند و تحلیل بنیادی/تکنیکال سنتی
            را با تکنیک‌های پیشرفته یادگیری ماشین ترکیب می‌کند. هر نوع تحلیل هدف مشخصی در فرآیند
            تصمیم‌گیری سرمایه‌گذاری دارد.
          </p>
        </TarotCard>

        {/* Method Tabs */}
        <div className="flex gap-2 flex-wrap">
          {analysisMethods.map((method) => (
            <button
              key={method.id}
              onClick={() => setActiveMethod(method.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-colors whitespace-nowrap ${
                activeMethod === method.id
                  ? "bg-secondary text-secondary-foreground"
                  : "bg-muted text-muted-foreground hover:bg-muted/80"
              }`}
            >
              <method.Icon className="h-4 w-4" />
              {method.title}
            </button>
          ))}
        </div>

        {/* Active Method Content */}
        {analysisMethods.map((method) => (
          activeMethod === method.id && (
            <TarotCard key={method.id} icon={<method.Icon className="h-5 w-5" />} title={method.title}>
              <div className="space-y-4">
                <p className="text-muted-foreground">{method.description}</p>

                {/* Steps */}
                <div>
                  <h4 className="font-medium mb-2">مراحل فرآیند:</h4>
                  <ol className="list-decimal list-inside space-y-2 text-sm text-muted-foreground">
                    {method.steps.map((step, i) => (
                      <li key={i}>{step}</li>
                    ))}
                  </ol>
                </div>

                {/* Details */}
                <div>
                  <h4 className="font-medium mb-2">جزئیات فنی:</h4>
                  <p className="text-sm text-muted-foreground">{method.details}</p>
                </div>

                {/* API Endpoints */}
                {method.apiEndpoints && (
                  <div>
                    <h4 className="font-medium mb-2">نقاط پایانی API:</h4>
                    <ul className="list-disc list-inside space-y-1 text-sm font-mono">
                      {method.apiEndpoints.map((endpoint, i) => (
                        <li key={i}>{endpoint}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </TarotCard>
          )
        ))}

        {/* Secondary Information */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Capabilities */}
          <TarotCard title="قابلیت‌های کلیدی">
            <ul className="space-y-2 text-sm">
              <li className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-success" aria-hidden="true" />
                <span>پوشش: ایران، جهانی و بازارهای کریپتو</span>
              </li>
              <li className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-success" aria-hidden="true" />
                <span>به‌روزرسانی داده‌های لحظه‌ای (۲۴/۷)</span>
              </li>
              <li className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-success" aria-hidden="true" />
                <span>سیستم وزن‌دهی بهینه‌شده ML</span>
              </li>
              <li className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-success" aria-hidden="true" />
                <span>ترجیحات قابل سفارشی‌سازی کاربر</span>
              </li>
            </ul>
          </TarotCard>

          {/* Disclaimers */}
          <TarotCard title="نکات مهم">
            <div className="space-y-3 text-sm">
              <div>
                <h5 className="font-medium mb-1">سلب مسئولیت:</h5>
                <p className="text-muted-foreground">این یک ابزار تحلیلی است، نه مشاوره مالی.</p>
              </div>
              <div>
                <h5 className="font-medium mb-1">دقت:</h5>
                <p className="text-muted-foreground">نتایج بر اساس داده‌های تاریخی هستند، عملکرد آینده تضمین شده نیست.</p>
              </div>
            </div>
          </TarotCard>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col md:flex-row gap-3">
          <Link href="/scoring">
            <PrimaryButton className="w-full">کاوش امتیازدهی ۶ بعدی</PrimaryButton>
          </Link>
          <Link href="/analysis">
            <PrimaryButton className="w-full">اجرای تحلیل</PrimaryButton>
          </Link>
        </div>
      </div>
    </DashboardShell>
  );
}
