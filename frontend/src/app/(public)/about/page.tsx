import { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "About Us | BedaanWaves",
  description: "Learn about BedaanWaves — our mission, team, and commitment to empowering traders with advanced market analysis.",
};

const values = [
  {
    title: "Precision",
    description:
      "We deliver accurate, real-time market data and analytics to help traders make informed decisions.",
  },
  {
    title: "Innovation",
    description:
      "Our platform leverages cutting-edge AI and machine learning to provide predictive market insights.",
  },
  {
    title: "Transparency",
    description:
      "We believe in clear, honest communication with our users about market conditions and platform capabilities.",
  },
  {
    title: "Security",
    description:
      "Bank-level encryption and security protocols protect your data and trading strategies.",
  },
];

const team = [
  {
    name: "Alex Chen",
    role: "Founder & CEO",
    bio: "Former quantitative analyst with 15+ years in financial technology.",
  },
  {
    name: "Sarah Johnson",
    role: "CTO",
    bio: "AI researcher and full-stack engineer specializing in real-time data systems.",
  },
  {
    name: "Michael Park",
    role: "Head of Product",
    bio: "Product leader focused on building intuitive trading experiences.",
  },
  {
    name: "Emily Davis",
    role: "Lead Data Scientist",
    bio: "PhD in Machine Learning with expertise in time-series forecasting.",
  },
];

export default function AboutPage() {
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
              About <span className="text-[var(--color-primary)]">BedaanWaves</span>
            </h1>
            <p className="mt-6 text-lg text-[var(--color-text-secondary)]">
              We are a team of traders, engineers, and data scientists dedicated to democratizing professional-grade market analysis. Our mission is to empower every trader — from beginners to professionals — with the tools and insights they need to succeed in today&apos;s complex markets.
            </p>
          </div>
        </div>
      </section>

      {/* Values */}
      <section className="py-16 border-t border-[var(--color-border)]">
        <div className="container-grid">
          <h2 className="text-3xl font-bold text-[var(--color-text-primary)] mb-12">
            Our Values
          </h2>
          <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-4">
            {values.map((value, index) => (
              <div
                key={index}
                className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm transition-all hover:border-[var(--color-primary)]/50 hover:shadow-lg"
              >
                <div className="mb-4 inline-flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--color-primary)]/10 text-[var(--color-primary)]">
                  <span className="font-bold">{index + 1}</span>
                </div>
                <h3 className="text-lg font-semibold text-[var(--color-text-primary)]">
                  {value.title}
                </h3>
                <p className="mt-2 text-sm text-[var(--color-text-secondary)]">
                  {value.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Team */}
      <section className="py-16 border-t border-[var(--color-border)]">
        <div className="container-grid">
          <h2 className="text-3xl font-bold text-[var(--color-text-primary)] mb-12">
            Meet the Team
          </h2>
          <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
            {team.map((member, index) => (
              <div
                key={index}
                className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm transition-all hover:border-[var(--color-primary)]/50 hover:shadow-lg"
              >
                <div className="flex h-16 w-16 items-center justify-center rounded-full bg-[var(--color-primary)]/10 text-xl font-bold text-[var(--color-primary)] mb-4">
                  {member.name.split(" ").map((n) => n[0]).join("")}
                </div>
                <h3 className="text-lg font-semibold text-[var(--color-text-primary)]">
                  {member.name}
                </h3>
                <p className="text-sm text-[var(--color-primary)] font-medium mb-2">
                  {member.role}
                </p>
                <p className="text-sm text-[var(--color-text-secondary)]">
                  {member.bio}
                </p>
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
              Ready to Start Trading Smarter?
            </h2>
            <p className="mx-auto mt-4 max-w-2xl text-lg text-white/80">
              Join thousands of traders who use BedaanWaves for professional-grade analysis and AI-powered insights.
            </p>
            <div className="mt-8 flex flex-col items-center justify-center gap-4 sm:flex-row">
              <Link
                href="/register"
                className="inline-flex items-center gap-2 rounded-md bg-white px-8 py-4 text-base font-semibold text-[var(--color-primary)] transition-all hover:bg-gray-100"
              >
                Start Free Trial
                <span className="text-xl">→</span>
              </Link>
              <Link
                href="/contact"
                className="inline-flex items-center gap-2 rounded-md border-2 border-white px-8 py-4 text-base font-semibold text-white transition-all hover:bg-white/10"
              >
                Contact Us
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
