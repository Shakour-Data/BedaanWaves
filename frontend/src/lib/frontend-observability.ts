"use client";

import { useEffect } from "react";
import { onCLS, onINP, onLCP, onFCP, onTTFB } from "web-vitals";

function send(payload: Record<string, unknown>) {
  if (typeof navigator === "undefined" || !navigator.sendBeacon) {
    return;
  }
  const blob = new Blob([JSON.stringify(payload)], { type: "application/json" });
  navigator.sendBeacon("/api/v1/system/observability/frontend-metrics", blob);
}

export function reportWebVitals() {
  onCLS((metric) => send({ type: "CLS", ...metric }));
  onINP((metric) => send({ type: "INP", ...metric }));
  onLCP((metric) => send({ type: "LCP", ...metric }));
  onFCP((metric) => send({ type: "FCP", ...metric }));
  onTTFB((metric) => send({ type: "TTFB", ...metric }));
}

export function useFrontendObservability() {
  useEffect(() => {
    reportWebVitals();
  }, []);
}

export function captureFrontendError(error: Error, context?: Record<string, unknown>) {
  send({
    type: "frontend-error",
    message: error.message,
    stack: error.stack,
    name: error.name,
    context: context || {},
    timestamp: new Date().toISOString(),
    userAgent: typeof navigator !== "undefined" ? navigator.userAgent : undefined,
    url: typeof window !== "undefined" ? window.location.href : undefined,
  });
}
