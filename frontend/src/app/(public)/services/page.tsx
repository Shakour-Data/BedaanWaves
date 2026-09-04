import { Metadata } from "next";
import Link from "next/link";
import { PublicLayout } from "@/components/layout/PublicLayout";
import { ArrowRight, Check, Zap, BarChart3, Globe, Bell, Newspaper, TrendingUp } from "lucide-react";

export const metadata: Metadata = {
  title: "Services | BedaanWaves",
  description: "Explore BedaanWaves services including real-time market data, AI-powered scoring, technical analysis, portfolio tracking, and more.",
};

const services = [
  {
    icon: TrendingUp,
    title: "Real-Time Market Data",
    description:
      "Access live NASDAQ market data with millisecond latency updates. Track thousands of stocks, indices, and ETFs with real-time price movements, volume, and market depth.",
    features: ["Live price feeds", "Volume analysis", "Market depth"],
  },
  {
    icon: Zap,
    title: "AI-Powered Scoring",
    description:
      "Advanced machine learning models analyze multiple data points to generate actionable stock scores. Our AI evaluates fundamentals, technicals, and market sentiment.",
    features: ["Multi-factor scoring", "Sentiment analysis", "Pattern recognition"],
  },
  {
    icon: BarChart3,
    title: "Technical Analysis",
    description:
      "Professional-grade charting tools with 100+ technical indicators. Identify trends, patterns, and entry/exit points with precision.",
    features: ["100+ indicators", "Pattern recognition", "Custom timeframes"],
  },
  {
    icon: Globe,
    title: "Portfolio Tracking",
    description:
      "Track your portfolio performance in real-time. Monitor gains, losses, diversification, and risk metrics all in one place.",
    features: ["Performance analytics", "Risk metrics", "Diversification insights"],
  },
  {
    icon: Bell,
    title: "Smart Alerts",
    description:
      "Set custom alerts for price movements, volume spikes, and news events. Never miss a trading opportunity.",
    features: ["Price alerts", "Volume alerts", "News alerts"],
  },
  {
    icon: Newspaper,
    title: "Market News & Insights",
    description:
      "Stay informed with curated market news, earnings reports, and expert analysis. Filter by sector, ticker, or market event.",
    features: ["Curated news feed", "Earnings calendar", "Expert commentary"],
  },
];

const pricingPlans = [
  {
    name: "Starter",
    price: "$0",
    period: "/month",
    description: "Perfect for getting started with market analysis.",
    features: ["Basic market data", "5 watchlists", "3 technical indicators", "Email alerts"],
    cta: "Get Started",
    href: "/register",
  },
  {
    name: "Pro",
    price: "$29",
    period: "/month",
    description: "For serious traders who need advanced tools.",
    features: ["Real-time data", "Unlimited watchlists", "All technical indicators", "AI scoring", "Portfolio tracking", "Priority support"],
    cta: "Start Free Trial",
    href: "/register",
    popular: true,
  },
  {
    name: "Enterprise",
    price: "$99",
    period: "/month",
    description: "For teams and institutions requiring full access.",
    features: ["Everything in Pro", "API access", "Custom integrations", "Dedicated support", "White-label options", "Advanced analytics"],
    cta: "Contact Sales",
    href: "/contact",
  },
];

