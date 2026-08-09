"use client";

import { useAuthStore } from "@/store/useAuthStore";

export async function apiFetch(url: string, options: RequestInit = {}) {
  const currentLang = useAuthStore.getState().currentLang;
 
  const headers = {
    "Content-Type": "application/json",
    ...options.headers,
  };
 
  const response = await fetch(url, {
    ...options,
    headers,
  });
 
  return response;
}