import type { Metadata } from "next";
import { UXProviders } from "@/providers/UXProviders";
import "./globals.css";

export const metadata: Metadata = {
  title: "BedaanWaves | Market Analysis Platform",
  description:
    "Comprehensive market analysis platform with real-time data, technical analysis, fundamentals, and AI signals.",
  openGraph: {
    title: "BedaanWaves | Market Analysis Platform",
    description:
      "Comprehensive market analysis platform with real-time data, technical analysis, fundamentals, and AI signals.",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "BedaanWaves | Market Analysis Platform",
    description:
      "Comprehensive market analysis platform with real-time data, technical analysis, fundamentals, and AI signals.",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" dir="ltr" data-scroll-behavior="smooth">
      <body>
        <UXProviders>{children}</UXProviders>
      </body>
    </html>
  );
}