export default function ServicesPage() {
  return (
    <PublicLayout>
      <div className="page-transition-enter">
        {/* Hero */}
        <section className="relative overflow-hidden py-20 lg:py-32">
          <div className="absolute inset-0 overflow-hidden">
            <div className="absolute -top-1/2 -right-1/4 h-[600px] w-[600px] rounded-full bg-[var(--color-primary)]/5 blur-3xl" />
            <div className="absolute -bottom-1/2 -left-1/4 h-[400px] w-[400px] rounded-full bg-[var(--color-accent)]/5 blur-3xl" />
          </div>
          <div className="relative container-grid">
            <div className="max-w-3xl">
              <div className="inline-flex items-center gap-2 rounded-full border border-[var(--color-primary)]/30 bg-[var(--color-primary-soft)] px-4 py-1.5 mb-6">
                <span className="text-sm font-medium text-[var(--color-primary)]">What We Offer</span>
              </div>
              <h1 className="text-4xl font-bold tracking-tight text-[var(--color-text-primary)] sm:text-5xl lg:text-6xl text-balance">
                Our <span className="bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-accent)] bg-clip-text text-transparent">Services</span>
              </h1>
              <p className="mt-8 text-lg text-[var(--color-text-secondary)] leading-relaxed max-w-2xl">
                Comprehensive market analysis tools designed for modern traders. From real-time data to AI-powered insights, we provide everything you need to make smarter trading decisions.
              </p>
            </div>
          </div>
        </section>

        {/* Services Grid */}
        <section className="py-20 border-t border-[var(--color-border)]">
          <div className="container-grid">
            <div className="text-center mb-16">
              <h2 className="text-3xl font-bold text-[var(--color-text-primary)] sm:text-4xl text-balance">
                Powerful <span className="bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-accent)] bg-clip-text text-transparent">Tools</span>
              </h2>
              <p className="mt-4 text-lg text-[var(--color-text-secondary)] max-w-2xl mx-auto">
                Everything you need to analyze markets and make informed decisions
              </p>
            </div>
            <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
              {services.map((service, index) => {
                const Icon = service.icon;
                return (
                  <div
                    key={index}
                    className="group rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm transition-all hover:border-[var(--color-primary)]/50 hover:shadow-xl hover:-translate-y-1"
                  >
                    <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-xl bg-[var(--color-primary-soft)] text-[var(--color-primary)] group-hover:bg-gradient-to-br group-hover:from-[var(--color-primary)] group-hover:to-[var(--color-accent)] group-hover:text-white transition-all duration-300">
                      <Icon className="h-6 w-6" />
                    </div>
                    <h3 className="text-lg font-semibold text-[var(--color-text-primary)]">
                      {service.title}
                    </h3>
                    <p className="mt-3 text-sm text-[var(--color-text-secondary)] leading-relaxed">
                      {service.description}
                    </p>
                    <ul className="mt-4 space-y-2">
                      {service.features.map((feature, i) => (
                        <li key={i} className="flex items-center gap-2 text-sm text-[var(--color-text-secondary)]">
                          <Check className="h-4 w-4 text-[var(--color-success)] shrink-0" />
                          {feature}
                        </li>
                      ))}
                    </ul>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        {/* Pricing */}
        <section className="py-20 border-t border-[var(--color-border)]">
          <div className="container-grid">
            <div className="text-center mb-16">
              <h2 className="text-3xl font-bold text-[var(--color-text-primary)] sm:text-4xl text-balance">
                Simple, Transparent <span className="bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-accent)] bg-clip-text text-transparent">Pricing</span>
              </h2>
              <p className="mt-4 text-lg text-[var(--color-text-secondary)] max-w-2xl mx-auto">
                Choose the plan that fits your trading needs. All plans include a 14-day free trial.
              </p>
            </div>
            <div className="grid gap-8 lg:grid-cols-3">
              {pricingPlans.map((plan, index) => (
                <div
                  key={index}
                  className={cn(
                    "relative rounded-2xl border bg-[var(--color-surface)] p-8 shadow-sm transition-all hover:shadow-lg",
                    plan.popular
                      ? "border-[var(--color-primary)] shadow-lg scale-[1.02]"
                      : "border-[var(--color-border)]"
                  )}
                >
                  {plan.popular && (
                    <div className="absolute -top-4 left-1/2 -translate-x-1/2 rounded-full bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-accent)] px-4 py-1 text-xs font-semibold text-white shadow-lg">
                      Most Popular
                    </div>
                  )}
                  <div className="text-center">
                    <h3 className="text-lg font-semibold text-[var(--color-text-primary)]">
                      {plan.name}
                    </h3>
                    <div className="mt-4 flex items-baseline justify-center gap-1">
                      <span className="text-4xl font-bold bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-accent)] bg-clip-text text-transparent">
                        {plan.price}
                      </span>
                      <span className="text-[var(--color-text-secondary)]">{plan.period}</span>
                    </div>
                    <p className="mt-2 text-sm text-[var(--color-text-secondary)]">
                      {plan.description}
                    </p>
                  </div>
                  <ul className="mt-8 space-y-3">
                    {plan.features.map((feature, i) => (
                      <li key={i} className="flex items-start gap-3 text-sm text-[var(--color-text-secondary)]">
                        <Check className="mt-0.5 h-4 w-4 text-[var(--color-success)] shrink-0" />
                        {feature}
                      </li>
                    ))}
                  </ul>
                  <Link
                    href={plan.href}
                    className={cn(
                      "mt-8 flex w-full items-center justify-center gap-2 rounded-xl px-6 py-3 text-sm font-semibold transition-all",
                      plan.popular
                        ? "bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-primary-hover)] text-white shadow-lg hover:shadow-xl hover:-translate-y-0.5"
                        : "border border-[var(--color-border)] text-[var(--color-text-primary)] hover:border-[var(--color-primary)] hover:text-[var(--color-primary)] hover:shadow-md"
                    )}
                  >
                    {plan.cta}
                    {plan.popular && <ArrowRight className="h-4 w-4" />}
                  </Link>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="py-20 border-t border-[var(--color-border)]">
          <div className="container-grid">
            <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-accent)] p-8 sm:p-16 text-center shadow-2xl">
              <div className="absolute inset-0 opacity-10">
                <div className="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-white" />
                <div className="absolute -bottom-20 -left-20 h-64 w-64 rounded-full bg-white" />
              </div>
              <div className="relative">
                <h2 className="text-3xl font-bold text-white sm:text-4xl text-balance">
                  Need a Custom Solution?
                </h2>
                <p className="mx-auto mt-4 max-w-2xl text-lg text-white/90">
                  Contact our team to discuss enterprise solutions, API integrations, or custom features tailored to your needs.
                </p>
                <div className="mt-8">
                  <Link
                    href="/contact"
                    className="inline-flex items-center gap-2 rounded-xl bg-white px-8 py-4 text-base font-semibold text-[var(--color-primary)] shadow-lg transition-all hover:bg-gray-100 hover:shadow-xl hover:-translate-y-0.5"
                  >
                    Contact Sales
                    <ArrowRight className="h-4 w-4" />
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>
    </PublicLayout>
  );
}

function cn(...classes: (string | boolean | undefined)[]) {
  return classes.filter(Boolean).join(" ");
}
