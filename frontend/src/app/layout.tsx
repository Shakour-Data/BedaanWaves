import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "BedaanWaves | معماری ارتعاشی بازار سرمایه",
  description:
    "محیطی ناخودآگاه برای تحلیل بازار سرمایه؛ جایی که هر پیکسل و هر حرکت، کاربر را به سمت اقدام هارمونیک هدایت می‌کند.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="fa" dir="rtl">
      <body>{children}</body>
    </html>
  );
}
