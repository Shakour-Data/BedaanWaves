"use client";

import { DashboardShell } from "@/components/layout/DashboardShell";
import { TarotCard } from "@/components/ui/TarotCard";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import Link from "next/link";
import { useEffect, useState } from "react";
import { fetchScoring, fetchSymbols, type Asset } from "@/lib/api/stocks";
import { Input } from "@/components/ui/input";
import { PageLoading } from "@/components/ui/PageLoading";

const dimensionDetails = [
  {
    id: "fundamental",
    title: "تحلیل بنیادی (25٪)",
    weight: 25,
    color: "bg-blue-500/20 border-blue-400",
    icon: "",
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
    icon: "",
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
    icon: "️‍️",
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
    icon: "️",
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
    icon: "",
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
    icon: "",
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

import { t } from "@/lib/i18n";
import { useAuthStore } from "@/store/useAuthStore";

export default function ScoringPage() {
  const { currentLang } = useAuthStore();
  const [expandedDim, setExpandedDim] = useState(null);
  const [search, setSearch] = useState("");
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null);
  const [scoringData, setScoringData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<Asset[]>([]);

  const dimensionDetails = [
    {
      id: "fundamental",
      title: `${t("app.scoring.dimensions.fundamental", currentLang)} (25٪)`,
      weight: 25,
      color: "bg-blue-500/20 border-blue-400",
      icon: "🏦",
      aspects: [
        { name: "P/E Ratio", desc: currentLang === "fa" ? "نسبت قیمت به سود" : "Price-to-Earnings Ratio" },
        { name: "ROE", desc: currentLang === "fa" ? "بازده حقوق صاحبان سهام" : "Return on Equity" },
        { name: "Book Value", desc: currentLang === "fa" ? "ارزش دفتری در هر سهم" : "Book Value per Share" },
        { name: "Revenue Growth", desc: currentLang === "fa" ? "رشد درآمدی سالانه" : "Annual Revenue Growth" },
        { name: "Debt-to-Equity", desc: currentLang === "fa" ? "نسبت بدهی به حقوق صاحبان سهام" : "Debt-to-Equity Ratio" }
      ],
    },
    {
      id: "technical",
      title: `${t("app.scoring.dimensions.technical", currentLang)} (20٪)`,
      weight: 20,
      color: "bg-green-500/20 border-green-400",
      icon: "📈",
      aspects: [
        { name: "RSI", desc: currentLang === "fa" ? "شاخص قدرت نسبی" : "Relative Strength Index" },
        { name: "MACD", desc: currentLang === "fa" ? "واگرایی و همگرایی میانگین متحرک" : "Moving Average Convergence Divergence" },
        { name: "Moving Averages", desc: currentLang === "fa" ? "میانگین‌های متحرک 50 و 200 روزه" : "50 and 200-day Moving Averages" },
        { name: "Bollinger Bands", desc: currentLang === "fa" ? "باندهای بولینگر" : "Bollinger Bands" },
        { name: "Volume Profile", desc: currentLang === "fa" ? "پروفیل حجم معاملات" : "Volume Profile" }
      ],
    },
    {
      id: "sentiment",
      title: `${t("app.scoring.dimensions.sentiment", currentLang)} (15٪)`,
      weight: 15,
      color: "bg-purple-500/20 border-purple-400",
      icon: "🎭",
      aspects: [
        { name: "News Sentiment", desc: currentLang === "fa" ? "احساسات خبری" : "News Sentiment" },
        { name: "Social Media", desc: currentLang === "fa" ? "احساسات شبکه‌های اجتماعی" : "Social Media Sentiment" },
        { name: "Analyst Ratings", desc: currentLang === "fa" ? "امتیاز تحلیلگران" : "Analyst Ratings" }
      ],
    },
    {
      id: "risk",
      title: `${t("app.scoring.dimensions.risk", currentLang)} (20٪)`,
      weight: 20,
      color: "bg-red-500/20 border-red-400",
      icon: "🛡️",
      aspects: [
        { name: "Volatility", desc: currentLang === "fa" ? "نوسان قیمت" : "Price Volatility" },
        { name: "VaR", desc: currentLang === "fa" ? "ارزش در معرض ریسک" : "Value at Risk" },
        { name: "Sharpe Ratio", desc: currentLang === "fa" ? "ضریب شارپ" : "Sharpe Ratio" },
        { name: "Max Drawdown", desc: currentLang === "fa" ? "بیشترین افت قیمت" : "Maximum Drawdown" }
      ],
    },
    {
      id: "macro",
      title: `${t("app.scoring.dimensions.macro", currentLang)} (10٪)`,
      weight: 10,
      color: "bg-orange-500/20 border-orange-400",
      icon: "🌍",
      aspects: [
        { name: "GDP Growth", desc: currentLang === "fa" ? "رشد تولید ناخالص داخلی" : "GDP Growth" },
        { name: "Inflation", desc: currentLang === "fa" ? "نرخ تورم" : "Inflation Rate" },
        { name: "Interest Rates", desc: currentLang === "fa" ? "نرخ بهره" : "Interest Rates" },
        { name: "FX Rates", desc: currentLang === "fa" ? "نرخ ارز" : "Foreign Exchange Rates" }
      ],
    },
    {
      id: "ai",
      title: `${t("app.scoring.dimensions.ai", currentLang)} (10٪)`,
      weight: 10,
      color: "bg-cyan-500/20 border-cyan-400",
      icon: "🤖",
      aspects: [
        { name: "LSTM Forecast", desc: currentLang === "fa" ? "پیش‌بینی قیمت با LSTM" : "Price Forecasting with LSTM" },
        { name: "Pattern Detection", desc: currentLang === "fa" ? "تشکیل الگوهای نموداری" : "Chart Pattern Detection" },
        { name: "Anomaly Detection", desc: currentLang === "fa" ? "تشخیص ناهنجاری‌ها" : "Anomaly Detection" }
      ],
    },
  ];

  const grades = [
    { label: currentLang === "fa" ? "A (خرید قوی)" : "A (Strong Buy)", min: 85, color: "text-green-600", bg: "bg-green-500/20" },
    { label: currentLang === "fa" ? "B (خرید)" : "B (Buy)", min: 70, color: "text-emerald-600", bg: "bg-emerald-500/20" },
    { label: currentLang === "fa" ? "C (نگهداری)" : "C (Hold)", min: 55, color: "text-yellow-600", bg: "bg-yellow-500/20" },
    { label: currentLang === "fa" ? "D (فروش)" : "D (Sell)", min: 40, color: "text-orange-600", bg: "bg-orange-500/20" },
    { label: currentLang === "fa" ? "E (فروش قوی)" : "E (Strong Sell)", min: 0, color: "text-red-600", bg: "bg-red-500/20" },
  ];

  const mlCoefficients = [
    { label: t("app.scoring.dimensions.fundamental", currentLang), defaultWeight: 25, mlOptimized: true },
    { label: t("app.scoring.dimensions.technical", currentLang), defaultWeight: 20, mlOptimized: true },
    { label: t("app.scoring.dimensions.sentiment", currentLang), defaultWeight: 15, mlOptimized: true },
    { label: t("app.scoring.dimensions.risk", currentLang), defaultWeight: 20, mlOptimized: true },
    { label: t("app.scoring.dimensions.macro", currentLang), defaultWeight: 10, mlOptimized: true },
    { label: t("app.scoring.dimensions.ai", currentLang), defaultWeight: 10, mlOptimized: true }
  ];

  useEffect(() => {
    if (search.length > 1) {
      fetchSymbols({ limit: 5 }).then(assets => {
        setSuggestions(assets.filter(a => 
          a.symbol.toLowerCase().includes(search.toLowerCase()) || 
          a.name.toLowerCase().includes(search.toLowerCase())
        ));
      });
    } else {
      setSuggestions([]);
    }
  }, [search]);

  const handleSelect = async (symbol: string) => {
    setSearch(symbol);
    setSuggestions([]);
    setSelectedSymbol(symbol);
    setLoading(true);
    try {
      const data = await fetchScoring(symbol);
      setScoringData(data);
    } catch (error) {
      console.error("Error fetching scoring:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <DashboardShell title={t("app.scoring.title", currentLang)}>
      <div className="flex flex-col gap-6">
        {/* Symbol Search */}
        <TarotCard icon="🔍" title={t("app.scoring.search_title", currentLang)}>
          <div className="relative">
            <Input
              type="text"
              placeholder={t("app.scoring.search_placeholder", currentLang)}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full"
            />
            {suggestions.length > 0 && (
              <div className="absolute z-10 w-full mt-1 bg-surface border rounded-xl shadow-lg overflow-hidden">
                {suggestions.map((s) => (
                  <button
                    key={s.id}
                    onClick={() => handleSelect(s.symbol)}
                    className="w-full text-right px-4 py-2 hover:bg-neutral/50 transition-colors flex justify-between items-center"
                  >
                    <span className="font-bold">{s.symbol}</span>
                    <span className="text-xs text-muted-foreground">{s.name}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
          
          {loading && <div className="mt-4"><PageLoading /></div>}
          
          {scoringData && !loading && (
            <div className="mt-6 p-4 rounded-xl bg-secondary/10 border border-secondary/20">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-xl font-bold">{selectedSymbol}</h3>
                <div className="text-right">
                  <div className="text-sm text-muted-foreground">{t("app.scoring.overall_score", currentLang)}</div>
                  <div className="text-3xl font-black text-secondary">
                    {scoringData.overall_score?.toLocaleString(currentLang === "fa" ? "fa-IR" : "en-US")}
                  </div>
                </div>
              </div>
              
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {Object.entries(scoringData.dimensions || {}).map(([dim, score]: [string, any]) => (
                  <div key={dim} className="p-3 rounded-lg bg-surface border">
                    <div className="text-xs text-muted-foreground capitalize">{t(`app.scoring.dimensions.${dim.toLowerCase()}`, currentLang)}</div>
                    <div className="text-lg font-bold">{score?.toLocaleString(currentLang === "fa" ? "fa-IR" : "en-US")}</div>
                  </div>
                ))}
              </div>
              
              <div className="mt-4 text-center">
                <div className="inline-block px-4 py-1 rounded-full bg-surface border text-sm font-bold">
                  {t("app.scoring.grade", currentLang)} <span className="text-secondary">{scoringData.grade}</span>
                </div>
              </div>
            </div>
          )}
        </TarotCard>
        <TarotCard icon="💯" title={t("app.scoring.system_title", currentLang)}>
          <div className="space-y-6 padding">
            <p className="text-justify text-muted-foreground">
              {t("app.scoring.system_desc", currentLang)}
            </p>

            <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
              {mlCoefficients.map((w, i) => (
                <div key={i} className="border p-2 rounded bg-muted/30">
                  <div className="flex items-center gap-2">
                    <span className="text-sm">{w.label}</span>
                    <div className="flex items-center">
                      <span className="font-bold text-secondary">{w.defaultWeight}%</span>
                      {w.mlOptimized && <span className="text-xs text-muted-foreground" title="Optimized by ML"></span>}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </TarotCard>

        <TarotCard icon="🧊" title={t("app.scoring.dimensions_title", currentLang)}>
          {dimensionDetails.map((dim, i) => (
            <div key={dim.id} className="mb-2">
              <div 
                className="flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition hover:shadow-md"
                onClick={() => setExpandedDim(expandedDim === dim.id ? null : dim.id)}
              >
                <span className="text-2xl">{dim.icon}</span>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <h4 className="font-semibold">{dim.title}</h4>
                    <span className={`px-2 py-1 rounded text-xs font-bold ${dim.color}`}>{t("app.scoring.weight", currentLang)} {dim.weight}%</span>
                  </div>
                </div>
                <span className="text-xl">{expandedDim === dim.id ? "▼" : "▶"}</span>
              </div>

              {expandedDim === dim.id && (
                <div className="mt-2 ml-8 border-l-2 border-border/50 pl-4 animate-in slide-in-from-top-2 duration-200">
                  {dim.aspects.map((a, j) => (
                    <div key={j} className="mb-3 last:mb-0">
                      <div className="font-medium text-sm text-foreground">{a.name}</div>
                      <div className="text-xs text-muted-foreground">{a.desc}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </TarotCard>

        <TarotCard icon="📊" title={t("app.scoring.grading_scale", currentLang)}>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
            {grades.map((g, i) => (
              <div key={i} className={`text-center p-3 rounded ${g.bg} border ${g.color}`}>
                <div className={`font-bold text-lg ${g.color}`}>{g.label}</div>
                <div className="mt-1 text-sm text-muted-foreground">
                  {i === 0 ? "≥ 85" : `${currentLang === "fa" ? "از" : "From"} ${g.min} ${currentLang === "fa" ? "تا" : "to"} ${grades[i-1]?.min ? grades[i-1].min - 1 : "--"}`}
                </div>
              </div>
            ))}
          </div>
        </TarotCard>

        <TarotCard icon="🤖" title={t("app.scoring.ml_optimization", currentLang)}>
          <div className="space-y-4">
            <p className="text-sm text-muted-foreground">
              {t("app.scoring.ml_desc", currentLang)}
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {dimensionDetails.map((dim, i) => (
                <div key={i} className="border p-2 rounded bg-muted/30">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">{dim.title}</span>
                    <span className="text-sm text-right mr-2">{t("app.scoring.weight", currentLang)} {dim.weight}%</span>
                  </div>
                  <p className="text-xs text-muted-foreground">{currentLang === "fa" ? "به‌طور هفتگی بر اساس عملکرد تاریخی بهینه می‌شود." : "Optimized weekly based on historical performance data."}</p>
                </div>
              ))}
            </div>
          </div>
        </TarotCard>

        <TarotCard icon="🧬" title={t("app.scoring.hierarchy_title", currentLang)}>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-3 bg-secondary/10 rounded text-center">
              <div className="text-2xl font-bold">6</div>
              <div className="text-xs">{t("app.scoring.hierarchy.dimensions", currentLang)}</div>
            </div>

            <div className="p-3 bg-secondary/10 rounded text-center">
              <div className="text-2xl font-bold">40</div>
              <div className="text-xs">{t("app.scoring.hierarchy.sub_dimensions", currentLang)}</div>
            </div>

            <div className="p-3 bg-secondary/10 rounded text-center">
              <div className="text-2xl font-bold">80</div>
              <div className="text-xs">{t("app.scoring.hierarchy.aspects", currentLang)}</div>
            </div>

            <div className="p-3 bg-secondary/10 rounded text-center">
              <div className="text-2xl font-bold">173</div>
              <div className="text-xs">{t("app.scoring.hierarchy.sub_aspects", currentLang)}</div>
            </div>
          </div>
        </TarotCard>

        <div className="flex flex-col md:flex-row gap-3">
          <Link href="/analysis">
            <PrimaryButton className="w-full cursor-pointer">{t("app.scoring.actions.view_analysis", currentLang)}</PrimaryButton>
          </Link>
          <Link href="/stocks">
            <PrimaryButton className="w-full cursor-pointer">{t("app.scoring.actions.browse_stocks", currentLang)}</PrimaryButton>
          </Link>
        </div>
      </div>
    </DashboardShell>
  );
}
