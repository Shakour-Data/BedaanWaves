"use client";

import { DashboardShell } from "@/components/layout/DashboardShell";
import { TarotCard } from "@/components/ui/TarotCard";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import Link from "next/link";
import { useState } from "react";

const dimensionDetails = [
  {
    id: "fundamental",
    title: "تحلیل بنیادی (25٪)",
    weight: 25,
    color: "bg-blue-500/20 border-blue-400",
    icon: "💎",
    aspects: [
      { name: "P/E Ratio", desc: "نسبت قیمت به سود" },
      { name: "ROE", desc: "بازده حقوق صاحبان سهام" },
      { name: "Book Value", desc: "ارزش دفتری در هر سهم" },
      { name: "Revenue Growth", desc: "رشد درآمدی سالانه" },
      { name: "Debt-to-Equity", desc: "نسبت بدهی به حقوق صاحبان سهام" }
    ],
  },
  {
    id: "technical",
    title: "تحلیل تکنیکال (20٪)",
    weight: 20,
    color: "bg-green-500/20 border-green-400",
    icon: "📈",
    aspects: [
      { name: "RSI", desc: "شاخص قدرت نسبی" },
      { name: "MACD", desc: "واگرایی و همگرایی میانگین متحرک" },
      { name: "Moving Averages", desc: "میانگین‌های متحرک 50 و 200 روزه" },
      { name: "Bollinger Bands", desc: "باندهای بولینگر" },
      { name: "Volume Profile", desc: "پروفیل حجم معاملات" }
    ],
  },
  {
    id: "sentiment",
    title: "تحلیل احساسات (15٪)",
    weight: 15,
    color: "bg-purple-500/20 border-purple-400",
    icon: "👁️‍🗨️",
    aspects: [
      { name: "News Sentiment", desc: "احساسات خبری" },
      { name: "Social Media", desc: "احساسات شبکه‌های اجتماعی" },
      { name: "Analyst Ratings", desc: "امتیاز تحلیلگران" }
    ],
  },
  {
    id: "risk",
    title: "تحلیل ریسک (20٪)",
    weight: 20,
    color: "bg-red-500/20 border-red-400",
    icon: "⚠️",
    aspects: [
      { name: "Volatility", desc: "نوسان قیمت" },
      { name: "VaR", desc: "ارزش در معرض ریسک" },
      { name: "Sharpe Ratio", desc: "ضریب شارپ" },
      { name: "Max Drawdown", desc: "بیشترین افت قیمت" }
    ],
  },
  {
    id: "macro",
    title: "تحلیل ماکرو (10٪)",
    weight: 10,
    color: "bg-orange-500/20 border-orange-400",
    icon: "🌍",
    aspects: [
      { name: "GDP Growth", desc: "رشد تولید ناخالص داخلی" },
      { name: "Inflation", desc: "نرخ تورم" },
      { name: "Interest Rates", desc: "نرخ بهره" },
      { name: "FX Rates", desc: "نرخ ارز" }
    ],
  },
  {
    id: "ai",
    title: "هوش مصنوعی (10٪)",
    weight: 10,
    color: "bg-cyan-500/20 border-cyan-400",
    icon: "🧠",
    aspects: [
      { name: "LSTM Forecast", desc: "پیش‌بینی قیمت با LSTM" },
      { name: "Pattern Detection", desc: "تشکیل الگوهای نموداری" },
      { name: "Anomaly Detection", desc: "تشخیص ناهنجاری‌ها" }
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
  { label: "AI", defaultWeight: 10, mlOptimized: true }
];

export default function ScoringPage() {
  const [expandedDim, setExpandedDim] = useState(null);

return (
    <DashboardShell title="6D Scoring Methodology">
      <div className="flex flex-col gap-6">
        <TarotCard icon="🧮" title="6D Scoring System">
          <div className="space-y-6 padding">
            <p className="text-justify text-muted-foreground">
              The 6D scoring system evaluates stocks across six dimensions: Fundamental, Technical, Sentiment, Risk, Macro, and AI factors. Each dimension is weighted 25%, 20%, 15%, 20%, 10%, and 10% respectively. The scoring algorithm uses 305 hierarchical nodes across four levels to calculate a final score between 0-100.
            </p>

            <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
              {mlCoefficients.map((w, i) => (
                <div key={i} className="border p-2 rounded bg-muted/30">
                  <div className="flex items-center gap-2">
                    <span className="text-sm">{w.label}</span>
                    <div className="flex items-center">
                      <span className="font-bold text-secondary">{w.defaultWeight}%</span>
                      {w.mlOptimized && <span className="text-xs text-muted-foreground" title="Optimized by ML">🤖</span>}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </TarotCard>

        <TarotCard icon="🧩" title="6 Dimensions">
          {dimensionDetails.map((dim, i) => (
            <div key={dim.id} className="cursor-pointer transition hover:shadow-md">
              <div className="flex items-center gap-3 p-3 rounded-lg border cursor-pointer">
                <span className="text-2xl">{dim.icon}</span>
                <div className="flex-1">
                  <div className="flex items-center">
                    <h4 className="font-semibold">{dim.title}</h4>
                    <span className={`px-2 py-1 rounded text-xs font-bold ${dim.color}`}>Weight: {dim.weight}%</span>
                  </div>
                  <span className="text-xl">{expandedDim === dim.id ? "▼" : "▶"}</span>
                </div>

                {expandedDim === dim.id && (
                  <div className="mt-2 ml-8 border-l-2 border-border/50 pl-4">
                    {dim.aspects.map((a, j) => (
                      <div key={j} className="space-y-2">
                        <div className="font-medium text-sm">{a.name}</div>
                        <div className="text-xs text-muted-foreground">{a.desc}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
        </TarotCard>

        <TarotCard icon="🏆" title="Grading Scale">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
            {grades.map((g, i) => (
              <div key={i} className={`text-center p-3 rounded ${g.bg} border ${g.color}`}>
                <div className={`font-bold text-lg ${g.color}`}>{g.label}</div>
                <div className="mt-1 text-sm text-muted-foreground">
                  {i === 0 ? "≥ 85" : `From ${g.min} to ${grades[i-1]?.min ? grades[i-1].min - 1 : "--"}`}
                </div>
              </div>
            ))}
          </div>
        </TarotCard>

        <TarotCard icon="🤖" title="Machine Learning Optimization">
          <div className="space-y-4">
            <p className="text-sm text-muted-foreground">
              Static weights serve as fallback values. The ML service dynamically optimizes these weights by:
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {dimensionDetails.map((dim, i) => (
                <div key={i} className="border p-2 rounded bg-muted/30">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">{dim.title}</span>
                    <span className="text-sm text-right mr-2">Weight: {dim.weight}%</span>
                  </div>
                  <p className="text-xs text-muted-foreground">Optimized weekly based on historical performance data.</p>
                </div>
              ))}
            </div>
          </div>
        </TarotCard>

        <TarotCard icon="🔗" title="305-Node Hierarchy">
          <div className="grid grid-cols-4 gap-4">
            <div className="p-3 bg-secondary/10 rounded">
              <div className="text-2xl font-bold">6</div>
              <div className="text-xs">Dimensions</div>
            </div>

            <div className="p-3 bg-secondary/10 rounded">
              <div className="text-2xl font-bold">40</div>
              <div className="text-xs">Sub-Dimensions</div>
            </div>

            <div className="p-3 bg-secondary/10 rounded">
              <div className="text-2xl font-bold">80</div>
              <div className="text-xs">Aspects</div>
            </div>

            <div className="p-3 bg-secondary/10 rounded">
              <div className="text-2xl font-bold">173</div>
              <div className="text-xs">Sub-Aspects</div>
            </div>
          </div>
        </TarotCard>

        <div className="flex flex-col md:flex-row gap-3">
          <Link href="/analysis">
            <PrimaryButton className="w-full cursor-pointer">View Current Analysis</PrimaryButton>
          </Link>
          <Link href="/stocks">
            <PrimaryButton className="w-full cursor-pointer">Browse Stocks</PrimaryButton>
          </Link>
        </div>
      </div>
    </DashboardShell>
  );
}