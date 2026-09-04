"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { PublicLayout } from "@/components/layout/PublicLayout";
import { PageTransition } from "@/components/layout/PageTransition";
import { ArrowRight, TrendingUp, Brain, BarChart3, Shield, Zap, Globe, Sparkles } from "lucide-react";

const features = [
  {
    title: "Real-Time Market Data",
    description: "Live streaming data from global exchanges with sub-50ms latency. Never miss a market move.",
    icon: TrendingUp,
  },
  {
    title: "AI-Powered Scoring",
    description: "6-dimensional scoring engine across 305 nodes — Fundamental, Technical, Sentiment, Risk, Macro, and AI.",
    icon: Brain,
  },
  {
    title: "Technical Analysis",
    description: "50+ indicators including RSI, MACD, Moving Averages, Bollinger Bands, and Volume Profile.",
    icon: BarChart3,
  },
  {
    title: "Fundamental Analysis",
    description: "Deep fundamental metrics — P/E, ROE, Book Value, Revenue Growth, Debt-to-Equity ratios.",
    icon: BarChart3,
  },
  {
    title: "Sentiment Analysis",
    description: "Persian and multi-language NLP processing of news, social media, and financial reports.",
    icon: Globe,
  },
  {
    title: "Risk Assessment",
    description: "Portfolio VaR, Sharpe Ratio, Max Drawdown, and advanced volatility forecasting models.",
    icon: Shield,
  },
  {
    title: "Price Prediction",
    description: "LSTM, ARIMA, and Prophet ensemble models for forecasting future price movements.",
    icon: Sparkles,
  },
  {
    title: "Pattern Recognition",
    description: "Automated chart pattern detection and anomaly identification across all tracked assets.",
    icon: Zap,
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
        <section className="relative overflow-hidden pt-28 pb-20 lg:pt-40 lg:pb-32">
          <div className="absolute inset-0 overflow-hidden">
            <div className="absolute -top-1/2 -right-1/4 h-[800px] w-[800px] rounded-full bg-[var(--color-primary)]/5 blur-3xl animate-pulse" />
            <div className="absolute -bottom-1/2 -left-1/4 h-[600px] w-[600px] rounded-full bg-[var(--color-accent)]/5 blur-3xl animate-pulse" style={{ animationDelay: "1s" }} />
          </div>

          <div className="relative container-grid">
            <div className="text-center max-w-4xl mx-auto">
              <div className="mb-8 inline-flex items-center gap-2 rounded-full border border-[var(--color-primary)]/30 bg-[var(--color-primary-soft)] px-4 py-1.5 backdrop-blur-sm">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[var(--color-success)] opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-[var(--color-success)]"></span>
                </span>
                <span className="text-sm font-medium text-[var(--color-primary)]">Live Market Data Active</span>
              </div>

              <h1 className="mb-8 text-5xl font-bold leading-[1.1] tracking-tight text-[var(--color-text-primary)] sm:text-6xl lg:text-7xl text-balance">
                Master the Markets
                <br />
                <span className="bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-accent)] bg-clip-text text-transparent">
                  with AI
                </span>
              </h1>

              <p className="mx-auto mb-10 max-w-2xl text-lg sm:text-xl text-[var(--color-text-secondary)] text-balance leading-relaxed">
                Professional-grade market analysis platform with AI-powered scoring,
                real-time data, and advanced technical analysis
                for informed decisions.
              </p>

              <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
                <Link
                  href="/register"
                  className="group flex items-center gap-2 rounded-xl bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-primary-hover)] px-8 py-4 text-base font-semibold text-white shadow-xl shadow-[var(--color-primary)]/25 transition-all hover:shadow-2xl hover:shadow-[var(--color-primary)]/30 hover:-translate-y-0.5"
                >
                  Get Started Free
                  <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                </Link>
                <Link
                  href="/login"
                  className="flex items-center gap-2 rounded-xl border-2 border-[var(--color-border)] bg-[var(--color-surface)] px-8 py-4 text-base font-semibold text-[var(--color-text-primary)] transition-all hover:border-[var(--color-primary)] hover:bg-[var(--color-primary-light)] hover:shadow-lg"
                >
                  Sign In
                </Link>
              </div>
            </div>
          </div>
        </section>

        {/* Stats Section */}
        <section className={`border-y border-[var(--color-border)] bg-[var(--color-surface)]/80 backdrop-blur-sm py-12 transition-all ${scrolled ? "shadow-md" : ""}`}>
          <div className="container-grid">
            <div className="grid grid-cols-2 gap-8 md:grid-cols-4">
              {stats.map((stat, index) => (
                <div key={index} className="text-center group">
                  <div className="text-3xl font-bold text-[var(--color-text-primary)] sm:text-4xl bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-accent)] bg-clip-text text-transparent group-hover:from-[var(--color-primary-hover)] group-hover:to-[var(--color-primary)] transition-all">
                    {stat.value}
                  </div>
                  <div className="mt-1 text-sm font-semibold text-[var(--color-text-secondary)]">{stat.label}</div>
                  <div className="mt-0.5 text-xs text-[var(--color-text-muted)]">{stat.sub}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section id="features" className="py-24">
          <div className="container-grid">
            <div className="text-center mb-16 max-w-3xl mx-auto">
              <h2 className="text-3xl font-bold text-[var(--color-text-primary)] sm:text-4xl lg:text-5xl text-balance">
                Everything You Need to
                <span className="bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-accent)] bg-clip-text text-transparent"> Trade Smarter</span>
              </h2>
              <p className="mt-6 text-lg text-[var(--color-text-secondary)] max-w-2xl mx-auto">
                Comprehensive tools and AI-powered insights designed for modern traders and investors
              </p>
            </div>

            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
              {features.map((feature, index) => {
                const Icon = feature.icon;
                return (
                  <div
                    key={index}
                    className="group rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 transition-all duration-300 hover:border-[var(--color-primary)]/50 hover:shadow-xl hover:shadow-[var(--color-primary)]/5 hover:-translate-y-1"
                  >
                    <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-xl bg-[var(--color-primary-soft)] text-[var(--color-primary)] group-hover:bg-[var(--color-primary)] group-hover:text-white transition-all duration-300">
                      <Icon className="h-6 w-6" />
                    </div>
                    <h3 className="mb-2 text-lg font-semibold text-[var(--color-text-primary)]">
                      {feature.title}
                    </h3>
                    <p className="text-sm leading-relaxed text-[var(--color-text-secondary)]">{feature.description}</p>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        {/* How It Works Section */}
        <section className="py-24 bg-[var(--color-surface)]/30">
          <div className="container-grid">
            <div className="text-center mb-16">
              <h2 className="text-3xl font-bold text-[var(--color-text-primary)] sm:text-4xl text-balance">
                Get Started in
                <span className="bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-accent)] bg-clip-text text-transparent"> 3 Simple Steps</span>
              </h2>
              <p className="mt-4 text-lg text-[var(--color-text-secondary)]">
                From signup to analysis in minutes
              </p>
            </div>

            <div className="grid gap-8 md:grid-cols-3">
              {steps.map((step, index) => (
                <div key={index} className="relative text-center group">
                  <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-accent)] text-3xl font-bold text-white shadow-lg shadow-[var(--color-primary)]/25 group-hover:shadow-xl group-hover:shadow-[var(--color-primary)]/30 transition-all group-hover:scale-105">
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
                className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-primary-hover)] px-8 py-4 text-base font-semibold text-white shadow-lg shadow-[var(--color-primary)]/25 transition-all hover:shadow-xl hover:shadow-[var(--color-primary)]/30 hover:-translate-y-0.5"
              >
                Create Free Account
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </div>
        </section>

        {/* Testimonials Section */}
        <section className="py-24">
          <div className="container-grid">
            <div className="text-center mb-16">
              <h2 className="text-3xl font-bold text-[var(--color-text-primary)] sm:text-4xl text-balance">
                Trusted by
                <span className="bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-accent)] bg-clip-text text-transparent"> Professional Traders</span>
              </h2>
            </div>

            <div className="grid gap-8 md:grid-cols-3">
              {testimonials.map((testimonial, index) => (
                <div
                  key={index}
                  className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-8 shadow-sm transition-all hover:shadow-lg hover:border-[var(--color-primary)]/30 hover:-translate-y-1"
                >
                  <div className="flex items-center gap-1 mb-4">
                    {[...Array(5)].map((_, i) => (
                      <svg key={i} className="h-4 w-4 text-[var(--color-warning)]" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                      </svg>
                    ))}
                  </div>
                  <p className="mb-6 text-[var(--color-text-secondary)] italic leading-relaxed">{testimonial.quote}</p>
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-accent)] text-sm font-bold text-white">
                      {testimonial.author.split(" ").map(n => n[0]).join("")}
                    </div>
                    <div>
                      <div className="font-semibold text-[var(--color-text-primary)] text-sm">{testimonial.author}</div>
                      <div className="text-xs text-[var(--color-text-muted)]">{testimonial.role}</div>
                    </div>
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
              <h2 className="text-3xl font-bold text-[var(--color-text-primary)] sm:text-4xl text-balance">
                Powerful
                <span className="bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-accent)] bg-clip-text text-transparent"> Platform Features</span>
              </h2>
            </div>

            <div className="grid gap-8 md:grid-cols-2">
              {[
                { num: "01", title: "Interactive Charts", desc: "Professional candlestick charts with volume indicators, drawing tools, and multi-timeframe analysis." },
                { num: "02", title: "Smart Alerts", desc: "Multi-channel notifications via email, push, SMS, and Telegram when your conditions are met." },
                { num: "03", title: "News & Sentiment", desc: "Real-time news aggregation with AI sentiment scoring to gauge market mood and impact." },
                { num: "04", title: "Portfolio Tracking", desc: "Track holdings, P&L, and performance metrics across your entire investment portfolio." },
                { num: "05", title: "Dark & Light Themes", desc: "Seamless theme switching with system preference detection. Optimized for extended trading sessions." },
                { num: "06", title: "Secure Authentication", desc: "JWT-based secure login with password recovery. Your data is encrypted and protected." },
              ].map((item, index) => (
                <div key={index} className="flex gap-5 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 transition-all hover:border-[var(--color-primary)]/30 hover:shadow-lg group">
                  <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-accent)] text-lg font-bold text-white shadow-md group-hover:shadow-lg transition-all">
                    {item.num}
                  </div>
                  <div>
                    <h3 className="mb-2 text-lg font-semibold text-[var(--color-text-primary)]">{item.title}</h3>
                    <p className="text-sm text-[var(--color-text-secondary)] leading-relaxed">
                      {item.desc}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-24">
          <div className="container-grid">
            <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-accent)] px-8 py-16 sm:px-16 sm:py-24 shadow-2xl">
              <div className="absolute inset-0 opacity-10">
                <div className="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-white" />
                <div className="absolute -bottom-20 -left-20 h-64 w-64 rounded-full bg-white" />
              </div>

              <div className="relative text-center">
                <h2 className="mb-4 text-3xl font-bold text-white sm:text-4xl lg:text-5xl text-balance">
                  Ready to Trade Smarter?
                </h2>
                <p className="mx-auto mb-8 max-w-2xl text-lg text-white/90">
                  Join thousands of traders who use BedaanWaves for professional-grade analysis
                  and AI-powered market insights.
                </p>
                <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
                  <Link
                    href="/register"
                    className="inline-flex items-center gap-2 rounded-xl bg-white px-8 py-4 text-base font-semibold text-[var(--color-primary)] shadow-lg transition-all hover:bg-gray-100 hover:shadow-xl hover:-translate-y-0.5"
                  >
                    Create Free Account
                    <ArrowRight className="h-4 w-4" />
                  </Link>
                  <Link
                    href="/login"
                    className="inline-flex items-center gap-2 rounded-xl border-2 border-white px-8 py-4 text-base font-semibold text-white transition-all hover:bg-white/10 hover:shadow-lg"
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
