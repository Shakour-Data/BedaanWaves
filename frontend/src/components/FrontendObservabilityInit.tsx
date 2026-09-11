"use client";

import { useFrontendObservability } from "@/lib/frontend-observability";

export function FrontendObservabilityInit() {
  useFrontendObservability();
  return null;
}
