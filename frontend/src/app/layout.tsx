import type { Metadata } from "next";
import "./globals.css";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";

export const metadata: Metadata = {
  title: "BedaanWaves | پلتفرم تحلیل بازار سرمایه",
  description:
    "پلتفرم جامع تحلیل بازار سرمایه با دسترسی به داده‌های لحظه‌ای، تحلیل تکنیکال، فاندامنتال و هوش مصنوعی.",
  openGraph: {
    title: "BedaanWaves | پلتفرم تحلیل بازار سرمایه",
    description: "پلتفرم جامع تحلیل بازار سرمایه با دسترسی به داده‌های لحظه‌ای، تحلیل تکنیکال، فاندامنتال و هوش مصنوعی.",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "BedaanWaves | پلتفرم تحلیل بازار سرمایه",
    description: "پلتفرم جامع تحلیل بازار سرمایه با دسترسی به داده‌های لحظه‌ای، تحلیل تکنیکال، فاندامنتال و هوش مصنوعی.",
  },
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="fa" dir="rtl" data-scroll-behavior="smooth">
      <body>
        <LanguageSwitcher />
        {children}
      </body>
    </html>
  );
}
