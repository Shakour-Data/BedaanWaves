import Link from "next/link";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import {
  TrendUpIcon,
  ChartBarIcon,
  CpuIcon,
  BriefcaseIcon,
  BellIcon,
  NewspaperIcon,
  SearchIcon,
  GlobeIcon,
  TargetIcon,
} from "@/components/icons/Icons";

const features = [
  {
    title: "Real-Time Market Data",
    desc: "Live and historical OHLCV data for NASDAQ, NYSE, TSE/OTC, and crypto markets with multiple timeframes.",
    Icon: TrendUpIcon,
  },
  {
    title: "Fundamental Analysis",
    desc: "Quarterly financials, ratios (P/E, P/B, EPS, ROE), and key metrics for stocks across all supported markets.",
    Icon: ChartBarIcon,
  },
  {
    title: "AI-Powered Signals",
    desc: "Machine-learning predictions, technical indicators, and anomaly detection to support informed decisions.",
    Icon: CpuIcon,
  },
  {
    title: "Portfolio Tracking",
    desc: "Track positions, unrealized P&L, allocation, and performance across personal and watchlist portfolios.",
    Icon: BriefcaseIcon,
  },
  {
    title: "Smart Alerts",
    desc: "Configure price, signal, and news alerts with multi-channel notifications (email, SMS, push, webhook).",
    Icon: BellIcon,
  },
  {
    title: "News & Sentiment",
    desc: "Aggregated market news with multilingual NLP summaries and sentiment scoring for assets.",
    Icon: NewspaperIcon,
  },
  {
    title: "Advanced Screening",
    desc: "Filter universes by fundamental, technical, and custom criteria across sectors and markets.",
    Icon: SearchIcon,
  },
  {
    title: "Crypto & International",
    desc: "Seamless coverage of Binance, Kraken, Coinbase, and major international exchanges alongside Tehran markets.",
    Icon: GlobeIcon,
  },
  {
    title: "Scoring & Methodology",
    desc: "Hierarchical multi-dimensional scoring with transparent methodology and coefficient learning pipeline.",
    Icon: TargetIcon,
  },
];

export default function HomePage() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-[#F8FAFC] to-white">
      <section className="px-4 pt-20 pb-16">
        <div className="mx-auto max-w-4xl text-center">
          <h1 className="text-4xl font-bold text-[#0F172A] md:text-5xl">
            BedaanWaves
          </h1>
          <p className="mt-4 text-lg text-[#475569] md:text-xl">
            Professional market analysis platform with real-time data, AI signals,
            fundamentals, and portfolio intelligence.
          </p>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
            <Link href="/login">
              <PrimaryButton size="lg">Sign In</PrimaryButton>
            </Link>
            <Link href="/register">
              <PrimaryButton variant="outline" size="lg">
                Create Account
              </PrimaryButton>
            </Link>
          </div>
        </div>
      </section>

      <section className="px-4 pb-20">
        <div className="mx-auto max-w-6xl">
          <h2 className="mb-10 text-center text-2xl font-semibold text-[#0F172A]">
            Everything you need to analyze markets
          </h2>
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
            {features.map((item) => (
              <div
                key={item.title}
                className="rounded-2xl border border-[#E2E8F0] bg-white p-6 shadow-sm transition-shadow hover:shadow-md"
              >
                <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <item.Icon className="h-5 w-5" />
                </div>
                <h3 className="text-lg font-semibold text-[#0F172A]">
                  {item.title}
                </h3>
                <p className="mt-2 text-sm text-[#475569]">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="px-4 pb-20">
        <div className="mx-auto max-w-4xl rounded-2xl bg-[#0F172A] px-8 py-12 text-center text-white md:px-12">
          <h2 className="text-2xl font-semibold md:text-3xl">
            Ready to start analyzing?
          </h2>
          <p className="mt-3 text-[#94A3B8]">
            Sign in or create an account to access dashboards, signals, and portfolio tools.
          </p>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
            <Link href="/login">
              <PrimaryButton size="lg">Sign In</PrimaryButton>
            </Link>
            <Link href="/register">
              <PrimaryButton variant="outline" size="lg">
                Create Account
              </PrimaryButton>
            </Link>
          </div>
        </div>
      </section>
    </main>
  );
}
