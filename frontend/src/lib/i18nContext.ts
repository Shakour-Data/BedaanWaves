import { useState, useEffect, useContext } from 'react';

// Create a context for language
export const LanguageContext = {
  currentLang: 'en',
  setLanguage: (lang: string) => {},
};

// Initialize with localStorage value
export const initLanguage = () => {
  const savedLang = localStorage.getItem('lang');
  if (savedLang && ['en', 'fa'].includes(savedLang)) {
    return savedLang;
  }
  return 'en';
};