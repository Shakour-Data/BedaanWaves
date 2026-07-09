import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { TarotCard } from "@/components/ui/TarotCard";

const pillars = [
  {
    icon: "🔥",
    title: "قدرت (Gevurah)",
    body: "تحلیل‌های پرقدرت و هشدارهای لحظه‌ای بر پایه‌ی ۶ بعد تحلیل.",
  },
  {
    icon: "💧",
    title: "مهربانی (Chesed)",
    body: "مسیری امن و شفاف برای درک بازار و تصمیم‌گیری آگاهانه.",
  },
  {
    icon: "🌿",
    title: "بنیاد (Yesod)",
    body: "زیربنایی پایدار از داده‌های بورس تهران تا دارایی‌های دیجیتال.",
  },
  {
    icon: "✨",
    title: "زیبایی (Tiferet)",
    body: "تجربه‌ای هارمونیک که کاربر را به سمت اقدام هدایت می‌کند.",
  },
];

export default function HomePage() {
  return (
    <main className="min-h-screen">
      {/* مسیر جادویی: تصویر بزرگ (آتش) → متن وعده (آب) → دکمه‌ی اقدام (خاک) */}
      <section className="flex min-h-screen flex-col items-center justify-start px-3 pt-5 text-center">
        <p className="text-secondary text-sm font-medium tracking-wide">
          معماری ارتعاشی بازار سرمایه
        </p>
        <h1
          className="mt-3 max-w-3xl font-bold"
          style={{ fontSize: "clamp(34px, 6vw, 89px)" }}
        >
          هر پیکسل، یک ارتعاش؛ هر حرکت، یک اقدام هارمونیک.
        </h1>
        <p
          className="mt-3 max-w-2xl text-muted-foreground"
          style={{ fontSize: "clamp(16px, 2.2vw, 21px)" }}
        >
          BedaanWaves میدانی یکپارچه برای تحلیل بازار سرمایه می‌سازد که در آن
          نظم ریاضی و اعداد مقدس، آرامش و قابلیت پیش‌بینی را در ناخودآگاه شما
          جاری می‌کند.
        </p>
        <div className="mt-3">
          <PrimaryButton>شروع سفر</PrimaryButton>
        </div>
      </section>

      {/* کارت‌های محتوا (Tarot Cards) - اصل روانشناسی یونگ */}
      <section className="mx-auto grid max-w-6xl grid-cols-1 gap-3 px-3 pb-5 sm:grid-cols-2 lg:grid-cols-4">
        {pillars.map((p) => (
          <TarotCard key={p.title} icon={p.icon} title={p.title}>
            <p className="text-muted-foreground text-sm">{p.body}</p>
          </TarotCard>
        ))}
      </section>
    </main>
  );
}
