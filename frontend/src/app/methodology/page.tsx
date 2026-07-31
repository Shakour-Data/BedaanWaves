"use client";

import { DashboardShell } from "@/components/layout/DashboardShell";
import { TarotCard } from "@/components/ui/TarotCard";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import Link from "next/link";
import { useState } from "react";

const analysisMethods = [
  {
    id: "scoring",
    title: "6D Scoring System",
    icon: "🧮",
    description: "Comprehensive multi-dimensional stock evaluation",
    steps: [
      "Collect data across six dimensions (fundamental, technical, sentiment, risk, macro, AI)",
      "Calculate individual scores (0-100) for each dimension",
      "Apply ML-optimized weights to dimension scores",
      "Compute final weighted score and assign grade (A-E)"
    ],
    details: "Uses a 4-level hierarchy with 305 nodes to evaluate investments across six equally-weighted dimensions. Machine learning dynamically optimizes weights based on historical performance.",
    apiEndpoints: [
      "/analysis/scoring",
      "/analysis/scoring/rank"
    ]
  },
  {
    id: "ranking",
    title: "Ranking System",
    icon: "📊",
    description: "Stock ranking by performance metrics",
    steps: [
      "Calculate 6D scores for all eligible securities",
      "Sort by selected metric (overall score or specific dimension)",
      "Return top N results (default: 10)"
    ],
    details: "Users can rank by any of the six dimensions or the composite score. Results are cached for 5 minutes to reduce API load.",
    apiEndpoints: [
      "/analysis/scoring/rank"
    ]
  },
  {
    id: "technical",
    title: "Technical Analysis",
    icon: "📈",
    description: "Price and volume-based indicators",
    steps: [
      "Fetch historical price/volume data (minimum 20 periods)",
      "Calculate indicators (RSI, MACD, moving averages, Bollinger Bands)",
      "Generate trading signals based on indicator crossovers and thresholds"
    ],
    details: "Provides 50+ technical indicators including momentum oscillators, trend-following tools, and volatility measures.",
    apiEndpoints: [
      "/analysis/technical/{symbol}"
    ]
  },
  {
    id: "fundamental",
    title: "Fundamental Analysis",
    icon: "💰",
    description: "Financial statement analysis",
    steps: [
      "Retrieve latest financial statements from CODAL, Yahoo Finance, or Alpha Vantage",
      "Calculate key ratios (P/E, P/B, ROE, Debt/Equity, etc.)",
      "Assess earnings quality and growth sustainability"
    ],
    details: "Analyzes income statements, balance sheets, and cash flow statements from multiple global data sources.",
    apiEndpoints: [
      "/analysis/fundamental/{symbol}"
    ]
  },
  {
    id: "momentum",
    title: "Momentum Analysis",
    icon: "🚀",
    description: "Short-term price trend identification",
    steps: [
      "Calculate price changes over multiple timeframes (1D, 1W, 1M, 3M)",
      "Identify assets with strongest relative momentum",
      "Filter for stocks showing consistent upward trends"
    ],
    details: "Focuses on relative strength and trend persistence to identify potential outperformers.",
    apiEndpoints: [
      "/analysis/momentum/{symbol}"
    ]
  },
  {
    id: "risk",
    title: "Risk Analysis",
    icon: "⚠️",
    description: "Volatility and downside risk assessment",
    steps: [
      "Calculate daily returns from historical price data",
      "Compute volatility (standard deviation of returns)",
      "Calculate Value-at-Risk (VaR) and Conditional VaR",
      "Determine Sharpe, Sortino, and Calmar ratios"
    ],
    details: "Provides comprehensive risk metrics including maximum drawdown, beta, and tail risk measures.",
    apiEndpoints: [
      "/analysis/risk/{symbol}",
      "/analysis/volatility/{symbol}"
    ]
  },
  {
    id: "sentiment",
    title: "Sentiment Analysis",
    icon: "🗣️",
    description: "Market sentiment from news and social media",
    steps: [
      "Collect financial news and social media mentions",
      "Apply NLP models to extract sentiment scores",
      "Aggregate sentiment by source and time period"
    ],
    details: "Uses transformer-based NLP models to analyze text sentiment from multiple sources in real-time.",
    apiEndpoints: [
      "/analysis/sentiment/{symbol}"
    ]
  },
  {
    id: "ai",
    title: "AI/ML Analysis",
    icon: "🧠",
    description: "Machine learning-based predictions",
    steps: [
      "Train LSTM/Prophet models on historical price data",
      "Generate price forecasts for multiple time horizons",
      "Detect chart patterns and anomalies using computer vision"
    ],
    details: "Combines time series forecasting, pattern recognition, and anomaly detection for predictive insights.",
    apiEndpoints: [
      "/analysis/prediction/{symbol}"
    ]
  }
];

