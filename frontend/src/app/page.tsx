import Link from "next/link";
import { PrimaryButton } from "@/components/ui/PrimaryButton";

const industries = [
  {
    name: "صنعت‌های فارماویی",
    desc: "تحلیل‌های پیشرفته و مدرن بیشتر با رویدادهای روزانه و کامل",
  },
  {
    name: "بازارهای تورمی",
    desc: "آمار تولید و پایش الگوهای رفتاری بازار",
  },
  {
    name: "پرونده‌های سودآور",
    desc: "تقسیم‌بندی سودها و درآمدهای اصلی روزانه",
  },
];

export default function HomePage() {
  return (
    <main className="min-h-screen">
      <section className="px-4 pt-10 pb-6">
        <h1 className="text-center text-4xl font-bold text-gray-800 mb-4">
          BedaanWaves پلتفرم تحلیل بازار سرمایه
        </h1>
        <p className="text-center text-gray-600 text-lg mb-12 max-w-2xl mx-auto">
          پلتفرم کاملاً ریاضی و دقیق برای تحلیل بازار سرمایه.
          با دسترسی به ۱۰ تایی بهترین ایده‌ها، آمار و تحلیل‌های استاندارد
          بازار.
        </p>
      </section>

      <section className="px-4 pb-12">
        <h2 className="text-2xl font-semibold text-gray-800 mb-6 text-center">
          پنل‌های اصلی
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-6xl mx-auto">
          {industries.map((item) => (
            <div
              key={item.name}
              className="bg-white rounded-xl shadow-md p-6 border border-gray-200"
            >
              <h3 className="text-xl font-semibold text-red-700 mb-2">
                {item.name}
              </h3>
              <p className="text-gray-600 text-sm">{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="px-4 pb-12 text-center">
        <div className="flex flex-col items-center gap-4">
          <Link href="/dashboard">
            <PrimaryButton>بیشتر دسترسی</PrimaryButton>
          </Link>
          <p className="text-gray-400 text-sm">
            سیستم پیش‌فرض: در حال اجرا
          </p>
        </div>
      </section>
    </main>
  );
}
