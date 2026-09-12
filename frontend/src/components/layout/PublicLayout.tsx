"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/cn";
import { useAppStore } from "@/store/useAppStore";
import { NewSidebar } from "@/components/layout/NewSidebar";

const navLinks = [
  { href: "/", label: "Home" },
  { href: "/about", label: "About" },
  { href: "/services", label: "Services" },
  { href: "/blog", label: "Blog" },
  { href: "/contact", label: "Contact" },
];

export function PublicLayout({ children }: { children: React.ReactNode }) {
  const [scrolled, setScrolled] = useState(false);
  const pathname = usePathname();
  const sidebarOpen = useAppStore((state) => state.sidebarOpen);
  const setSidebarOpen = useAppStore((state) => state.setSidebarOpen);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <div className="flex min-h-screen flex-col bg-[var(--color-background)]">
      <NewSidebar />

      <header
        className={cn(
          "fixed top-0 left-0 right-0 z-30 h-16 shrink-0 transition-all duration-300 lg:left-64",
          scrolled
            ? "glass-strong shadow-md border-b border-[var(--color-border)]"
            : "bg-transparent"
        )}
      >
        <div className="container-grid">
          <div className="flex h-full items-center justify-between">
            <Link href="/" className="flex items-center gap-3 group">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[var(--color-primary)] shadow-lg shadow-[var(--color-primary)]/25 transition-transform group-hover:scale-105">
                <span className="text-white font-bold text-lg">B</span>
              </div>
              <div className="flex flex-col">
                <span className="text-lg font-bold text-[var(--color-text-primary)] leading-tight tracking-tight">
                  BedaanWaves
                </span>
                <span className="text-[10px] font-medium text-[var(--color-text-muted)] uppercase tracking-widest leading-tight">
                  Analytics
                </span>
              </div>
            </Link>

            <nav className="hidden md:flex items-center gap-1">
              {navLinks.map((link) => {
                const isActive = pathname === link.href || (link.href !== "/" && pathname.startsWith(link.href));
                return (
                  <Link
                    key={link.href}
                    href={link.href}
                    className={cn(
                      "relative px-4 py-2 text-sm font-medium transition-colors rounded-lg",
                      isActive
                        ? "text-[var(--color-primary)]"
                        : "text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-muted)]"
                    )}
                  >
                    {link.label}
                    {isActive && (
                      <span className="absolute bottom-0 left-4 right-4 h-0.5 rounded-full bg-[var(--color-primary)]" />
                    )}
                  </Link>
                );
              })}
            </nav>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className={cn(
                  "flex items-center justify-center h-11 w-11 rounded-lg text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-muted)] transition-colors md:hidden",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-primary)]/30"
                )}
                aria-label={sidebarOpen ? "Close sidebar" : "Open sidebar"}
                aria-expanded={sidebarOpen}
              >
                {sidebarOpen ? (
                  <span className="text-xl font-mono">&times;</span>
                ) : (
                  <span className="text-xl font-mono">&#9776;</span>
                )}
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="flex-1 pt-16 lg:ml-64">
        {children}
      </main>

      <footer className="border-t border-[var(--color-border)] bg-[var(--color-surface)]">
        <div className="container-grid py-16">
          <div className="grid gap-12 md:grid-cols-2 lg:grid-cols-5">
            <div className="lg:col-span-2">
              <Link href="/" className="flex items-center gap-3 mb-4">
                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[var(--color-primary)]">
                  <span className="text-white font-bold text-lg">B</span>
                </div>
                <span className="text-lg font-bold text-[var(--color-text-primary)]">
                  BedaanWaves
                </span>
              </Link>
              <p className="text-sm text-[var(--color-text-secondary)] max-w-sm leading-relaxed">
                Professional-grade market analysis platform with AI-powered scoring,
                real-time data, and advanced technical analysis for informed decisions.
              </p>
              <div className="mt-6 flex items-center gap-4">
                <div className="flex items-center gap-2 text-xs text-[var(--color-text-muted)]">
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[var(--color-success)] opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-[var(--color-success)]"></span>
                  </span>
                  All systems operational
                </div>
              </div>
            </div>
            <div>
              <h4 className="mb-4 text-sm font-semibold text-[var(--color-text-primary)] uppercase tracking-wider">
                Product
              </h4>
              <ul className="space-y-3">
                {[
                  { label: "Features", href: "/services" },
                  { label: "Leaderboard", href: "/leaderboard" },
                  { label: "Markets", href: "/stocks" },
                  { label: "Pricing", href: "/services#pricing" },
                ].map((item) => (
                  <li key={item.label}>
                    <Link
                      href={item.href}
                      className="text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-primary)] transition-colors"
                    >
                      {item.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h4 className="mb-4 text-sm font-semibold text-[var(--color-text-primary)] uppercase tracking-wider">
                Company
              </h4>
              <ul className="space-y-3">
                {["About Us", "Blog", "Contact"].map((item) => (
                  <li key={item}>
                    <Link
                      href={item === "About Us" ? "/about" : item === "Blog" ? "/blog" : "/contact"}
                      className="text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-primary)] transition-colors"
                    >
                      {item}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h4 className="mb-4 text-sm font-semibold text-[var(--color-text-primary)] uppercase tracking-wider">
                Legal
              </h4>
              <ul className="space-y-3">
                {[
                  { label: "Privacy Policy", href: "/legal/privacy" },
                  { label: "Terms of Service", href: "/legal/terms" },
                  { label: "Security", href: "/legal/security" },
                  { label: "Cookies", href: "/legal/cookies" },
                ].map((item) => (
                  <li key={item.label}>
                    <Link
                      href={item.href}
                      className="text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-primary)] transition-colors"
                    >
                      {item.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          </div>
          <div className="mt-16 flex flex-col items-center justify-between gap-4 border-t border-[var(--color-border)] pt-8 md:flex-row">
            <p className="text-sm text-[var(--color-text-muted)]">
              &copy; 2026 BedaanWaves. All rights reserved.
            </p>
            <div className="flex items-center gap-6">
              <span className="text-sm text-[var(--color-text-muted)]">
                Made with precision for traders worldwide.
              </span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
