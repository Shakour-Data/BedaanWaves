"use client";

import { useState, useEffect } from "react";
import { useAuthStore } from "@/store/useAuthStore";

export function LanguageSwitcher() {
  const currentLang = useAuthStore((s) => s.currentLang);
  const setLanguage = useAuthStore((s => s.setLanguage || (() => {})));

  const [open, setOpen] = useState(false);

  const languages = [
    { code: "en", label: "English", dir: "ltr" },
    { code: "fa", label: "فارسی", dir: "rtl" },
  ];

  const handleLanguageChange = (code: "en" | "fa") => {
    localStorage.setItem("lang", code);
    if (setLanguage) setLanguage(code);
    document.documentElement.lang = code;
    document.documentElement.dir = code === "fa" ? "rtl" : "ltr";
    // Reload to apply translations
    window.location.reload();
  };

  // Initialize HTML direction on mount
  useEffect(() => {
    document.documentElement.lang = currentLang;
    document.documentElement.dir = currentLang === "fa" ? "rtl" : "ltr";
  }, [currentLang]);

  return (
    <div className="relative inline-block text-left">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="inline-flex items-center justify-center rounded-lg border border-gray-300 bg-white px-3 py-1 text-sm font-medium shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 sm:menu-preview"
      >
        {currentLang === "fa" ? "فارسی" : "English"}
        <svg className="-mr-1 ml-1 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-32 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 focus:outline-none z-50">
          <div className="py-1" role="menu" aria-orientation="vertical" aria-labelledby="options-menu">
            {languages.map((lang) => (
              <button
                key={lang.code}
                onClick={() => handleLanguageChange(lang.code as "en" | "fa")}
                className="flex w-full items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-primary"
                className={currentLang === lang.code ? "bg-gray-100" : ""}
              >
                {lang.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}