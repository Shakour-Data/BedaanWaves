"use client";

import type { ButtonHTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/cn";
import { semanticColors, fontSizes, spacing, motion } from "@/styles/design-tokens";

interface PrimaryButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  size?: "sm" | "md" | "lg";
  variant?: "default" | "destructive" | "outline" | "secondary" | "ghost" | "link";
}

const sizeClasses: Record<string, string> = {
  sm: `px-${spacing[2]} py-${spacing[1]} text-${fontSizes.xs} rounded-md`,
  md: `px-${spacing[3]} py-${spacing[2]} text-${fontSizes.sm} rounded-lg`,
  lg: `px-${spacing[4]} py-${spacing[3]} text-${fontSizes.base} rounded-xl`,
};

const variantClasses: Record<string, { bg: string; text: string; border?: string; hoverBg?: string }> = {
  default: { bg: semanticColors.primary, text: semanticColors.primaryForeground, hoverBg: semanticColors.destructive },
  destructive: { bg: semanticColors.destructive, text: semanticColors.primaryForeground },
  outline: { bg: "transparent", text: semanticColors.primary, border: semanticColors.primary, hoverBg: `${semanticColors.primary}1A` },
  secondary: { bg: semanticColors.secondary, text: semanticColors.secondaryForeground, hoverBg: `${semanticColors.secondary}E6` },
  ghost: { bg: "transparent", text: semanticColors.foreground, hoverBg: semanticColors.neutral },
  link: { bg: "transparent", text: semanticColors.primary, hoverBg: "transparent" },
};

export function PrimaryButton({
  children,
  className,
  size = "md",
  variant = "default",
  ...props
}: PrimaryButtonProps) {
  const v = variantClasses[variant];

  const dynamicStyle: Record<string, string> = {
    backgroundColor: v.bg,
    color: v.text,
    transitionProperty: "background-color, color, transform, box-shadow",
    transitionDuration: motion.durationFast,
    transitionTimingFunction: motion.easing,
  };

  if (v.border) {
    dynamicStyle.border = `2px solid ${v.border}`;
  }
  if (v.hoverBg && v.hoverBg !== "transparent") {
    dynamicStyle["--hover-bg"] = v.hoverBg;
  }

  return (
    <button
      className={cn(
        "inline-flex items-center justify-center font-medium",
        "focus:outline-none focus:ring-2 focus:ring-offset-2",
        "disabled:pointer-events-none disabled:opacity-50",
        sizeClasses[size],
        className
      )}
      style={dynamicStyle}
      onMouseEnter={(e) => {
        if (v.hoverBg && v.hoverBg !== "transparent") {
          (e.currentTarget as HTMLButtonElement).style.backgroundColor = v.hoverBg;
        }
      }}
      onMouseLeave={(e) => {
        if (v.hoverBg && v.hoverBg !== "transparent") {
          (e.currentTarget as HTMLButtonElement).style.backgroundColor = v.bg;
        }
      }}
      {...props}
    >
      {children}
    </button>
  );
}
