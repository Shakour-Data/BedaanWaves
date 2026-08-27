"use client";

import Link from "next/link";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { t } from "@/lib/i18n";
import { useAuthStore } from "@/store/useAuthStore";

export default function HomePage() {
  const { currentLang } = useAuthStore();

  const features = [
    {
      title: t("app.home.features.market_data.title", currentLang),
      desc: t("app.home.features.market_data.desc", currentLang),
    },
    {
      title: t("app.home.features.fundamental.title", currentLang),
      desc: t("app.home.features.fundamental.desc", currentLang),
    },
    {
      title: t("app.home.features.ai.title", currentLang),
      desc: t("app.home.features.ai.desc", currentLang),
    },
  ];

  return (
    <main className="min-h-screen">
      <section className="px-4 pt-10 pb-6">
        <h1 className="text-center text-4xl font-bold text-gray-800 mb-4">
          {t("app.home.hero_title", currentLang)}
        </h1>
        <p className="text-center text-gray-600 text-lg mb-12 max-w-2xl mx-auto">
          {t("app.home.hero_desc", currentLang)}
        </p>
      </section>

      <section className="px-4 pb-12">
        <h2 className="text-2xl font-semibold text-gray-800 mb-6 text-center">
          {t("app.home.features_title", currentLang)}
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-6xl mx-auto">
          {features.map((item) => (
            <div
              key={item.title}
              className="bg-white rounded-xl shadow-md p-6 border border-gray-200"
            >
              <h3 className="text-xl font-semibold text-blue-700 mb-2">
                {item.title}
              </h3>
              <p className="text-gray-600 text-sm">{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="px-4 pb-12 text-center">
        <div className="flex flex-col items-center gap-4">
          <Link href="/stocks">
            <PrimaryButton>{t("app.home.view_stocks", currentLang)}</PrimaryButton>
          </Link>
          <p className="text-gray-400 text-sm">
            Backend running on port 3000 | Frontend on port 3005
          </p>
        </div>
      </section>
    </main>
  );
}
