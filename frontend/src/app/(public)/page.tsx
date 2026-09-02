"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { PublicLayout } from "@/components/layout/PublicLayout";
import { PageTransition } from "@/components/layout/PageTransition";

const features = [
  {
    title: "Real-Time Market Data",
    description: "Live streaming data from global exchanges with sub-50ms latency. Never miss a market move.",
  },
  {
    title: "AI-Powered Scoring",
    description: "6-dimensional scoring engine across 305 nodes — Fundamental, Technical, Sentiment, Risk, Macro, and AI.",
  },
  {
    title: "Technical Analysis",
    description: "50+ indicators including RSI, MACD, Moving Averages, Bollinger Bands, and Volume Profile.",
  },
  {
    title: "Fundamental Analysis",
    description: "Deep fundamental metrics — P/E, ROE, Book Value, Revenue Growth, Debt-to-Equity ratios.",
  },
  {
    title: "Sentiment Analysis",
    description: "Persian and multi-language NLP processing of news, social media, and financial reports.",
  },
  {
    title: "Risk Assessment",
    description: "Portfolio VaR, Sharpe Ratio, Max Drawdown, and advanced volatility forecasting models.",
  },
  {
    title: "Price Prediction",
    description: "LSTM, ARIMA, and Prophet ensemble models for forecasting future price movements.",
  },
  {
    title: "Pattern Recognition",
    description: "Automated chart pattern detection and anomaly identification across all tracked assets.",
  },
];

const steps = [
  {
    number: "01",
    title: "Create Account",
    description: "Sign up in seconds with just your email. No credit card required to start.",
  },
  {
    number: "02",
    title: "Configure Markets",
    description: "Select your preferred markets, indices, and industries to personalize your dashboard.",
  },
  {
    number: "03",
    title: "Start Analyzing",
    description: "Access AI-powered scores and real-time charts instantly.",
  },
];

const stats = [
  { value: "5,000+", label: "Stocks Tracked", sub: "NASDAQ & Global Exchanges" },
  { value: "99.9%", label: "Platform Uptime", sub: "Enterprise-grade reliability" },
  { value: "<50ms", label: "Data Latency", sub: "Real-time streaming" },
  { value: "24/7", label: "Market Monitoring", sub: "Continuous tracking" },
];

const testimonials = [
  {
    quote: "The AI scoring system has completely transformed how I evaluate stocks. It's like having a research team on call 24/7.",
    author: "Sarah Chen",
    role: "Portfolio Manager",
  },
  {
    quote: "Real-time data combined with technical analysis tools gives me the edge I need in volatile markets.",
    author: "Marcus Rodriguez",
    role: "Day Trader",
  },
  {
    quote: "The sentiment analysis feature is a game-changer. Being able to gauge market mood across languages is invaluable.",
    author: "Elena Kowalski",
    role: "Quantitative Analyst",
  },
];

