"use client";

import Link from "next/link";

interface PublicLayoutProps {
  children: React.ReactNode;
}

export function PublicLayout({ children }: PublicLayoutProps) {

  return (
    <div className="flex min-h-screen flex-col bg-[var(--color-background)]">
      {/* Main Content */}
      <main className="flex-1">
        <div className="container-grid py-8">{children}</div>
      </main>

      {/* Footer */}
      <footer className="border-t border-[var(--color-border)] bg-[var(--color-surface)]">
        <div className="container-grid py-12">
          <div className="grid gap-8 md:grid-cols-4">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--color-primary)]">
                  <span className="text-white font-bold text-sm">B</span>
                </div>
                <span className="text-lg font-bold text-[var(--color-text-primary)]">
                  BedaanWaves
                </span>
              </div>
              <p className="text-sm text-[var(--color-text-secondary)]">
                Comprehensive market analysis platform with real-time data, technical analysis, fundamentals, and AI signals.
              </p>
            </div>
            <div>
              <h4 className="mb-4 text-sm font-semibold text-[var(--color-text-primary)]">
                Product
              </h4>
              <ul className="space-y-2">
                <li>
                  <Link href="/services" className="text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]">
                    Features
                  </Link>
                </li>
                <li>
                  <Link href="/dashboard" className="text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]">
                    Dashboard
                  </Link>
                </li>
                <li>
                  <Link href="/stocks" className="text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]">
                    Markets
                  </Link>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="mb-4 text-sm font-semibold text-[var(--color-text-primary)]">
                Company
              </h4>
              <ul className="space-y-2">
                <li>
                  <Link href="/about" className="text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]">
                    About Us
                  </Link>
                </li>
                <li>
                  <Link href="/blog" className="text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]">
                    Blog
                  </Link>
                </li>
                <li>
                  <Link href="/contact" className="text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]">
                    Contact
                  </Link>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="mb-4 text-sm font-semibold text-[var(--color-text-primary)]">
                Legal
              </h4>
              <ul className="space-y-2">
                <li>
                  <span className="text-sm text-[var(--color-text-secondary)]">
                    Privacy Policy
                  </span>
                </li>
                <li>
                  <span className="text-sm text-[var(--color-text-secondary)]">
                    Terms of Service
                  </span>
                </li>
                <li>
                  <span className="text-sm text-[var(--color-text-secondary)]">
                    Security
                  </span>
                </li>
              </ul>
            </div>
          </div>
          <div className="mt-12 flex flex-col items-center justify-between gap-4 border-t border-[var(--color-border)] pt-8 md:flex-row">
            <p className="text-sm text-[var(--color-text-secondary)]">
              © 2026 BedaanWaves. All rights reserved.
            </p>
            <div className="flex items-center gap-4">
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
