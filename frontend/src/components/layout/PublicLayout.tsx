"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTheme } from "@/providers/ThemeProvider";
import { cn } from "@/lib/cn";
import { useAuthStore } from "@/store/useAuthStore";

interface PublicLayoutProps {
  children: React.ReactNode;
}

const publicNavItems = [
  { label: "Home", href: "/" },
  { label: "About", href: "/about" },
  { label: "Services", href: "/services" },
  { label: "Blog", href: "/blog" },
  { label: "Contact", href: "/contact" },
];

export function PublicLayout({ children }: PublicLayoutProps) {
  const pathname = usePathname();
  const { theme, toggleTheme } = useTheme();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  return (
    <div className="flex min-h-screen flex-col bg-[var(--color-background)]">
      {/* Header / Navbar */}
      <header className="sticky top-0 z-30 border-b border-[var(--color-border)] bg-[var(--color-surface)]/80 backdrop-blur-xl">
        <div className="container-grid flex h-16 items-center justify-between">
          <div className="flex items-center gap-8">
            <Link href="/" className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--color-primary)] text-white">
                <span className="font-bold text-sm">B</span>
              </div>
              <span className="text-lg font-bold text-[var(--color-text-primary)]">
                BedaanWaves
              </span>
            </Link>
            <nav className="hidden items-center gap-6 md:flex">
              {publicNavItems.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "text-sm font-medium transition-colors",
                    pathname === item.href
                      ? "text-[var(--color-primary)]"
                      : "text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]"
                  )}
                >
                  {item.label}
                </Link>
              ))}
            </nav>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={toggleTheme}
              className="flex h-9 w-9 items-center justify-center rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] text-[var(--color-text-secondary)] transition-colors hover:border-[var(--color-primary)] hover:text-[var(--color-primary)]"
              aria-label="Toggle theme"
            >
              {theme === "dark" ? "☀️" : "🌙"}
            </button>
            {isAuthenticated ? (
              <Link
                href="/dashboard"
                className="hidden rounded-lg bg-[var(--color-primary)] px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-[var(--color-primary-hover)] sm:block"
              >
                Dashboard
              </Link>
            ) : (
              <Link
                href="/login"
                className="hidden rounded-lg bg-[var(--color-primary)] px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-[var(--color-primary-hover)] sm:block"
              >
                Sign In
              </Link>
            )}
          </div>
        </div>
      </header>

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