export default function HomePage() {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <PublicLayout>
      <PageTransition>
        {/* Hero Section */}
        <section className="relative overflow-hidden pt-20 pb-24 lg:pt-32 lg:pb-40">
          <div className="absolute inset-0 overflow-hidden">
            <div className="absolute -top-1/2 -right-1/4 h-[800px] w-[800px] rounded-full bg-[var(--color-primary)]/5 blur-3xl" />
            <div className="absolute -bottom-1/2 -left-1/4 h-[600px] w-[600px] rounded-full bg-[var(--color-primary)]/5 blur-3xl" />
          </div>

          <div className="relative container-grid">
            <div className="text-center">
              <div className="mb-8 inline-flex items-center gap-2 rounded-full border border-[var(--color-primary)]/30 bg-[var(--color-primary)]/10 px-4 py-1.5">
                <span className="flex h-2 w-2 animate-pulse rounded-full bg-[var(--color-primary)]" />
                <span className="text-sm font-medium text-[var(--color-primary)]">Live Market Data Active</span>
              </div>

              <h1 className="mb-6 text-4xl font-bold leading-tight tracking-tight text-[var(--color-text-primary)] sm:text-5xl lg:text-7xl">
                Master the Markets
                <br />
                <span className="bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-primary-hover)] bg-clip-text text-transparent">
                  with AI
                </span>
              </h1>

              <p className="mx-auto mb-10 max-w-2xl text-lg text-[var(--color-text-secondary)] sm:text-xl">
                Professional-grade market analysis platform with AI-powered scoring,
                real-time data, and advanced technical analysis
                for informed decisions.
              </p>

              <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
                <Link
                  href="/register"
                  className="group flex items-center gap-2 rounded-lg bg-[var(--color-primary)] px-8 py-4 text-base font-semibold text-white shadow-lg shadow-[var(--color-primary)]/25 transition-all hover:bg-[var(--color-primary-hover)] hover:shadow-xl hover:shadow-[var(--color-primary)]/30"
                >
                  Get Started Free
                  <span className="text-xl transition-transform group-hover:translate-x-1">→</span>
                </Link>
                <Link
                  href="/login"
                  className="flex items-center gap-2 rounded-lg border-2 border-[var(--color-border)] bg-[var(--color-surface)] px-8 py-4 text-base font-semibold text-[var(--color-text-primary)] transition-all hover:border-[var(--color-primary)] hover:bg-[var(--color-primary-light)]"
                >
                  Sign In
                </Link>
              </div>
            </div>
          </div>
        </section>

        {/* Stats Section */}
        <section className={`border-y border-[var(--color-border)] bg-[var(--color-surface)]/50 py-12 transition-all ${scrolled ? "shadow-md" : ""}`}>
          <div className="container-grid">
            <div className="grid grid-cols-2 gap-8 md:grid-cols-4">
              {stats.map((stat, index) => (
                <div key={index} className="text-center">
                  <div className="text-3xl font-bold text-[var(--color-text-primary)] sm:text-4xl">{stat.value}</div>
                  <div className="mt-1 text-sm font-medium text-[var(--color-text-secondary)]">{stat.label}</div>
                  <div className="mt-0.5 text-xs text-[var(--color-text-muted)]">{stat.sub}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section id="features" className="py-24">
          <div className="container-grid">
            <div className="text-center mb-16">
              <h2 className="text-3xl font-bold text-[var(--color-text-primary)] sm:text-4xl lg:text-5xl">
                Everything You Need to
                <span className="text-[var(--color-primary)]"> Trade Smarter</span>
              </h2>
              <p className="mt-4 text-lg text-[var(--color-text-secondary)] max-w-2xl mx-auto">
                Comprehensive tools and AI-powered insights designed for modern traders and investors
              </p>
            </div>

            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
              {features.map((feature, index) => (
                <div
                  key={index}
                  className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 transition-all duration-300 hover:border-[var(--color-primary)]/50 hover:shadow-xl"
                >
                  <h3 className="mb-2 text-lg font-semibold text-[var(--color-text-primary)]">
                    {feature.title}
                  </h3>
                  <p className="text-sm leading-relaxed text-[var(--color-text-secondary)]">{feature.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* How It Works Section */}
        <section className="py-24 bg-[var(--color-surface)]/30">
          <div className="container-grid">
            <div className="text-center mb-16">
              <h2 className="text-3xl font-bold text-[var(--color-text-primary)] sm:text-4xl">
                Get Started in
                <span className="text-[var(--color-primary)]"> 3 Simple Steps</span>
              </h2>
              <p className="mt-4 text-lg text-[var(--color-text-secondary)]">
                From signup to analysis in minutes
              </p>
            </div>

            <div className="grid gap-8 md:grid-cols-3">
              {steps.map((step, index) => (
                <div key={index} className="relative text-center">
                  <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-2xl bg-[var(--color-primary)]/10 text-3xl font-bold text-[var(--color-primary)]">
                    {step.number}
                  </div>
                  <h3 className="mb-3 text-xl font-semibold text-[var(--color-text-primary)]">{step.title}</h3>
                  <p className="text-[var(--color-text-secondary)] max-w-sm mx-auto">{step.description}</p>
                  {index < steps.length - 1 && (
                    <div className="hidden md:block absolute top-10 left-[60%] w-[80%] border-t-2 border-dashed border-[var(--color-border)]" />
                  )}
                </div>
              ))}
            </div>

            <div className="mt-16 text-center">
              <Link
                href="/register"
                className="inline-flex items-center gap-2 rounded-lg bg-[var(--color-primary)] px-8 py-4 text-base font-semibold text-white shadow-lg shadow-[var(--color-primary)]/25 transition-all hover:bg-[var(--color-primary-hover)] hover:shadow-xl"
              >
                Create Free Account
                <span className="text-xl">→</span>
              </Link>
            </div>
          </div>
        </section>

        {/* Testimonials Section */}
        <section className="py-24">
          <div className="container-grid">
            <div className="text-center mb-16">
              <h2 className="text-3xl font-bold text-[var(--color-text-primary)] sm:text-4xl">
                Trusted by
                <span className="text-[var(--color-primary)]"> Professional Traders</span>
              </h2>
            </div>

            <div className="grid gap-8 md:grid-cols-3">
              {testimonials.map((testimonial, index) => (
                <div
                  key={index}
                  className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-8 shadow-sm transition-all hover:shadow-lg"
                >
                  <p className="mb-6 text-[var(--color-text-secondary)] italic">{testimonial.quote}</p>
                  <div>
                    <div className="font-semibold text-[var(--color-text-primary)]">{testimonial.author}</div>
                    <div className="text-sm text-[var(--color-text-muted)]">{testimonial.role}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Platform Highlights */}
        <section className="py-24 bg-[var(--color-surface)]/30">
          <div className="container-grid">
            <div className="text-center mb-16">
              <h2 className="text-3xl font-bold text-[var(--color-text-primary)] sm:text-4xl">
                Powerful
                <span className="text-[var(--color-primary)]"> Platform Features</span>
              </h2>
            </div>

            <div className="grid gap-8 md:grid-cols-2">
              <div className="flex gap-4 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 transition-all hover:border-[var(--color-primary)]/30">
                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-[var(--color-primary)]/10 text-2xl font-bold text-[var(--color-primary)]">
                  01
                </div>
                <div>
                  <h3 className="mb-2 text-lg font-semibold text-[var(--color-text-primary)]">Interactive Charts</h3>
                  <p className="text-sm text-[var(--color-text-secondary)]">
                    Professional candlestick charts with volume indicators, drawing tools, and multi-timeframe analysis.
                  </p>
                </div>
              </div>

              <div className="flex gap-4 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 transition-all hover:border-[var(--color-primary)]/30">
                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-[var(--color-primary)]/10 text-2xl font-bold text-[var(--color-primary)]">
                  02
                </div>
                <div>
                  <h3 className="mb-2 text-lg font-semibold text-[var(--color-text-primary)]">Smart Alerts</h3>
                  <p className="text-sm text-[var(--color-text-secondary)]">
                    Multi-channel notifications via email, push, SMS, and Telegram when your conditions are met.
                  </p>
                </div>
              </div>

              <div className="flex gap-4 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 transition-all hover:border-[var(--color-primary)]/30">
                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-[var(--color-primary)]/10 text-2xl font-bold text-[var(--color-primary)]">
                  03
                </div>
                <div>
                  <h3 className="mb-2 text-lg font-semibold text-[var(--color-text-primary)]">News & Sentiment</h3>
                  <p className="text-sm text-[var(--color-text-secondary)]">
                    Real-time news aggregation with AI sentiment scoring to gauge market mood and impact.
                  </p>
                </div>
              </div>

              <div className="flex gap-4 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 transition-all hover:border-[var(--color-primary)]/30">
                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-[var(--color-primary)]/10 text-2xl font-bold text-[var(--color-primary)]">
                  04
                </div>
                <div>
                  <h3 className="mb-2 text-lg font-semibold text-[var(--color-text-primary)]">Portfolio Tracking</h3>
                  <p className="text-sm text-[var(--color-text-secondary)]">
                    Track holdings, P&L, and performance metrics across your entire investment portfolio.
                  </p>
                </div>
              </div>

              <div className="flex gap-4 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 transition-all hover:border-[var(--color-primary)]/30">
                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-[var(--color-primary)]/10 text-2xl font-bold text-[var(--color-primary)]">
                  05
                </div>
                <div>
                  <h3 className="mb-2 text-lg font-semibold text-[var(--color-text-primary)]">Dark & Light Themes</h3>
                  <p className="text-sm text-[var(--color-text-secondary)]">
                    Seamless theme switching with system preference detection. Optimized for extended trading sessions.
                  </p>
                </div>
              </div>

              <div className="flex gap-4 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 transition-all hover:border-[var(--color-primary)]/30">
                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-[var(--color-primary)]/10 text-2xl font-bold text-[var(--color-primary)]">
                  06
                </div>
                <div>
                  <h3 className="mb-2 text-lg font-semibold text-[var(--color-text-primary)]">Secure Authentication</h3>
                  <p className="text-sm text-[var(--color-text-secondary)]">
                    JWT-based secure login with password recovery. Your data is encrypted and protected.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-24">
          <div className="container-grid">
            <div className="relative overflow-hidden rounded-3xl bg-[var(--color-primary)] px-8 py-16 sm:px-16 sm:py-24">
              <div className="absolute inset-0 opacity-10">
                <div className="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-white" />
                <div className="absolute -bottom-20 -left-20 h-64 w-64 rounded-full bg-white" />
              </div>

              <div className="relative text-center">
                <h2 className="mb-4 text-3xl font-bold text-white sm:text-4xl lg:text-5xl">
                  Ready to Trade Smarter?
                </h2>
                <p className="mx-auto mb-8 max-w-2xl text-lg text-white/80">
                  Join thousands of traders who use BedaanWaves for professional-grade analysis
                  and AI-powered market insights.
                </p>
                <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
                  <Link
                    href="/register"
                    className="inline-flex items-center gap-2 rounded-lg bg-white px-8 py-4 text-base font-semibold text-[var(--color-primary)] shadow-lg transition-all hover:bg-gray-100 hover:shadow-xl"
                  >
                    Create Free Account
                    <span className="text-xl">→</span>
                  </Link>
                  <Link
                    href="/login"
                    className="inline-flex items-center gap-2 rounded-lg border-2 border-white px-8 py-4 text-base font-semibold text-white transition-all hover:bg-white/10"
                  >
                    Sign In
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
