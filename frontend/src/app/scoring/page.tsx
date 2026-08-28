"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { cn } from "@/lib/cn";
import { t } from "@/lib/i18n";
import { useAuthStore } from "@/store/useAuthStore";
import { fetchSymbols, fetchScoring } from "@/lib/api/stocks";

// Types
interface ScoredStock {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  score: number;
  recommendation: "Strong Buy" | "Buy" | "Hold" | "Sell" | "Strong Sell";
  sector: string;
  metrics: {
    value: number;
    growth: number;
    profitability: number;
    momentum: number;
    quality: number;
  };
  aiAnalysis: string;
}

// Mock Data
const mockScoredStocks: ScoredStock[] = [
  {
    symbol: "NVDA",
    name: "NVIDIA Corporation",
    price: 138.25,
    change: 4.87,
    changePercent: 3.65,
    score: 96,
    recommendation: "Strong Buy",
    sector: "Technology",
    metrics: { value: 85, growth: 98, profitability: 95, momentum: 94, quality: 92 },
    aiAnalysis: "Exceptional AI chip demand with dominant market position. Strong financials and growth trajectory."
  },
  {
    symbol: "MSFT",
    name: "Microsoft Corporation",
    price: 432.05,
    change: 5.12,
    changePercent: 1.20,
    score: 94,
    recommendation: "Strong Buy",
    sector: "Technology",
    metrics: { value: 88, growth: 92, profitability: 96, momentum: 90, quality: 94 },
    aiAnalysis: "Cloud computing leader with consistent innovation. Excellent balance sheet and dividend history."
  },
  {
    symbol: "AAPL",
    name: "Apple Inc.",
    price: 233.67,
    change: 3.45,
    changePercent: 1.50,
    score: 92,
    recommendation: "Buy",
    sector: "Technology",
    metrics: { value: 85, growth: 78, profitability: 98, momentum: 88, quality: 93 },
    aiAnalysis: "Strong brand loyalty and cash generation. Growth concerns balanced by innovation pipeline."
  },
  {
    symbol: "GOOGL",
    name: "Alphabet Inc.",
    price: 178.35,
    change: 1.25,
    changePercent: 0.71,
    score: 90,
    recommendation: "Buy",
    sector: "Communication Services",
    metrics: { value: 90, growth: 85, profitability: 88, momentum: 82, quality: 89 },
    aiAnalysis: "Search dominance and AI capabilities. Regulatory concerns remain a risk factor."
  },
  {
    symbol: "AMZN",
    name: "Amazon.com Inc.",
    price: 197.83,
    change: 2.14,
    changePercent: 1.09,
    score: 88,
    recommendation: "Buy",
    sector: "Consumer Cyclical",
    metrics: { value: 82, growth: 88, profitability: 75, momentum: 86, quality: 85 },
    aiAnalysis: "AWS growth and e-commerce dominance. Margin expansion continues to improve."
  },
  {
    symbol: "META",
    name: "Meta Platforms Inc.",
    price: 612.77,
    change: 12.45,
    changePercent: 2.07,
    score: 86,
    recommendation: "Buy",
    sector: "Communication Services",
    metrics: { value: 78, growth: 92, profitability: 85, momentum: 90, quality: 80 },
    aiAnalysis: "Metaverse investments showing early returns. Strong social media engagement."
  },
  {
    symbol: "AMD",
    name: "Advanced Micro Devices",
    price: 142.88,
    change: 3.42,
    changePercent: 2.45,
    score: 82,
    recommendation: "Buy",
    sector: "Technology",
    metrics: { value: 80, growth: 88, profitability: 78, momentum: 85, quality: 78 },
    aiAnalysis: "Strong CPU/GPU market position. Data center growth accelerating."
  },
  {
    symbol: "TSLA",
    name: "Tesla Inc.",
    price: 248.50,
    change: -5.25,
    changePercent: -2.07,
    score: 75,
    recommendation: "Hold",
    sector: "Consumer Cyclical",
    metrics: { value: 65, growth: 82, profitability: 72, momentum: 68, quality: 70 },
    aiAnalysis: "EV market leader facing increased competition. Regulatory and execution risks."
  },
  {
    symbol: "INTC",
    name: "Intel Corporation",
    price: 21.24,
    change: -0.42,
    changePercent: -1.85,
    score: 58,
    recommendation: "Hold",
    sector: "Technology",
    metrics: { value: 70, growth: 45, profitability: 55, momentum: 42, quality: 60 },
    aiAnalysis: "Turnaround story with significant execution challenges. Dividend at risk."
  },
];

