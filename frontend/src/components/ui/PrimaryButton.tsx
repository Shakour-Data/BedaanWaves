import type { ButtonHTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/cn";
import { semanticColors, fontSizes, spacing, motion } from "@/styles/design-tokens";

interface PrimaryButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  size?: "sm" | "md" | "lg";
  variant?: "default" | "destructive" | "outline" | "secondary" | "ghost" | "link";
}

/**
 * Primary Button - Main call-to-action button
 * Professional styling for primary actions
 */
export function PrimaryButton({
  children,
  className,
  size = "md",
  variant = "default",
  ...props
}: PrimaryButtonProps) {
  const sizeStyles = {
    sm: `px-${spacing[2]} py-${spacing[1]} text-${fontSizes.xs} rounded-md`,
    md: `px-${spacing[3]} py-${spacing[2]} text-${fontSizes.sm} rounded-lg`,
    lg: `px-${spacing[4]} py-${spacing[3]} text-${fontSizes.base} rounded-xl`,
  };

  const variantStyles = {
    default: `bg-[${semanticColors.primary}] text-[${semanticColors.primaryForeground}] hover:bg-[${semanticColors.destructive}] transition-all ${motion.durationFast} ${motion.easing}`,
    destructive: `bg-[${semanticColors.destructive}] text-[${semanticColors.primaryForeground}] hover:bg-[${semanticColors.destructive}] opacity-90 transition-all ${motion.durationFast} ${motion.easing}`,
    outline: `border-2 border-[${semanticColors.primary}] bg-transparent text-[${semanticColors.primary}] hover:bg-[${semanticColors.primary}]/10 transition-all ${motion.durationFast} ${motion.easing}`,
    secondary: `bg-[${semanticColors.secondary}] text-[${semanticColors.secondaryForeground}] hover:bg-[${semanticColors.secondary}]/90 transition-all ${motion.durationFast} ${motion.easing}`,
    ghost: `bg-transparent text-[${semanticColors.foreground}] hover:bg-[${semanticColors.neutral}] transition-all ${motion.durationFast} ${motion.easing}`,
    link: `bg-transparent text-[${semanticColors.primary}] underline hover:text-[${semanticColors.destructive}] transition-all ${motion.durationFast} ${motion.easing}`,
  };

  return (
    <button
      className={cn(
        "inline-flex items-center justify-center font-medium",
        "focus:outline-none focus:ring-2 focus:ring-[${semanticColors.primary}]/50",
        "disabled:pointer-events-none disabled:opacity-50",
        sizeStyles[size],
        variantStyles[variant],
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
}
