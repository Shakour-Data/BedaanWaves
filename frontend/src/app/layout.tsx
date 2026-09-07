import type { Metadata } from "next";
import { UXProviders } from "@/providers/UXProviders";
import { ReactQueryProvider } from "@/providers/ReactQueryProvider";
import { ErrorBoundary } from "@/components/ux/ErrorBoundary";
import "./globals.css";

export const metadata: Metadata = {
  title: "BedaanWaves | Market Analysis Platform",
  description:
    "Comprehensive market analysis platform with real-time data, technical analysis, and fundamentals.",
  openGraph: {
    title: "BedaanWaves | Market Analysis Platform",
    description:
      "Comprehensive market analysis platform with real-time data, technical analysis, and fundamentals.",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "BedaanWaves | Market Analysis Platform",
    description:
      "Comprehensive market analysis platform with real-time data, technical analysis, and fundamentals.",
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
        <ReactQueryProvider>
          <ErrorBoundary>
            <UXProviders>{children}</UXProviders>
          </ErrorBoundary>
        </ReactQueryProvider>
      </body>
    </html>
  );
}
