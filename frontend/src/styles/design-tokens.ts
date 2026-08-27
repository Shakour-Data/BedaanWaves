/**
 * design-tokens.ts
 * ---------------------------------------------------------------------------
 * Professional Market Analysis Platform Design System
 * Clean, financial-focused design tokens for market data visualization
 * and professional financial interfaces.
 * ---------------------------------------------------------------------------
 */

export const colors = {
  // Financial Red - Primary actions, alerts, market movers
  primary: "#DC2626",
  // Professional Slate - Secondary elements, borders, muted text
  secondary: "#64748B",
  // Light Grey - Background, cards
  neutral: "#F8FAFC",
  // Amber - Warnings, highlights
  accent: "#FBBF24" } as const;

export const semanticColors = {
  background: colors.neutral,
  surface: "#FFFFFF",
  foreground: "#1E293B",
  mutedForeground: "#64748B",
  border: "#E2E8F0",
  primary: colors.primary,
  secondary: colors.secondary,
  neutral: colors.neutral,
  primaryForeground: "#FFFFFF",
  secondaryForeground: "#FFFFFF",
  accentForeground: "#3D2C00",
  destructive: colors.primary,
  success: "#10B981",
  error: "#EF4444",
  warning: "#F59E0B",
  info: "#3B82F6" } as const;

export const fontSizes = {
  xs: "12px",
  sm: "14px",
  base: "16px",
  lg: "18px",
  xl: "20px",
  "2xl": "24px",
  "3xl": "30px",
  "4xl": "36px" } as const;

export const spacing = {
  1: "4px",
  2: "8px",
  3: "12px",
  4: "16px",
  5: "24px",
  6: "32px",
  8: "48px",
  10: "64px" } as const;

export const grid = {
  columns: 12,
  gutter: "16px" } as const;

export const motion = {
  durationFast: "150ms",
  durationMedium: "300ms",
  durationSlow: "500ms",
  easing: "cubic-bezier(0.4, 0, 0.2, 1)" } as const;

export const designTokens = {
  colors,
  semanticColors,
  fontSizes,
  spacing,
  grid,
  motion } as const;

export type DesignTokens = typeof designTokens;
