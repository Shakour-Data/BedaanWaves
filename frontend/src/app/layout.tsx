import type { Metadata } from "next";
import type { ReactNode } from "react";
import { cookies } from "next/headers";
import "./globals.css";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { AuthGate } from "@/components/layout/AuthGate";

export const metadata: Metadata = {
  title: "BedaanWaves | Market Analysis Platform",
  description:
    "Comprehensive market analysis platform with real-time data, technical analysis, fundamentals, and AI signals.",
  openGraph: {
    title: "BedaanWaves | Market Analysis Platform",
    description: "Comprehensive market analysis platform with real-time data, technical analysis, fundamentals, and AI signals.",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "BedaanWaves | Market Analysis Platform",
    description: "Comprehensive market analysis platform with real-time data, technical analysis, fundamentals, and AI signals.",
  },
};

function PublicNav() {
  return (
    <header className="sticky top-0 z-30 flex items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-2">
      <a href="/" className="text-lg font-bold text-foreground">
        BedaanWaves
      </a>
      <nav className="flex items-center gap-4 text-sm">
        <a href="/login" className="text-secondary hover:underline">
          Login
        </a>
        <a href="/register" className="text-secondary hover:underline">
          Register
        </a>
        <LanguageSwitcher />
      </nav>
    </header>
  );
}

export default async function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const cookieStore = await cookies();
  const locale = cookieStore.get("locale")?.value || "en";
  const dir = locale === "fa" ? "rtl" : "ltr";

  return (
    <html lang={locale} dir={dir} data-scroll-behavior="smooth">
      <body>
        <AuthGate
          authenticatedContent={children}
          unauthenticatedNav={<PublicNav />}
        />
      </body>
    </html>
  );
}
