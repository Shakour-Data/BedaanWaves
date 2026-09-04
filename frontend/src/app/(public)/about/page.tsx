import { Metadata } from "next";
import Link from "next/link";
import { PublicLayout } from "@/components/layout/PublicLayout";
import { ArrowRight, Target, Lightbulb, Lock, Globe } from "lucide-react";

export const metadata: Metadata = {
  title: "About Us | BedaanWaves",
  description: "Learn about BedaanWaves — our mission, team, and commitment to empowering traders with advanced market analysis.",
};

const values = [
  {
    title: "Precision",
    description: "We deliver accurate, real-time market data and analytics to help traders make informed decisions.",
    icon: Target,
  },
  {
    title: "Innovation",
    description: "Our platform leverages cutting-edge AI and machine learning to provide predictive market insights.",
    icon: Lightbulb,
  },
  {
    title: "Transparency",
    description: "We believe in clear, honest communication with our users about market conditions and platform capabilities.",
    icon: Globe,
  },
  {
    title: "Security",
    description: "Bank-level encryption and security protocols protect your data and trading strategies.",
    icon: Lock,
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
                <span className="text-sm font-medium text-[var(--color-primary)]">Our Story</span>
              </div>
              <h1 className="text-4xl font-bold tracking-tight text-[var(--color-text-primary)] sm:text-5xl lg:text-6xl text-balance">
                About <span className="bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-accent)] bg-clip-text text-transparent">BedaanWaves</span>
              </h1>
              <p className="mt-8 text-lg text-[var(--color-text-secondary)] leading-relaxed max-w-2xl">
                We are a team of traders, engineers, and data scientists dedicated to democratizing professional-grade market analysis. Our mission is to empower every trader — from beginners to professionals — with the tools and insights they need to succeed in today&apos;s complex markets.
              </p>
            </div>
          </div>
        </section>

        {/* Values */}
        <section className="py-20 border-t border-[var(--color-border)]">
          <div className="container-grid">
            <div className="text-center mb-16">
              <h2 className="text-3xl font-bold text-[var(--color-text-primary)] sm:text-4xl text-balance">
                Our <span className="bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-accent)] bg-clip-text text-transparent">Values</span>
              </h2>
              <p className="mt-4 text-lg text-[var(--color-text-secondary)] max-w-2xl mx-auto">
                The principles that guide everything we build
              </p>
            </div>
            <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-4">
              {values.map((value, index) => {
                const Icon = value.icon;
                return (
                  <div
                    key={index}
                    className="group rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm transition-all hover:border-[var(--color-primary)]/50 hover:shadow-lg hover:-translate-y-1"
                  >
                    <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-xl bg-[var(--color-primary-soft)] text-[var(--color-primary)] group-hover:bg-gradient-to-br group-hover:from-[var(--color-primary)] group-hover:to-[var(--color-accent)] group-hover:text-white transition-all duration-300">
                      <Icon className="h-6 w-6" />
                    </div>
                    <h3 className="text-lg font-semibold text-[var(--color-text-primary)]">
                      {value.title}
                    </h3>
                    <p className="mt-2 text-sm text-[var(--color-text-secondary)] leading-relaxed">
                      {value.description}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        {/* Team */}
        <section className="py-20 border-t border-[var(--color-border)]">
          <div className="container-grid">
            <div className="text-center mb-16">
              <h2 className="text-3xl font-bold text-[var(--color-text-primary)] sm:text-4xl text-balance">
                Meet the <span className="bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-accent)] bg-clip-text text-transparent">Team</span>
              </h2>
              <p className="mt-4 text-lg text-[var(--color-text-secondary)] max-w-2xl mx-auto">
                The experts behind BedaanWaves
              </p>
            </div>
            <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
              {team.map((member, index) => (
                <div
                  key={index}
                  className="group rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm transition-all hover:border-[var(--color-primary)]/50 hover:shadow-lg hover:-translate-y-1 text-center"
                >
                  <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-accent)] text-2xl font-bold text-white mb-4 shadow-lg group-hover:shadow-xl transition-all group-hover:scale-105">
                    {member.name.split(" ").map((n) => n[0]).join("")}
                  </div>
                  <h3 className="text-lg font-semibold text-[var(--color-text-primary)]">
                    {member.name}
                  </h3>
                  <p className="text-sm text-[var(--color-primary)] font-medium mb-2">
                    {member.role}
                  </p>
                  <p className="text-sm text-[var(--color-text-secondary)] leading-relaxed">
                    {member.bio}
                  </p>
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
                <h2 className="text-3xl font-bold text-white sm:text-4xl lg:text-5xl text-balance">
                  Ready to Start Trading Smarter?
                </h2>
                <p className="mx-auto mt-6 max-w-2xl text-lg text-white/90">
                  Join thousands of traders who use BedaanWaves for professional-grade analysis and AI-powered insights.
                </p>
                <div className="mt-8 flex flex-col items-center justify-center gap-4 sm:flex-row">
                  <Link
                    href="/register"
                    className="inline-flex items-center gap-2 rounded-xl bg-white px-8 py-4 text-base font-semibold text-[var(--color-primary)] shadow-lg transition-all hover:bg-gray-100 hover:shadow-xl hover:-translate-y-0.5"
                  >
                    Start Free Trial
                    <ArrowRight className="h-4 w-4" />
                  </Link>
                  <Link
                    href="/contact"
                    className="inline-flex items-center gap-2 rounded-xl border-2 border-white px-8 py-4 text-base font-semibold text-white transition-all hover:bg-white/10 hover:shadow-lg"
                  >
                    Contact Us
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
