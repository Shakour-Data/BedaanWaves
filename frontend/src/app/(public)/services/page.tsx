import { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Services | BedaanWaves",
  description: "Explore BedaanWaves services including real-time market data, AI-powered scoring, technical analysis, portfolio tracking, and more.",
};

const services = [
  {
    icon: "📊",
    title: "Real-Time Market Data",
    description:
      "Access live NASDAQ market data with millisecond latency updates. Track thousands of stocks, indices, and ETFs with real-time price movements, volume, and market depth.",
    features: ["Live price feeds", "Volume analysis", "Market depth"],
  },
  {
    icon: "🤖",
    title: "AI-Powered Scoring",
    description:
      "Advanced machine learning models analyze multiple data points to generate actionable stock scores. Our AI evaluates fundamentals, technicals, and market sentiment.",
    features: ["Multi-factor scoring", "Sentiment analysis", "Pattern recognition"],
  },
  {
    icon: "📈",
    title: "Technical Analysis",
    description:
      "Professional-grade charting tools with 100+ technical indicators. Identify trends, patterns, and entry/exit points with precision.",
    features: ["100+ indicators", "Pattern recognition", "Custom timeframes"],
  },
  {
    icon: "💼",
    title: "Portfolio Tracking",
    description:
      "Track your portfolio performance in real-time. Monitor gains, losses, diversification, and risk metrics all in one place.",
    features: ["Performance analytics", "Risk metrics", "Diversification insights"],
  },
  {
    icon: "🔔",
    title: "Smart Alerts",
    description:
      "Set custom alerts for price movements, volume spikes, and news events. Never miss a trading opportunity.",
    features: ["Price alerts", "Volume alerts", "News alerts"],
  },
  {
    icon: "📰",
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
    <div className="page-transition-enter">
      {/* Hero */}
      <section className="relative overflow-hidden py-16 lg:py-24">
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute -top-1/2 -right-1/4 h-[600px] w-[600px] rounded-full bg-[var(--color-primary)]/5 blur-3xl" />
        </div>
        <div className="relative container-grid">
          <div className="max-w-3xl">
            <h1 className="text-4xl font-bold tracking-tight text-[var(--color-text-primary)] sm:text-5xl">
              Our <span className="text-[var(--color-primary)]">Services</span>
            </h1>
            <p className="mt-6 text-lg text-[var(--color-text-secondary)]">
              Comprehensive market analysis tools designed for modern traders. From real-time data to AI-powered insights, we provide everything you need to make smarter trading decisions.
            </p>
          </div>
        </div>
      </section>

      {/* Services Grid */}
      <section className="py-16 border-t border-[var(--color-border)]">
        <div className="container-grid">
          <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
            {services.map((service, index) => (
              <div
                key={index}
                className="group rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm transition-all hover:border-[var(--color-primary)]/50 hover:shadow-xl"
              >
                <div className="mb-4 text-4xl">{service.icon}</div>
                <h3 className="text-lg font-semibold text-[var(--color-text-primary)]">
                  {service.title}
                </h3>
                <p className="mt-2 text-sm text-[var(--color-text-secondary)]">
                  {service.description}
                </p>
                <ul className="mt-4 space-y-2">
                  {service.features.map((feature, i) => (
                    <li key={i} className="flex items-center gap-2 text-sm text-[var(--color-text-secondary)]">
                      <span className="text-[var(--color-primary)]">✓</span>
                      {feature}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section className="py-16 border-t border-[var(--color-border)]">
        <div className="container-grid">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-[var(--color-text-primary)] sm:text-4xl">
              Simple, Transparent <span className="text-[var(--color-primary)]">Pricing</span>
            </h2>
            <p className="mt-4 text-lg text-[var(--color-text-secondary)]">
              Choose the plan that fits your trading needs. All plans include a 14-day free trial.
            </p>
          </div>
          <div className="grid gap-8 lg:grid-cols-3">
            {pricingPlans.map((plan, index) => (
              <div
                key={index}
                className={cn(
                  "relative rounded-2xl border bg-[var(--color-surface)] p-8 shadow-sm",
                  plan.popular
                    ? "border-[var(--color-primary)] shadow-lg"
                    : "border-[var(--color-border)]"
                )}
              >
                {plan.popular && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2 rounded-full bg-[var(--color-primary)] px-4 py-1 text-xs font-semibold text-white">
                    Most Popular
                  </div>
                )}
                <div className="text-center">
                  <h3 className="text-lg font-semibold text-[var(--color-text-primary)]">
                    {plan.name}
                  </h3>
                  <div className="mt-4 flex items-baseline justify-center gap-1">
                    <span className="text-4xl font-bold text-[var(--color-text-primary)]">
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
                      <span className="mt-0.5 text-[var(--color-success)]">✓</span>
                      {feature}
                    </li>
                  ))}
                </ul>
                <Link
                  href={plan.href}
                  className={cn(
                    "mt-8 flex w-full items-center justify-center rounded-lg px-6 py-3 text-sm font-semibold transition-colors",
                    plan.popular
                      ? "bg-[var(--color-primary)] text-white hover:bg-[var(--color-primary-hover)]"
                      : "border border-[var(--color-border)] text-[var(--color-text-primary)] hover:border-[var(--color-primary)] hover:text-[var(--color-primary)]"
                  )}
                >
                  {plan.cta}
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 border-t border-[var(--color-border)]">
        <div className="container-grid">
          <div className="rounded-3xl bg-[var(--color-primary)] p-8 sm:p-16 text-center">
            <h2 className="text-3xl font-bold text-white sm:text-4xl">
              Need a Custom Solution?
            </h2>
            <p className="mx-auto mt-4 max-w-2xl text-lg text-white/80">
              Contact our team to discuss enterprise solutions, API integrations, or custom features tailored to your needs.
            </p>
            <div className="mt-8">
              <Link
                href="/contact"
                className="inline-flex items-center gap-2 rounded-md bg-white px-8 py-4 text-base font-semibold text-[var(--color-primary)] transition-all hover:bg-gray-100"
              >
                Contact Sales
                <span className="text-xl">→</span>
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

function cn(...classes: (string | boolean | undefined)[]) {
  return classes.filter(Boolean).join(" ");
}
