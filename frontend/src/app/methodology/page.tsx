"use client";

import { DashboardShell } from "@/components/layout/DashboardShell";
import { TarotCard } from "@/components/ui/TarotCard";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import Link from "next/link";
import { useState } from "react";

import { t } from "@/lib/i18n";
import { useAuthStore } from "@/store/useAuthStore";

export default function MethodologyPage() {
  const { currentLang } = useAuthStore();
  const [activeMethod, setActiveMethod] = useState("scoring");

  const analysisMethods = [
    {
      id: "scoring",
      title: t("app.methodology.methods.scoring.title", currentLang),
      icon: "💯",
      description: t("app.methodology.methods.scoring.desc", currentLang),
      steps: t("app.methodology.methods.scoring.steps", currentLang) as unknown as string[],
      details: t("app.methodology.methods.scoring.details", currentLang),
      apiEndpoints: ["/analysis/scoring", "/analysis/scoring/rank"]
    },
    {
      id: "ranking",
      title: t("app.methodology.methods.ranking.title", currentLang),
      icon: "🏆",
      description: t("app.methodology.methods.ranking.desc", currentLang),
      steps: t("app.methodology.methods.ranking.steps", currentLang) as unknown as string[],
      details: t("app.methodology.methods.ranking.details", currentLang),
      apiEndpoints: ["/analysis/scoring/rank"]
    },
    {
      id: "technical",
      title: t("app.methodology.methods.technical.title", currentLang),
      icon: "📈",
      description: t("app.methodology.methods.technical.desc", currentLang),
      steps: t("app.methodology.methods.technical.steps", currentLang) as unknown as string[],
      details: t("app.methodology.methods.technical.details", currentLang),
      apiEndpoints: ["/analysis/technical/{symbol}"]
    },
    {
      id: "fundamental",
      title: t("app.methodology.methods.fundamental.title", currentLang),
      icon: "🏦",
      description: t("app.methodology.methods.fundamental.desc", currentLang),
      steps: t("app.methodology.methods.fundamental.steps", currentLang) as unknown as string[],
      details: t("app.methodology.methods.fundamental.details", currentLang),
      apiEndpoints: ["/analysis/fundamental/{symbol}"]
    },
    {
      id: "momentum",
      title: t("app.methodology.methods.momentum.title", currentLang),
      icon: "🚀",
      description: t("app.methodology.methods.momentum.desc", currentLang),
      steps: t("app.methodology.methods.momentum.steps", currentLang) as unknown as string[],
      details: t("app.methodology.methods.momentum.details", currentLang),
      apiEndpoints: ["/analysis/momentum/{symbol}"]
    },
    {
      id: "risk",
      title: t("app.methodology.methods.risk.title", currentLang),
      icon: "🛡️",
      description: t("app.methodology.methods.risk.desc", currentLang),
      steps: t("app.methodology.methods.risk.steps", currentLang) as unknown as string[],
      details: t("app.methodology.methods.risk.details", currentLang),
      apiEndpoints: ["/analysis/risk/{symbol}", "/analysis/volatility/{symbol}"]
    },
    {
      id: "sentiment",
      title: t("app.methodology.methods.sentiment.title", currentLang),
      icon: "🎭",
      description: t("app.methodology.methods.sentiment.desc", currentLang),
      steps: t("app.methodology.methods.sentiment.steps", currentLang) as unknown as string[],
      details: t("app.methodology.methods.sentiment.details", currentLang),
      apiEndpoints: ["/analysis/sentiment/{symbol}"]
    },
    {
      id: "ai",
      title: t("app.methodology.methods.ai.title", currentLang),
      icon: "🤖",
      description: t("app.methodology.methods.ai.desc", currentLang),
      steps: t("app.methodology.methods.ai.steps", currentLang) as unknown as string[],
      details: t("app.methodology.methods.ai.details", currentLang),
      apiEndpoints: ["/analysis/prediction/{symbol}"]
    }
  ];

  return (
    <DashboardShell title={t("app.methodology.title", currentLang)}>
      <div className="flex flex-col gap-6">
        {/* Header */}
        <TarotCard icon="📘" title={t("app.methodology.overview", currentLang)}>
          <p className="text-muted-foreground text-justify leading-relaxed">
            {t("app.methodology.desc", currentLang)}
          </p>
        </TarotCard>

        {/* Method Tabs */}
        <div className="flex gap-2 flex-wrap pb-2">
          {analysisMethods.map((method) => (
            <button
              key={method.id}
              onClick={() => setActiveMethod(method.id)}
              className={`px-4 py-2 rounded-full text-sm font-bold transition-all duration-300 whitespace-nowrap flex items-center gap-2 ${
                activeMethod === method.id
                  ? "bg-secondary text-white shadow-md transform scale-105"
                  : "bg-neutral text-muted-foreground hover:bg-neutral/80"
              }`}
            >
              <span>{method.icon}</span>
              {method.title}
            </button>
          ))}
        </div>

        {/* Active Method Content */}
        {analysisMethods.map((method) => (
          activeMethod === method.id && (
            <TarotCard key={method.id} icon={method.icon} title={method.title} className="animate-in fade-in slide-in-from-bottom-4 duration-500">
              <div className="space-y-6">
                <p className="text-foreground font-medium leading-relaxed border-r-4 border-secondary pr-4">{method.description}</p>

                {/* Steps */}
                <div className="bg-neutral/30 p-4 rounded-xl border border-border/40">
                  <h4 className="font-bold text-secondary mb-3 flex items-center gap-2">
                    <span>📝</span>
                    {t("app.methodology.process_steps", currentLang)}
                  </h4>
                  <ol className="list-decimal list-inside space-y-2 text-sm text-muted-foreground">
                    {Array.isArray(method.steps) && method.steps.map((step, i) => (
                      <li key={i} className="hover:text-foreground transition-colors">{step}</li>
                    ))}
                  </ol>
                </div>

                {/* Details */}
                <div>
                  <h4 className="font-bold text-secondary mb-2 flex items-center gap-2">
                    <span>🔍</span>
                    {t("app.methodology.technical_details", currentLang)}
                  </h4>
                  <p className="text-sm text-muted-foreground leading-relaxed">{method.details}</p>
                </div>

                {/* API Endpoints */}
                {method.apiEndpoints && (
                  <div className="bg-neutral/50 p-4 rounded-xl border border-border/20">
                    <h4 className="font-bold text-secondary mb-3 flex items-center gap-2">
                      <span>🔗</span>
                      {t("app.methodology.api_endpoints", currentLang)}
                    </h4>
                    <ul className="space-y-1 text-xs font-mono bg-background/50 p-2 rounded-lg">
                      {method.apiEndpoints.map((endpoint, i) => (
                        <li key={i} className="text-muted-foreground truncate" dir="ltr text-left">
                          <span className="text-secondary mr-2">GET</span>
                          {endpoint}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </TarotCard>
          )
        ))}

        {/* Secondary Information */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Capabilities */}
          <TarotCard icon="🚀" title={t("app.methodology.key_capabilities", currentLang)}>
            <ul className="space-y-2 text-sm">
              <li className="flex items-center gap-2">
                <span className="text-green-500">✅</span>
                <span>{t("app.methodology.coverage", currentLang)}</span>
              </li>
              <li className="flex items-center gap-2">
                <span className="text-green-500">✅</span>
                <span>{t("app.methodology.realtime", currentLang)}</span>
              </li>
              <li className="flex items-center gap-2">
                <span className="text-green-500">✅</span>
                <span>{t("app.methodology.ml_optimized", currentLang)}</span>
              </li>
              <li className="flex items-center gap-2">
                <span className="text-green-500">✅</span>
                <span>{t("app.methodology.customizable", currentLang)}</span>
              </li>
            </ul>
          </TarotCard>

          {/* Disclaimers */}
          <TarotCard icon="⚠️" title={t("app.methodology.important_notes", currentLang)}>
            <div className="space-y-3 text-sm">
              <div>
                <h5 className="font-medium mb-1">{t("app.methodology.disclaimer_title", currentLang)}</h5>
                <p className="text-muted-foreground">{t("app.methodology.disclaimer_desc", currentLang)}</p>
              </div>
              <div>
                <h5 className="font-medium mb-1">{t("app.methodology.accuracy_title", currentLang)}</h5>
                <p className="text-muted-foreground">{t("app.methodology.accuracy_desc", currentLang)}</p>
              </div>
            </div>
          </TarotCard>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col md:flex-row gap-3">
          <Link href="/scoring">
            <PrimaryButton className="w-full cursor-pointer">{t("app.methodology.explore_scoring", currentLang)}</PrimaryButton>
          </Link>
          <Link href="/analysis">
            <PrimaryButton className="w-full cursor-pointer">{t("app.methodology.run_analysis", currentLang)}</PrimaryButton>
          </Link>
        </div>
      </div>
    </DashboardShell>
  );
}
