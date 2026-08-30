"use client";

import type { ButtonHTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/cn";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  size?: "sm" | "md" | "lg";
  variant?: "primary" | "secondary" | "outline" | "ghost" | "destructive";
}

const sizeClasses: Record<string, string> = {
  sm: "h-8 px-3 text-xs font-medium",
  md: "h-10 px-4 text-sm font-medium",
  lg: "h-12 px-6 text-base font-medium",
};

const variantClasses: Record<string, string> = {
  primary:
    "bg-primary text-white hover:bg-primary-hover active:bg-primary-hover/90 shadow-sm hover:shadow-md disabled:bg-primary/50",
  secondary:
    "bg-secondary text-white hover:bg-secondary/90 active:bg-secondary/80 shadow-sm disabled:bg-secondary/50",
  outline:
    "border-2 border-primary text-primary hover:bg-primary-light active:bg-primary-light/80 disabled:border-primary/50 disabled:text-primary/50",
  ghost:
    "text-foreground hover:bg-neutral active:bg-neutral/80 disabled:text-foreground/50",
  destructive:
    "bg-error text-white hover:bg-error/90 active:bg-error/80 shadow-sm disabled:bg-error/50",
};

export function Button({
  children,
  className,
  size = "md",
  variant = "primary",
  disabled,
  type = "button",
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      disabled={disabled}
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition-all duration-200 ease-out",
        "focus:outline-none focus:ring-2 focus:ring-primary/30 focus:ring-offset-2 focus:ring-offset-background",
        "active:scale-[0.98] disabled:pointer-events-none disabled:opacity-60",
        sizeClasses[size],
        variantClasses[variant],
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
}
