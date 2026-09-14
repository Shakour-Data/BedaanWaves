"use client";

import { useEffect } from "react";
import { onCLS, onINP, onLCP, onFCP, onTTFB, type Metric } from "web-vitals";
import { API_BASE_URL } from "./utils";

function send(payload: Record<string, unknown>) {
  if (typeof navigator === "undefined" || !navigator.sendBeacon) {
    return;
  }
  const blob = new Blob([JSON.stringify(payload)], { type: "application/json" });
  navigator.sendBeacon(`${API_BASE_URL}/system/observability/frontend-metrics`, blob);
}

export function reportWebVitals() {
  const report = (type: string) => (metric: Metric) => send({ type, ...metric });
  onCLS(report("CLS"));
  onINP(report("INP"));
  onLCP(report("LCP"));
  onFCP(report("FCP"));
  onTTFB(report("TTFB"));
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
