/**
 * design-tokens.ts
 * ---------------------------------------------------------------------------
 * تک‌نمونه‌های طراحی «معماری ارتعاشی» (Vibrational Design System)
 * همه‌ی تیم توسعه باید از این مقادیر پیروی کند تا خروجی از نظر روان‌شناختی
 * و بصری، «مسحورکننده» و هارمونیک باشد. (سند FrontEnd.txt - فصل پنجم)
 *
 * - رنگ‌ها بر اساس کابالا (آتش/آب/خاک/هوا)
 * - مقیاس تایپوگرافی بر اساس دنباله فیبوناچی (۱،۱،۲،۳،۵،۸،۱۳،۲۱،۳۴…)
 * - فضای خالی بر اساس مضارب ۸ (هشت‌تایی)
 * - انیمیشن بر اساس قانون ۳-۷-۳ و منحنی جریان طبیعی آب
 * ---------------------------------------------------------------------------
 */

export const colors = {
  /** Gevurah (قدرت) - آتش - دکمه‌ها و هشدارها */
  primary: "#C62828",
  /** Chesed (مهربانی) - آب - لینک‌ها و هدرها */
  secondary: "#1565C0",
  /** Yesod (بنیاد) - خاک - پس‌زمینه اصلی */
  neutral: "#F5F5F5",
  /** Tiferet (زیبایی) - هوا - هایلایت و موفقیت */
  accent: "#FFD54F",
} as const;

/** دسترسی‌پذیری: نسبت تضاد حداقل ۴.۵:۱ برای متن روی پس‌زمینه */
export const semanticColors = {
  background: colors.neutral,
  surface: "#FFFFFF",
  foreground: "#1A1A1A",
  mutedForeground: "#5C5C5C",
  border: "#E0E0E0",
  primaryForeground: "#FFFFFF",
  secondaryForeground: "#FFFFFF",
  accentForeground: "#3D2C00",
  destructive: colors.primary,
  success: "#2E7D32",
} as const;

/**
 * مقیاس فیبوناچی برای تایپوگرافی.
 * h1 = ۳۴px (بیست‌ویکمین عدد)، body = ۱۶px (هشتمین عدد)
 */
export const fontSizes = {
  xs: "13px",
  sm: "16px",
  base: "16px",
  lg: "21px",
  xl: "34px",
  "2xl": "55px",
  "3xl": "89px",
} as const;

/** فضای خالی بر اساس مضارب ۸ (آبِ طراحی) */
export const spacing = {
  1: "8px",
  2: "16px",
  3: "24px",
  4: "48px",
  5: "96px",
} as const;

/** شبکه‌ی زندگی: ۱۲ ستونه با فاصله ۲۴px */
export const grid = {
  columns: 12,
  gutter: "24px",
} as const;

/**
 * قانون ۳-۷-۳ انیمیشن:
 * ۳۰۰ms تعاملات کوچک، ۷۰۰ms ترنزیشن صفحه، ۳۰۰۰ms انیمیشن پس‌زمینه
 */
export const motion = {
  durationFast: "300ms",
  durationPage: "700ms",
  durationAmbient: "3000ms",
  /** منحنی جریان طبیعی آب */
  easing: "cubic-bezier(0.25, 0.1, 0.25, 1.0)",
} as const;

export const designTokens = {
  colors,
  semanticColors,
  fontSizes,
  spacing,
  grid,
  motion,
} as const;

export type DesignTokens = typeof designTokens;