// Components
function getRecommendationColor(rec: string) {
  switch (rec) {
    case "Strong Buy": return "bg-[var(--color-success)]";
    case "Buy": return "bg-[var(--color-primary)]";
    case "Hold": return "bg-[var(--color-warning)]";
    case "Sell": return "bg-orange-500";
    case "Strong Sell": return "bg-[var(--color-error)]";
    default: return "bg-[var(--color-border)]";
  }
}

const mlCoefficients = [
  { label: "Fundamental", defaultWeight: 25, mlOptimized: true },
  { label: "Technical", defaultWeight: 20, mlOptimized: true },
  { label: "Sentiment", defaultWeight: 15, mlOptimized: true },
  { label: "Risk", defaultWeight: 20, mlOptimized: true },
  { label: "Macro", defaultWeight: 10, mlOptimized: true },
  { label: "AI", defaultWeight: 10, mlOptimized: true }
];

export default function ScoringPage() {
  const { currentLang } = useAuthStore();
  const [expandedDim, setExpandedDim] = useState<string | null>(null);
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

  const [stocks, setStocks] = useState<ScoredStock[]>(mockScoredStocks);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterRec, setFilterRec] = useState<string>("all");
  const [sortBy, setSortBy] = useState<"score" | "symbol" | "change">("score");

  useEffect(() => {
    const timer = setTimeout(() => setLoading(false), 1000);
    return () => clearTimeout(timer);
  }, []);

  const filteredStocks = useMemo(() => {
    let filtered = stocks;

    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (s) =>
          s.symbol.toLowerCase().includes(query) ||
          s.name.toLowerCase().includes(query) ||
          s.sector.toLowerCase().includes(query)
      );
    }

    if (filterRec !== "all") {
      filtered = filtered.filter((s) => s.recommendation === filterRec);
    }

    return [...filtered].sort((a, b) => {
      switch (sortBy) {
        case "score":
          return b.score - a.score;
        case "symbol":
          return a.symbol.localeCompare(b.symbol);
        case "change":
          return b.changePercent - a.changePercent;
        default:
          return 0;
      }
    });
  }, [stocks, searchQuery, filterRec, sortBy]);

  const recommendations = ["Strong Buy", "Buy", "Hold", "Sell", "Strong Sell"];
  const avgScore = Math.round(stocks.reduce((acc, s) => acc + s.score, 0) / stocks.length);

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="h-12 w-12 animate-spin rounded-full border-4 border-[var(--color-border)] border-t-[#00d4ff]" />
          <p className="text-[var(--color-text-secondary)]">Loading AI scoring data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold text-[var(--color-text-primary)]">
            <span className="text-[var(--color-primary)]">[AI]</span>
            AI Stock Scoring
          </h1>
          <p className="text-[var(--color-text-secondary)]">NASDAQ stocks ranked by our AI analysis engine</p>
        </div>
        <div className="flex items-center gap-4 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)]/50 px-4 py-3">
          <div className="text-center">
            <p className="text-xs text-[var(--color-text-secondary)]">Avg Score</p>
            <p className="text-xl font-bold text-[var(--color-text-primary)]">{avgScore}</p>
          </div>
          <div className="h-8 w-px bg-[var(--color-border)]" />
          <div className="text-center">
            <p className="text-xs text-[var(--color-text-secondary)]">Strong Buy</p>
            <p className="text-xl font-bold text-[var(--color-success)]">{stocks.filter((s) => s.recommendation === "Strong Buy").length}</p>
          </div>
          <div className="h-8 w-px bg-[var(--color-border)]" />
          <div className="text-center">
            <p className="text-xs text-[var(--color-text-secondary)]">Scored</p>
            <p className="text-xl font-bold text-[var(--color-text-primary)]">{stocks.length}</p>
          </div>
        </div>
      </div>

      {/* How It Works */}
      <div className="glass-card overflow-hidden rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5 shadow-sm">
        <div className="flex items-center gap-3 mb-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[var(--color-primary)]/10">
            <span className="text-[var(--color-primary)] text-lg">[Target]</span>
          </div>
          <div>
            <h3 className="font-semibold text-[var(--color-text-primary)]">How Our AI Scoring Works</h3>
            <p className="text-xs text-[var(--color-text-secondary)]">Analyzing 50+ metrics across 5 dimensions</p>
          </div>
        </div>
        
        <div className="grid gap-4 sm:grid-cols-5">
          {[
            { label: "Value", desc: "P/E, P/B, EV/EBITDA" },
            { label: "Growth", desc: "Revenue & EPS growth" },
            { label: "Profitability", desc: "ROE, margins, FCF" },
            { label: "Momentum", desc: "Price trends, RSI" },
            { label: "Quality", desc: "Balance sheet, stability" },
          ].map((metric) => (
            <div key={metric.label} className="rounded-lg bg-[var(--color-background)]/50 p-3">
              <div className="flex items-center gap-2">
                <span className="text-[var(--color-primary)]">*</span>
                <span className="text-sm font-medium text-[var(--color-text-primary)]">{metric.label}</span>
              </div>
              <p className="mt-1 text-xs text-[var(--color-text-secondary)]">{metric.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col gap-4 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)]/50 p-4 lg:flex-row lg:items-center">
        <div className="relative flex-1">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-text-secondary)]">Search</span>
          <input
            type="text"
            placeholder="Search stocks..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="h-10 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] pl-10 pr-4 text-sm text-[var(--color-text-primary)] placeholder-[#64748b] focus:border-[var(--color-primary)] focus:outline-none"
          />
        </div>

        <div className="flex items-center gap-2">
          <span className="text-[var(--color-text-secondary)]">Filter</span>
          <select
            value={filterRec}
            onChange={(e) => setFilterRec(e.target.value)}
            className="h-10 rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] px-3 text-sm text-[var(--color-text-primary)] focus:border-[var(--color-primary)] focus:outline-none"
          >
            <option value="all">All Recommendations</option>
            {recommendations.map((rec) => (
              <option key={rec} value={rec}>{rec}</option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-[var(--color-text-secondary)]">Settings</span>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="h-10 rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] px-3 text-sm text-[var(--color-text-primary)] focus:border-[var(--color-primary)] focus:outline-none"
          >
            <option value="score">Score (High to Low)</option>
            <option value="symbol">Symbol</option>
            <option value="change">Change %</option>
          </select>
        </div>
      </div>

      {/* Results */}
      <div className="space-y-4">
        {filteredStocks.length > 0 ? (
          filteredStocks.map((stock, index) => (
            <ScoredStockCard key={stock.symbol} stock={stock} index={index} />
          ))
        ) : (
          <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-[var(--color-border)] bg-[var(--color-surface)]/30 py-16">
            <span className="text-4xl text-[#334155]">Search</span>
            <h3 className="mt-4 text-lg font-medium text-[var(--color-text-primary)]">No stocks found</h3>
            <p className="mt-1 text-sm text-[var(--color-text-secondary)]">Try adjusting your filters</p>
          </div>
        )}
      </div>
    </div>
  );
}

function ScoreRing({ score }: { score: number }) {
  const getColor = (s: number) => {
    if (s >= 90) return "#10b981";
    if (s >= 75) return "#00d4ff";
    if (s >= 60) return "#f59e0b";
    return "#ef4444";
  };

  return (
    <div className="relative h-16 w-16">
      <svg className="h-full w-full -rotate-90" viewBox="0 0 36 36">
        <path
          d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
          fill="none"
          stroke="#1e293b"
          strokeWidth="3"
        />
        <path
          d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
          fill="none"
          stroke={getColor(score)}
          strokeWidth="3"
          strokeDasharray={`${score}, 100`}
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-lg font-bold text-[var(--color-text-primary)]">{score}</span>
      </div>
    </div>
  );
}

function MetricBar({ label, value }: { label: string; value: number }) {
  const getColor = (v: number) => {
    if (v >= 90) return "bg-[var(--color-success)]";
    if (v >= 75) return "bg-[var(--color-primary)]";
    if (v >= 60) return "bg-[var(--color-warning)]";
    return "bg-[var(--color-error)]";
  };

  return (
    <div>
      <div className="flex items-center justify-between text-xs">
        <span className="text-[var(--color-text-secondary)]">{label}</span>
        <span className="font-medium text-[var(--color-text-primary)]">{value}</span>
      </div>
      <div className="mt-1 h-1.5 w-full rounded-full bg-[var(--color-border)]">
        <div className={cn("h-full rounded-full transition-all", getColor(value))} style={{ width: `${value}%` }} />
      </div>
    </div>
  );
}

function ScoredStockCard({ stock, index }: { stock: ScoredStock; index: number }) {
  const isPositive = stock.change >= 0;

  return (
    <div className="glass-card group overflow-hidden rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5 transition-all duration-300 hover:border-[var(--color-primary)]/30 hover:shadow-md">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center">
        {/* Rank & Logo */}
        <div className="flex items-center gap-3">
          <div className={cn(
            "flex h-10 w-10 items-center justify-center rounded-lg text-sm font-bold",
            index === 0 ? "bg-[var(--color-warning)] text-white" :
            index === 1 ? "bg-gray-400 text-white" :
            index === 2 ? "bg-amber-700 text-white" :
            "bg-[var(--color-border)] text-[var(--color-text-secondary)]"
          )}>
            {index + 1}
          </div>
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-[#00d4ff]/20 to-[#0ea5e9]/20 text-lg font-bold text-[var(--color-primary)]">
            {stock.symbol.slice(0, 2)}
          </div>
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-semibold text-[var(--color-text-primary)]">{stock.symbol}</h3>
            <span className={`rounded-full bg-gradient-to-r px-2 py-0.5 text-xs font-semibold text-[var(--color-text-primary)] bg-gradient-to-r ${getRecommendationColor(stock.recommendation)}`}>
              {stock.recommendation}
            </span>
          </div>
          <p className="truncate text-sm text-[var(--color-text-secondary)]">{stock.name}</p>
          <p className="mt-1 text-xs text-[var(--color-text-secondary)]">{stock.sector}</p>
        </div>

        {/* Price */}
        <div className="text-right">
          <p className="text-xl font-bold text-[var(--color-text-primary)]">${stock.price.toFixed(2)}</p>
          <div className={cn(
            "flex items-center justify-end gap-1 text-sm font-medium",
            isPositive ? "text-[var(--color-success)]" : "text-[var(--color-error)]"
          )}>
            <span>{isPositive ? "Up" : "Down"}</span>
            <span>{isPositive ? "+" : ""}{stock.changePercent.toFixed(2)}%</span>
          </div>
        </div>

        {/* Score */}
        <div className="flex items-center gap-4">
          <ScoreRing score={stock.score} />
          <div className="hidden lg:block">
            <p className="text-xs text-[var(--color-text-secondary)]">AI Score</p>
            <p className="text-lg font-bold text-[var(--color-text-primary)]">{stock.score}/100</p>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          <Link
            href={`/stocks/${stock.symbol}`}
            className="flex items-center gap-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] px-3 py-2 text-sm font-medium text-[var(--color-text-primary)] transition-all hover:border-[var(--color-primary)]/50"
          >
            View
            <span>&gt;</span>
          </Link>
        </div>
      </div>

      {/* Metrics & Analysis */}
      <div className="mt-4 grid gap-4 border-t border-[var(--color-border)] pt-4 lg:grid-cols-3">
        <div className="space-y-3">
          <h4 className="text-xs font-medium uppercase tracking-wider text-[var(--color-text-secondary)]">Metric Breakdown</h4>
          <MetricBar label="Value" value={stock.metrics.value} />
          <MetricBar label="Growth" value={stock.metrics.growth} />
          <MetricBar label="Profitability" value={stock.metrics.profitability} />
          <MetricBar label="Momentum" value={stock.metrics.momentum} />
          <MetricBar label="Quality" value={stock.metrics.quality} />
        </div>
        
        <div className="lg:col-span-2">
          <h4 className="mb-2 text-xs font-medium uppercase tracking-wider text-[var(--color-text-secondary)]">AI Analysis</h4>
          <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-background)]/50 p-4">
            <div className="flex items-start gap-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-[#00d4ff]/20 to-[#0ea5e9]/20">
                <span className="text-[var(--color-primary)]">[AI]</span>
              </div>
              <p className="text-sm leading-relaxed text-[var(--color-text-secondary)]">{stock.aiAnalysis}</p>
            </div>
          </div>
          
          <div className="mt-4 flex flex-wrap gap-2">
            {["Technical Analysis", "Fundamental Data", "Market Sentiment", "Earnings Quality", "Risk Assessment"].map((tag) => (
              <span key={tag} className="rounded-full bg-[var(--color-border)] px-2.5 py-1 text-xs text-[var(--color-text-secondary)]">
                {tag}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
