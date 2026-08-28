import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";
import { AuthGate } from "@/components/layout/AuthGate";
import { t, type Lang } from "@/lib/i18n";
import { getServerLanguage } from "@/lib/i18n-server";

export const metadata: Metadata = {
  title: "BedaanWaves | Market Analysis Platform",
  description:
    "Comprehensive market analysis platform with real-time data, technical analysis, fundamentals, and AI signals.",
  openGraph: {
    title: "BedaanWaves | Market Analysis Platform",
    description: "Comprehensive market analysis platform with real-time data, technical analysis, fundamentals, and AI signals.",
    type: "website" },
  twitter: {
    card: "summary_large_image",
    title: "BedaanWaves | Market Analysis Platform",
    description: "Comprehensive market analysis platform with real-time data, technical analysis, fundamentals, and AI signals." } };

async function PublicNav() {
  const locale = (await getServerLanguage()) as Lang;
  return (
    <header className="sticky top-0 z-30 flex items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-2">
      <a href="/" className="text-lg font-bold text-foreground">
        {t("app.title", locale)}
      </a>
      <nav className="flex items-center gap-4 text-sm">
        <a href="/login" className="text-secondary hover:underline">
          {t("app.auth.login", locale)}
        </a>
        <a href="/register" className="text-secondary hover:underline">
          {t("app.auth.register", locale)}
        </a>
      </nav>
    </header>
  );
}

export default async function RootLayout({
  children }: Readonly<{ children: React.ReactNode }>) {
  const locale = (await getServerLanguage()) as Lang;

  return (
    <html lang={locale} dir="ltr" data-scroll-behavior="smooth">
      <body>
        <AuthGate
          authenticatedContent={children}
          unauthenticatedNav={<PublicNav />}
        />
      </body>
    </html>
  );
}
