"use client";

import { DashboardShell } from "@/components/layout/DashboardShell";
import { TarotCard } from "@/components/ui/TarotCard";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import Link from "next/link";
import { useState, useEffect } from "react";
import { apiClient } from "@/lib/api";
import {
  ChartBarIcon,
  AnalysisIcon,
  NewspaperIcon,
  AlertIcon,
  GlobeIcon,
  CpuIcon,
  ChevronDownIcon,
} from "@/components/icons/Icons";

const dimensionDetails = [
  {
    id: "fundamental",
    title: "تحلیل بنیادی (25٪)",
    weight: 25,
    color: "bg-blue-500/20 border-blue-400",
    Icon: ChartBarIcon,
    aspects: [
      { name: "P/E Ratio", desc: "نسبت قیمت به سود" },
      { name: "ROE", desc: "بازده حقوق صاحبان سهام" },
      { name: "Book Value", desc: "ارزش دفتری در هر سهم" },
      { name: "Revenue Growth", desc: "رشد درآمدی سالانه" },
      { name: "Debt-to-Equity", desc: "نسبت بدهی به حقوق صاحبان سهام" },
    ],
  },
  {
    id: "technical",
    title: "تحلیل تکنیکال (20٪)",
    weight: 20,
    color: "bg-green-500/20 border-green-400",
    Icon: AnalysisIcon,
    aspects: [
      { name: "RSI", desc: "شاخص قدرت نسبی" },
      { name: "MACD", desc: "واگرایی و همگرایی میانگین متحرک" },
      { name: "Moving Averages", desc: "میانگین‌های متحرک 50 و 200 روزه" },
      { name: "Bollinger Bands", desc: "باندهای بولینگر" },
      { name: "Volume Profile", desc: "پروفیل حجم معاملات" },
    ],
  },
  {
    id: "sentiment",
    title: "تحلیل احساسات (15٪)",
    weight: 15,
    color: "bg-purple-500/20 border-purple-400",
    Icon: NewspaperIcon,
    aspects: [
      { name: "News Sentiment", desc: "احساسات خبری" },
      { name: "Social Media", desc: "احساسات شبکه‌های اجتماعی" },
      { name: "Analyst Ratings", desc: "امتیاز تحلیلگران" },
    ],
  },
  {
    id: "risk",
    title: "تحلیل ریسک (20٪)",
    weight: 20,
    color: "bg-red-500/20 border-red-400",
    Icon: AlertIcon,
    aspects: [
      { name: "Volatility", desc: "نوسان قیمت" },
      { name: "VaR", desc: "ارزش در معرض ریسک" },
      { name: "Sharpe Ratio", desc: "ضریب شارپ" },
      { name: "Max Drawdown", desc: "بیشترین افت قیمت" },
    ],
  },
  {
    id: "macro",
    title: "تحلیل ماکرو (10٪)",
    weight: 10,
    color: "bg-orange-500/20 border-orange-400",
    Icon: GlobeIcon,
    aspects: [
      { name: "GDP Growth", desc: "رشد تولید ناخالص داخلی" },
      { name: "Inflation", desc: "نرخ تورم" },
      { name: "Interest Rates", desc: "نرخ بهره" },
      { name: "FX Rates", desc: "نرخ ارز" },
    ],
  },
  {
    id: "ai",
    title: "هوش مصنوعی (10٪)",
    weight: 10,
    color: "bg-cyan-500/20 border-cyan-400",
    Icon: CpuIcon,
    aspects: [
      { name: "LSTM Forecast", desc: "پیش‌بینی قیمت با LSTM" },
      { name: "Pattern Detection", desc: "تشکیل الگوهای نموداری" },
      { name: "Anomaly Detection", desc: "تشخیص ناهنجاری‌ها" },
    ],
  },
];

const grades = [
  { label: "A (خرید قوی)", min: 85, color: "text-green-600", bg: "bg-green-500/20" },
  { label: "B (خرید)", min: 70, color: "text-emerald-600", bg: "bg-emerald-500/20" },
  { label: "C (نگهداری)", min: 55, color: "text-yellow-600", bg: "bg-yellow-500/20" },
  { label: "D (فروش)", min: 40, color: "text-orange-600", bg: "bg-orange-500/20" },
  { label: "E (فروش قوی)", min: 0, color: "text-red-600", bg: "bg-red-500/20" },
];

