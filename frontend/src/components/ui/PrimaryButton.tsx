import type { ButtonHTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/cn";

interface PrimaryButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
}

/**
 * Primary Button - Main call-to-action button
 * Professional styling for primary actions
 */
export function PrimaryButton({
  children,
  className,
  ...props
}: PrimaryButtonProps) {
  return (
    <button className={cn("btn-primary", className)} {...props}>
      <span className="btn-text">{children}</span>
      <span className="btn-glow" aria-hidden="true" />
    </button>
  );
}
