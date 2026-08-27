import { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "NasdaqPulse | Professional NASDAQ Stock Analysis",
  description: "Advanced NASDAQ stock analysis platform with real-time data, AI-powered scoring, technical analysis, and portfolio tracking.",
  keywords: "NASDAQ, stock analysis, trading, AI scoring, technical analysis, stocks" };

const features = [
  {
    title: "Real-time Data",
    description: "Live NASDAQ market data with millisecond latency updates"
  },
  {
    title: "AI Scoring",
    description: "Advanced machine learning models for stock ranking"
  },
  {
    title: "Risk Analysis",
    description: "Comprehensive portfolio risk assessment tools"
  },
  {
    title: "Fast Execution",
    description: "Lightning-fast analysis and signal generation"
  }
];

const stats = [
  { value: "5,000+", label: "Stocks Tracked" },
  { value: "99.9%", label: "Uptime" },
  { value: "<50ms", label: "Latency" },
  { value: "24/7", label: "Monitoring" }
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[var(--color-background)]">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 border-b border-[var(--color-border)]/50 bg-[var(--color-background)]/80 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <Link href="/" className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--color-primary)] text-white">
              <span className="font-bold text-lg">N</span>
            </div>
            <span className="text-xl font-bold text-[var(--color-text-primary)]">NasdaqPulse</span>
          </Link>
          
          <div className="hidden items-center gap-8 md:flex">
            <Link href="#features" className="text-sm text-[var(--color-text-secondary)] transition-colors hover:text-[var(--color-text-primary)]">Features</Link>
            <Link href="#pricing" className="text-sm text-[var(--color-text-secondary)] transition-colors hover:text-[var(--color-text-primary)]">Pricing</Link>
            <Link href="#about" className="text-sm text-[var(--color-text-secondary)] transition-colors hover:text-[var(--color-text-primary)]">About</Link>
          </div>

          <div className="flex items-center gap-3">
            <Link 
              href="/login"
              className="hidden rounded-lg px-4 py-2 text-sm font-medium text-[var(--color-text-secondary)] transition-colors hover:text-[var(--color-text-primary)] md:block"
            >
              Sign In
            </Link>
            <Link 
              href="/register"
              className="flex items-center gap-2 rounded-lg bg-[var(--color-primary)] px-4 py-2 text-sm font-medium text-white transition-all hover:bg-[var(--color-primary-hover)]"
            >
              Get Started
              <span className="text-lg">→</span>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative overflow-hidden pt-32 pb-20 lg:pt-40 lg:pb-32">
        {/* Background Effects */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute -top-1/2 -right-1/4 h-[800px] w-[800px] rounded-full bg-[var(--color-primary)]/5 blur-3xl" />
          <div className="absolute -bottom-1/2 -left-1/4 h-[600px] w-[600px] rounded-full bg-[var(--color-primary)]/5 blur-3xl" />
        </div>

        <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            {/* Badge */}
            <div className="mb-8 inline-flex items-center gap-2 rounded-full border border-[var(--color-primary)]/30 bg-[var(--color-primary)]/10 px-4 py-1.5">
              <span className="flex h-2 w-2 animate-pulse rounded-full bg-[var(--color-primary)]" />
              <span className="text-sm font-medium text-[var(--color-primary)]">Live Market Data</span>
            </div>

            {/* Heading */}
            <h1 className="mb-6 text-4xl font-bold leading-tight tracking-tight text-[var(--color-text-primary)] sm:text-5xl lg:text-6xl">
              Master the
              <span className="text-[var(--color-primary)]"> NASDAQ </span>
              Market
            </h1>

            {/* Subheading */}
            <p className="mx-auto mb-10 max-w-2xl text-lg text-[var(--color-text-secondary)]">
              Professional-grade stock analysis platform with AI-powered scoring, 
              real-time data, and advanced technical analysis for NASDAQ stocks.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
              <Link
                href="/register"
                className="group flex items-center gap-2 rounded-md bg-[var(--color-primary)] px-8 py-4 text-base font-semibold text-white transition-all hover:bg-[var(--color-primary-hover)]"
              >
                Start Free Trial
                <span className="text-xl transition-transform group-hover:translate-x-1">→</span>
              </Link>
              <Link
                href="/dashboard"
                className="flex items-center gap-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-8 py-4 text-base font-semibold text-[var(--color-text-primary)] transition-all hover:border-[var(--color-primary)] hover:bg-[var(--color-border)]"
              >
                <span className="text-[var(--color-primary)]">[Chart]</span>
                View Demo
              </Link>
            </div>

            {/* Trust Badges */}
            <div className="mt-16 flex flex-wrap items-center justify-center gap-8 opacity-60">
              <div className="flex items-center gap-2 text-[var(--color-text-secondary)]">
                <span className="text-[var(--color-primary)]">[Security]</span>
                <span className="text-sm">Bank-level Security</span>
              </div>
              <div className="flex items-center gap-2 text-[var(--color-text-secondary)]">
                <span className="text-[var(--color-primary)]">[Global]</span>
                <span className="text-sm">Global Markets</span>
              </div>
              <div className="flex items-center gap-2 text-[var(--color-text-secondary)]">
                <span className="text-[var(--color-primary)]">[Users]</span>
                <span className="text-sm">10K+ Traders</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="border-y border-[var(--color-border)] bg-[var(--color-surface)]/50 py-12">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
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
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
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
                className="group relative rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 transition-all hover:border-[var(--color-primary)]/50 hover:shadow-xl hover:shadow-[#00d4ff]/10"
              >
                <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-xl bg-[var(--color-primary)]/10 text-[var(--color-primary)]">
                  <span className="text-xl font-bold">{index + 1}</span>
                </div>
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
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="relative overflow-hidden rounded-3xl bg-[var(--color-primary)] p-8 sm:p-16">
            {/* Background Pattern */}
            <div className="absolute inset-0 opacity-10">
              <div className="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-[var(--color-surface)]" />
              <div className="absolute -bottom-20 -left-20 h-64 w-64 rounded-full bg-[var(--color-surface)]" />
            </div>

            <div className="relative text-center">
              <h2 className="mb-4 text-3xl font-bold text-white sm:text-4xl">
                Ready to Start Trading Smarter?
              </h2>
              <p className="mx-auto mb-8 max-w-2xl text-lg text-white/80">
                Join thousands of traders who use NasdaqPulse for professional-grade analysis and AI-powered insights.
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
                  href="/login"
                  className="inline-flex items-center gap-2 rounded-md border-2 border-white px-8 py-4 text-base font-semibold text-white transition-all hover:bg-white/10"
                >
                  Sign In
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-[var(--color-border)] bg-[var(--color-background)] py-12">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="grid gap-8 md:grid-cols-4">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--color-primary)]">
                  <span className="text-white font-bold text-sm">N</span>
                </div>
                <span className="text-lg font-bold text-[var(--color-text-primary)]">NasdaqPulse</span>
              </div>
              <p className="text-sm text-[var(--color-text-secondary)]">
                Professional NASDAQ stock analysis platform for modern traders.
              </p>
            </div>
            <div>
              <h4 className="mb-4 text-sm font-semibold text-[var(--color-text-primary)]">Product</h4>
              <ul className="space-y-2">
                <li><Link href="/features" className="text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]">Features</Link></li>
                <li><Link href="/pricing" className="text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]">Pricing</Link></li>
                <li><Link href="/api" className="text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]">API</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="mb-4 text-sm font-semibold text-[var(--color-text-primary)]">Company</h4>
              <ul className="space-y-2">
                <li><Link href="/about" className="text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]">About</Link></li>
                <li><Link href="/blog" className="text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]">Blog</Link></li>
                <li><Link href="/careers" className="text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]">Careers</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="mb-4 text-sm font-semibold text-[var(--color-text-primary)]">Legal</h4>
              <ul className="space-y-2">
                <li><Link href="/privacy" className="text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]">Privacy</Link></li>
                <li><Link href="/terms" className="text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]">Terms</Link></li>
                <li><Link href="/security" className="text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]">Security</Link></li>
              </ul>
            </div>
          </div>
          <div className="mt-12 flex flex-col items-center justify-between gap-4 border-t border-[var(--color-border)] pt-8 md:flex-row">
            <p className="text-sm text-[var(--color-text-secondary)]">
              © 2026 NasdaqPulse. All rights reserved.
            </p>
            <div className="flex items-center gap-4">
              <a href="#" className="text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]">
                <span className="sr-only">Twitter</span>
                <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24"><path d="M8.29 20.251c7.547 0 11.675-6.253 11.675-11.675 0-.178 0-.355-.012-.53A8.348 8.348 0 0022 5.92a8.19 8.19 0 01-2.357.646 4.118 4.118 0 001.804-2.27 8.224 8.224 0 01-2.605.996 4.107 4.107 0 00-6.993 3.743 11.65 11.65 0 01-8.457-4.287 4.106 4.106 0 001.27 5.477A4.072 4.072 0 012.8 9.713v.052a4.105 4.105 0 003.292 4.022 4.095 4.095 0 01-1.853.07 4.108 4.108 0 003.834 2.85A8.233 8.233 0 012 18.407a11.616 11.616 0 006.29 1.84" /></svg>
              </a>
              <a href="#" className="text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]">
                <span className="sr-only">GitHub</span>
                <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24"><path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" /></svg>
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
