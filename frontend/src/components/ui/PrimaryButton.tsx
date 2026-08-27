"use client";

import type { ButtonHTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/cn";

interface PrimaryButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  size?: "sm" | "md" | "lg";
  variant?: "default" | "destructive" | "outline" | "secondary" | "ghost" | "link";
}

const sizeClasses: Record<string, string> = {
  sm: "px-3 py-1 text-xs rounded-md",
  md: "px-5 py-2 text-sm rounded-lg",
  lg: "px-6 py-3 text-base rounded-xl" };

const variantClasses: Record<string, string> = {
  default: "bg-primary text-[var(--color-text-primary)] hover:bg-red-700 shadow-sm hover:shadow-md",
  destructive: "bg-error text-[var(--color-text-primary)] hover:bg-red-700",
  outline: "bg-transparent text-primary border-2 border-primary hover:bg-primary/10",
  secondary: "bg-secondary text-[var(--color-text-primary)] hover:bg-secondary/90",
  ghost: "bg-transparent text-foreground hover:bg-neutral",
  link: "bg-transparent text-primary hover:underline px-0 py-0" };

export function PrimaryButton({
  children,
  className,
  size = "md",
  variant = "default",
  ...props
}: PrimaryButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center font-semibold transition duration-fast ease-flow",
        "focus:outline-none focus:ring-2 focus:ring-primary/20 focus:ring-offset-2",
        "disabled:pointer-events-none disabled:opacity-50 active:scale-95",
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
