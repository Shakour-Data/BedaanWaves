export const colors = {
  primary: "#005A9C",
  "primary-hover": "#004578",
  "primary-light": "#E6F0FA",
  secondary: "#64748B",
  success: "#22C55E",
  warning: "#F59E0B",
  error: "#EF4444",
  background: "#F8FAFC",
  surface: "#FFFFFF",
  "surface-elevated": "#FFFFFF",
  neutral: "#F8FAFC",
  foreground: "#0F172A",
  "text-primary": "#0F172A",
  "text-secondary": "#475569",
  "text-muted": "#94A3B8",
  "muted-foreground": "#475569",
  border: "#E2E8F0",
  "border-light": "#F1F5F9",
} as const;

export const semanticColors = {
  background: colors.background,
  surface: colors.surface,
  foreground: colors.foreground,
  mutedForeground: colors["muted-foreground"],
  border: colors.border,
  primary: colors.primary,
  secondary: colors.secondary,
  neutral: colors.neutral,
  primaryForeground: "#FFFFFF",
  secondaryForeground: "#FFFFFF",
  accentForeground: "#3D2C00",
  destructive: colors.error,
  success: colors.success,
  error: colors.error,
  warning: colors.warning,
  info: colors.primary,
} as const;

export const darkColors = {
  primary: "#3B82F6",
  "primary-hover": "#60A5FA",
  "primary-light": "#1E3A5F",
  secondary: "#94A3B8",
  success: "#4ADE80",
  warning: "#FBBF24",
  error: "#F87171",
  background: "#0F172A",
  surface: "#1E293B",
  "surface-elevated": "#334155",
  neutral: "#0F172A",
  foreground: "#F8FAFC",
  "text-primary": "#F8FAFC",
  "text-secondary": "#94A3B8",
  "text-muted": "#64748B",
  "muted-foreground": "#94A3B8",
  border: "#334155",
  "border-light": "#1E293B",
} as const;

export const darkSemanticColors = {
  background: darkColors.background,
  surface: darkColors.surface,
  foreground: darkColors.foreground,
  mutedForeground: darkColors["muted-foreground"],
  border: darkColors.border,
  primary: darkColors.primary,
  secondary: darkColors.secondary,
  neutral: darkColors.neutral,
  primaryForeground: "#FFFFFF",
  secondaryForeground: "#FFFFFF",
  accentForeground: "#3D2C00",
  destructive: darkColors.error,
  success: darkColors.success,
  error: darkColors.error,
  warning: darkColors.warning,
  info: darkColors.primary,
} as const;

export const fontSizes = {
  xs: "0.75rem",
  sm: "0.875rem",
  base: "1rem",
  lg: "1.125rem",
  xl: "1.25rem",
  "2xl": "1.5rem",
  "3xl": "1.875rem",
  "4xl": "2.25rem",
} as const;

export const fontWeights = {
  normal: 400,
  medium: 500,
  semibold: 600,
  bold: 700,
} as const;

export const spacing = {
  1: "0.25rem",
  2: "0.5rem",
  3: "0.75rem",
  4: "1rem",
  5: "1.5rem",
  6: "2rem",
  8: "3rem",
  10: "4rem",
} as const;

export const shadows = {
  sm: "0 1px 2px 0 rgb(0 0 0 / 0.05)",
  md: "0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)",
  lg: "0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)",
  xl: "0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)",
} as const;

export const radii = {
  sm: "0.25rem",
  md: "0.5rem",
  lg: "0.75rem",
  xl: "1rem",
  "2xl": "1.5rem",
  full: "9999px",
} as const;

export const motion = {
  durationFast: "150ms",
  durationMedium: "300ms",
  durationSlow: "500ms",
  easing: "cubic-bezier(0.4, 0, 0.2, 1)",
} as const;

export const designTokens = {
  colors,
  semanticColors,
  darkColors,
  darkSemanticColors,
  fontSizes,
  fontWeights,
  spacing,
  shadows,
  radii,
  motion,
} as const;

export type DesignTokens = typeof designTokens;
