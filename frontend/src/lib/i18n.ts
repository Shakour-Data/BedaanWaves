import { useAuthStore } from "@/store/useAuthStore";
import en from "@/i18n/en.json";

export type Lang = "en" | "fa";

const dictionaries: Record<string, Record<string, unknown>> = { en };

function lookup(dict: unknown, key: string): string | undefined {
  const parts = key.split(".");
  let current: unknown = dict;
  for (const part of parts) {
    if (current && typeof current === "object" && part in (current as Record<string, unknown>)) {
      current = (current as Record<string, unknown>)[part];
    } else {
      return undefined;
    }
  }
  return typeof current === "string" ? current : undefined;
}

export function t(key: string, lang?: Lang): string {
  const language = lang ?? useAuthStore.getState().currentLang ?? "en";
  const dict = dictionaries[language] ?? dictionaries.en;
  return lookup(dict, key) ?? lookup(dictionaries.en, key) ?? key;
}

export default t;