const mlCoefficients = [
  { label: "Fundamental", defaultWeight: 25, mlOptimized: true },
  { label: "Technical", defaultWeight: 20, mlOptimized: true },
  { label: "Sentiment", defaultWeight: 15, mlOptimized: true },
  { label: "Risk", defaultWeight: 20, mlOptimized: true },
  { label: "Macro", defaultWeight: 10, mlOptimized: true },
  { label: "AI", defaultWeight: 10, mlOptimized: true },
];

export default function ScoringPage() {
  const [expandedDim, setExpandedDim] = useState<string | null>(null);
  const [scoringData, setScoringData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [ticker, setTicker] = useState("AAPL");
  const [market, setMarket] = useState("NASDAQ");

  useEffect(() => {
    let active = true;
    async function loadScoring() {
      setLoading(true);
      try {
        const res = await apiClient.post<any>("/analysis/scoring", {
          ticker,
          market,
        });
        if (active && res.data?.status === "success") {
          setScoringData(res.data.scoring);
        }
      } catch {
        // keep fallback data
      } finally {
        if (active) setLoading(false);
      }
    }
    loadScoring();
    return () => {
      active = false;
    };
  }, [ticker, market]);

  return (
    <DashboardShell title="امتیازدهی ۶ بعدی">
      <div className="flex flex-col gap-6">
        <TarotCard title="Symbol Scoring">
          <div className="flex flex-wrap items-end gap-3">
            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium text-[#1E293B]">Ticker</label>
              <input
                type="text"
                value={ticker}
                onChange={(e) => setTicker(e.target.value.toUpperCase())}
                placeholder="AAPL"
                className="w-40 rounded-xl border border-[#E2E8F0] bg-white px-3 py-2 text-sm outline-none transition focus:border-[#005A9C] focus:ring-2 focus:ring-[#005A9C]/20"
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium text-[#1E293B]">Market</label>
              <select
                value={market}
                onChange={(e) => setMarket(e.target.value)}
                className="rounded-xl border border-[#E2E8F0] bg-white px-3 py-2 text-sm outline-none transition focus:border-[#005A9C] focus:ring-2 focus:ring-[#005A9C]/20"
              >
                <option value="NASDAQ">NASDAQ</option>
                <option value="NYSE">NYSE</option>
                <option value="TSE">TSE</option>
                <option value="BINANCE">Crypto</option>
              </select>
            </div>
            <p className="text-xs text-muted-foreground"> scoring updates automatically when you change the ticker.</p>
          </div>
        </TarotCard>

        <TarotCard title="سیستم امتیازدهی ۶ بعدی">
          <div className="space-y-4">
            <p className="text-justify text-muted-foreground">
              سیستم امتیازدهی ۶ بعدی سهام را در شش بعد ارزیابی می‌کند: بنیادی، تکنیکال، احساسات، ریسک، ماکرو و هوش مصنوعی. هر بعد به ترتیب با وزن‌های 25٪، 20٪، 15٪، 20٪، 10٪ و 10٪ محاسبه می‌شود. الگوریتم امتیازدهی از 305 گره سلسله‌مراتبی در چهار سطح برای محاسبه نمره نهایی بین 0 تا 100 استفاده می‌کند.
            </p>

            <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
              {mlCoefficients.map((w, i) => (
                <div key={i} className="border p-2 rounded bg-muted/30">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-sm">{w.label}</span>
                    <div className="flex items-center gap-1">
                      <span className="font-bold text-secondary">{w.defaultWeight}%</span>
                      {w.mlOptimized && (
                        <span className="h-2 w-2 rounded-full bg-success" title="بهینه‌شده توسط ML" />
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </TarotCard>

        <TarotCard title="۶ بعد تحلیل">
          <div className="space-y-2">
            {dimensionDetails.map((dim) => (
              <div
                key={dim.id}
                className="rounded-lg border p-3 transition hover:shadow-md"
              >
                <div
                  className="flex cursor-pointer items-center justify-between gap-3"
                  onClick={() => setExpandedDim(expandedDim === dim.id ? null : dim.id)}
                >
                  <div className="flex items-center gap-3">
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
                      <dim.Icon className="h-4 w-4" />
                    </div>
                    <div>
                      <h4 className="font-semibold">{dim.title}</h4>
                      <span className={`px-2 py-1 rounded text-xs font-bold ${dim.color}`}>
                        وزن: {dim.weight}٪
                      </span>
                    </div>
                  </div>
                  <ChevronDownIcon className={`h-4 w-4 text-muted-foreground transition-transform ${expandedDim === dim.id ? "rotate-180" : ""}`} />
                </div>

                {expandedDim === dim.id && (
                  <div className="mt-3 mr-8 border-r-2 border-border/50 pr-4 space-y-2">
                    {dim.aspects.map((a, j) => (
                      <div key={j} className="space-y-1">
                        <div className="font-medium text-sm">{a.name}</div>
                        <div className="text-xs text-muted-foreground">{a.desc}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </TarotCard>

        <TarotCard title="میزان نمره‌دهی">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            {grades.map((g, i) => (
              <div key={i} className={`text-center p-3 rounded border ${g.bg} ${g.color}`}>
                <div className={`font-bold text-lg ${g.color}`}>{g.label}</div>
                <div className="mt-1 text-sm text-muted-foreground">
                  {i === 0 ? "≥ 85" : `از ${g.min} تا ${grades[i - 1]?.min ? grades[i - 1].min - 1 : "--"}`}
                </div>
              </div>
            ))}
          </div>
        </TarotCard>

        <TarotCard title="بهینه‌سازی یادگیری ماشین">
          <div className="space-y-4">
            <p className="text-sm text-muted-foreground">
              وزن‌های ثابت به عنوان مقادیر جایگزین عمل می‌کنند. سرویس ML این وزن‌ها را به صورت پویا با استفاده از داده‌های تاریخی بهینه می‌کند:
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {dimensionDetails.map((dim, i) => (
                <div key={i} className="border p-3 rounded bg-muted/30">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">{dim.title}</span>
                    <span className="text-sm font-medium">{dim.weight}%</span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    بهینه‌سازی هفتگی بر اساس عملکرد تاریخی
                  </p>
                </div>
              ))}
            </div>
          </div>
        </TarotCard>

        <TarotCard title="سلسله‌مراتب ۳۰۵ گره">
          {loading ? (
            <div className="flex min-h-[120px] items-center justify-center text-muted-foreground">
              در حال بارگذاری...
            </div>
          ) : scoringData ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-4 bg-secondary/10 rounded text-center">
                <div className="text-3xl font-bold">6</div>
                <div className="text-xs text-muted-foreground">بعد</div>
              </div>
              <div className="p-4 bg-secondary/10 rounded text-center">
                <div className="text-3xl font-bold">40</div>
                <div className="text-xs text-muted-foreground">زیربعد</div>
              </div>
              <div className="p-4 bg-secondary/10 rounded text-center">
                <div className="text-3xl font-bold">80</div>
                <div className="text-xs text-muted-foreground">جوانب</div>
              </div>
              <div className="p-4 bg-secondary/10 rounded text-center">
                <div className="text-3xl font-bold">173</div>
                <div className="text-xs text-muted-foreground">زیرجوانب</div>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-4 bg-secondary/10 rounded text-center">
                <div className="text-3xl font-bold">6</div>
                <div className="text-xs text-muted-foreground">بعد</div>
              </div>
              <div className="p-4 bg-secondary/10 rounded text-center">
                <div className="text-3xl font-bold">40</div>
                <div className="text-xs text-muted-foreground">زیربعد</div>
              </div>
              <div className="p-4 bg-secondary/10 rounded text-center">
                <div className="text-3xl font-bold">80</div>
                <div className="text-xs text-muted-foreground">جوانب</div>
              </div>
              <div className="p-4 bg-secondary/10 rounded text-center">
                <div className="text-3xl font-bold">173</div>
                <div className="text-xs text-muted-foreground">زیرجوانب</div>
              </div>
            </div>
          )}
        </TarotCard>

        <div className="flex flex-col md:flex-row gap-3">
          <Link href="/analysis">
            <PrimaryButton className="w-full">مشاهده تحلیل‌های فعلی</PrimaryButton>
          </Link>
          <Link href="/stocks">
            <PrimaryButton className="w-full">مرور سهام</PrimaryButton>
          </Link>
        </div>
      </div>
    </DashboardShell>
  );
}