export default function MethodologyPage() {
  const [activeMethod, setActiveMethod] = useState("scoring");

  return (
    <DashboardShell title="Analysis Methodology">
      <div className="flex flex-col gap-6">
        {/* Header */}
        <TarotCard icon="🔬" title="Methodology Overview">
          <p className="text-muted-foreground text-justify">
            BedaanWaves employs a multi-faceted approach to financial analysis, combining traditional fundamental/technical analysis with cutting-edge machine learning techniques. Each analysis type serves a specific purpose in the investment decision-making process.
          </p>
        </TarotCard>

        {/* Method Tabs */}
        <div className="flex gap-2 flex-wrap">
          {analysisMethods.map((method) => (
            <button
              key={method.id}
              onClick={() => setActiveMethod(method.id)}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-colors whitespace-nowrap ${
                activeMethod === method.id
                  ? "bg-secondary text-secondary-foreground"
                  : "bg-muted text-muted-foreground hover:bg-muted/80"
              }`}
            >
              <span className="mr-2">{method.icon}</span>
              {method.title}
            </button>
          ))}
        </div>

        {/* Active Method Content */}
        {analysisMethods.map((method) => (
          activeMethod === method.id && (
            <TarotCard key={method.id} icon={method.icon} title={method.title}>
              <div className="space-y-4">
                <p className="text-muted-foreground">{method.description}</p>

                {/* Steps */}
                <div>
                  <h4 className="font-medium mb-2">Process Steps:</h4>
                  <ol className="list-decimal list-inside space-y-2 text-sm text-muted-foreground">
                    {method.steps.map((step, i) => (
                      <li key={i}>{step}</li>
                    ))}
                  </ol>
                </div>

                {/* Details */}
                <div>
                  <h4 className="font-medium mb-2">Technical Details:</h4>
                  <p className="text-sm text-muted-foreground">{method.details}</p>
                </div>

                {/* API Endpoints */}
                {method.apiEndpoints && (
                  <div>
                    <h4 className="font-medium mb-2">API Endpoints:</h4>
                    <ul className="list-disc list-inset space-y-1 text-sm font-mono">
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
          <TarotCard icon="📚" title="Key Capabilities">
            <ul className="space-y-2 text-sm">
              <li className="flex items-center gap-2">
                <span className="text-green-500">✓</span>
                <span>Coverage: Iran, Global, and Crypto Markets</span>
              </li>
              <li className="flex items-center gap-2">
                <span className="text-green-500">✓</span>
                <span>Real-time data updates (24/7)</span>
              </li>
              <li className="flex items-center gap-2">
                <span className="text-green-500">✓</span>
                <span>ML-optimized weighting system</span>
              </li>
              <li className="flex items-center gap-2">
                <span className="text-green-500">✓</span>
                <span>Customizable user preferences</span>
              </li>
            </ul>
          </TarotCard>

          {/* Disclaimers */}
          <TarotCard icon="⚡" title="Important Notes">
            <div className="space-y-3 text-sm">
              <div>
                <h5 className="font-medium mb-1">Disclaimer:</h5>
                <p className="text-muted-foreground">This is an analytical tool, not financial advice.</p>
              </div>
              <div>
                <h5 className="font-medium mb-1">Accuracy:</h5>
                <p className="text-muted-foreground">Results based on historical data, not guaranteed future performance.</p>
              </div>
            </div>
          </TarotCard>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col md:flex-row gap-3">
          <Link href="/scoring">
            <PrimaryButton className="w-full cursor-pointer">Explore 6D Scoring</PrimaryButton>
          </Link>
          <Link href="/analysis">
            <PrimaryButton className="w-full cursor-pointer">Run Analysis</PrimaryButton>
          </Link>
        </div>
      </div>
    </DashboardShell>
  );
}