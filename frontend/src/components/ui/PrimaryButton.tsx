import type { ButtonHTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/cn";

interface PrimaryButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
}

/**
 * دکمه‌ی اصلی (Primary Button) - «قلب تپنده‌ی سایت»
 * هاله‌ی نور طلایی + حرکت به سمت بالا در هاور (۳۰۰ms). (FrontEnd.txt - فصل چهارم)
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
