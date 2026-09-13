"use client";

import { Button } from "./Button";
import type { ButtonHTMLAttributes, ReactNode } from "react";

interface PrimaryButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  size?: "sm" | "md" | "lg";
  variant?: "default" | "destructive" | "outline" | "secondary" | "ghost" | "link";
}

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
      variant={variant === "default" ? "primary" : variant === "destructive" ? "destructive" : variant === "outline" ? "outline" : variant === "secondary" ? "secondary" : "ghost"}
      className={className}
      {...props}
    >
      {children}
    </Button>
  );
}