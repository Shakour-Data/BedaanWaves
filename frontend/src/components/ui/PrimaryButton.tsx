"use client";

import { Button } from "./Button";
import type { ButtonHTMLAttributes, ReactNode } from "react";

interface PrimaryButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  size?: "sm" | "md" | "lg";
  variant?: "default" | "destructive" | "outline" | "secondary" | "ghost" | "link";
}

const variantMap: Record<string, "primary" | "destructive" | "outline" | "secondary" | "ghost"> = {
  default: "primary",
  destructive: "destructive",
  outline: "outline",
  secondary: "secondary",
  ghost: "ghost",
};

export function PrimaryButton({
  children,
  className,
  size = "md",
  variant = "default",
  ...props
}: PrimaryButtonProps) {
  return (
    <Button
      size={size}
      variant={variantMap[variant] ?? "primary"}
      className={className}
      {...props}
    >
      {children}
    </Button>
  );
}
