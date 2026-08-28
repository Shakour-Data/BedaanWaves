import { Metadata } from "next";
import Link from "next/link";
import { PublicLayout } from "@/components/layout/PublicLayout";
import { PageTransition } from "@/components/layout/PageTransition";

export const metadata: Metadata = {
  title: "BedaanWaves | Professional Market Analysis Platform",
  description:
    "Comprehensive market analysis platform with real-time data, technical analysis, fundamentals, and AI signals.",
  keywords: "market analysis, trading, AI scoring, technical analysis, stocks, NASDAQ",
};

const features = [
  {
    title: "Real-time Data",
    description: "Live market data with millisecond latency updates across global exchanges.",
    icon: "📊",
  },
  {
    title: "AI Scoring",
    description: "Advanced machine learning models for stock ranking and signal generation.",
    icon: "🤖",
  },
  {
    title: "Risk Analysis",
    description: "Comprehensive portfolio risk assessment and management tools.",
    icon: "🛡️",
  },
  {
    title: "Fast Execution",
    description: "Lightning-fast analysis and signal generation for time-sensitive decisions.",
    icon: "⚡",
  },
];

const stats = [
  { value: "5,000+", label: "Stocks Tracked" },
  { value: "99.9%", label: "Uptime" },
  { value: "<50ms", label: "Latency" },
  { value: "24/7", label: "Monitoring" },
];

export default function HomePage() {
  return (
    <PublicLayout>
      <PageTransition>
        {/* Hero Section */}
        <section className="relative overflow-hidden pt-16 pb-20 lg:pt-24 lg:pb-32">
          <div className="absolute inset-0 overflow-hidden">
            <div className="absolute -top-1/2 -right-1/4 h-[800px] w-[800px] rounded-full bg-[var(--color-primary)]/5 blur-3xl" />
            <div className="absolute -bottom-1/2 -left-1/4 h-[600px] w-[600px] rounded-full bg-[var(--color-primary)]/5 blur-3xl" />
          </div>

          <div className="relative container-grid">
            <div className="text-center">
              <div className="mb-8 inline-flex items-center gap-2 rounded-full border border-[var(--color-primary)]/30 bg-[var(--color-primary)]/10 px-4 py-1.5">
                <span className="flex h-2 w-2 animate-pulse rounded-full bg-[var(--color-primary)]" />
                <span className="text-sm font-medium text-[var(--color-primary)]">Live Market Data</span>
              </div>

              <h1 className="mb-6 text-4xl font-bold leading-tight tracking-tight text-[var(--color-text-primary)] sm:text-5xl lg:text-6xl">
                Master the
                <span className="text-[var(--color-primary)]"> Markets </span>
                with AI
              </h1>

              <p className="mx-auto mb-10 max-w-2xl text-lg text-[var(--color-text-secondary)]">
                Professional-grade market analysis platform with AI-powered scoring,
                real-time data, and advanced technical analysis for informed trading decisions.
              </p>

              <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
                <Link
                  href="/register"
                  className="group flex items-center gap-2 rounded-md bg-[var(--color-primary)] px-8 py-4 text-base font-semibold text-white transition-all hover:bg-[var(--color-primary-hover)]"
                >
                  Start Free Trial
                  <span className="text-xl transition-transform group-hover:translate-x-1">→</span>
                </Link>
                <Link
                  href="/services"
                  className="flex items-center gap-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-8 py-4 text-base font-semibold text-[var(--color-text-primary)] transition-all hover:border-[var(--color-primary)] hover:bg-[var(--color-border)]"
                >
                  Explore Features
                </Link>
              </div>
            </div>
          </div>
        </section>

        {/* Stats Section */}
        <section className="border-y border-[var(--color-border)] bg-[var(--color-surface)]/50 py-12">
          <div className="container-grid">
            <div className="grid grid-cols-2 gap-8 md:grid-cols-4">
              {stats.map((stat, index) => (
                <div key={index} className="text-center">
                  <div className="text-3xl font-bold text-[var(--color-text-primary)]">{stat.value}</div>
                  <div className="mt-1 text-sm text-[var(--color-text-secondary)]">{stat.label}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section id="features" className="py-24">
          <div className="container-grid">
            <div className="text-center mb-16">
              <h2 className="text-3xl font-bold text-[var(--color-text-primary)] sm:text-4xl">
                Everything You Need to
                <span className="text-[var(--color-primary)]"> Trade Smarter</span>
              </h2>
              <p className="mt-4 text-lg text-[var(--color-text-secondary)]">
                Professional-grade tools designed for modern traders
              </p>
            </div>

            <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-4">
              {features.map((feature, index) => (
                <div
                  key={index}
                  className="group relative rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 transition-all hover:border-[var(--color-primary)]/50 hover:shadow-xl"
                >
                  <div className="mb-4 text-3xl">{feature.icon}</div>
                  <h3 className="mb-2 text-lg font-semibold text-[var(--color-text-primary)]">
                    {feature.title}
                  </h3>
                  <p className="text-sm text-[var(--color-text-secondary)]">{feature.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-24">
          <div className="container-grid">
            <div className="relative overflow-hidden rounded-3xl bg-[var(--color-primary)] p-8 sm:p-16">
              <div className="absolute inset-0 opacity-10">
                <div className="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-[var(--color-surface)]" />
                <div className="absolute -bottom-20 -left-20 h-64 w-64 rounded-full bg-[var(--color-surface)]" />
              </div>

              <div className="relative text-center">
                <h2 className="mb-4 text-3xl font-bold text-white sm:text-4xl">
                  Ready to Start Trading Smarter?
                </h2>
                <p className="mx-auto mb-8 max-w-2xl text-lg text-white/80">
                  Join thousands of traders who use BedaanWaves for professional-grade analysis and AI-powered insights.
                </p>
                <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
                  <Link
                    href="/register"
                    className="inline-flex items-center gap-2 rounded-md bg-white px-8 py-4 text-base font-semibold text-[var(--color-primary)] transition-all hover:bg-gray-100"
                  >
                    Start Free Trial
                    <span className="text-xl">→</span>
                  </Link>
                  <Link
                    href="/about"
                    className="inline-flex items-center gap-2 rounded-md border-2 border-white px-8 py-4 text-base font-semibold text-white transition-all hover:bg-white/10"
                  >
                    Learn More
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </section>
      </PageTransition>
    </PublicLayout>
  );
}
