import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

interface CardProps {
  children: ReactNode;
  className?: string;
  title?: string;
  subtitle?: string;
  footer?: ReactNode;
  onClick?: () => void;
  hoverable?: boolean;
  padding?: "sm" | "md" | "lg";
}

export function Card({
  children,
  className,
  title,
  subtitle,
  footer,
  onClick,
  hoverable = false,
  padding = "md",
}: CardProps) {
  const paddingClasses = {
    sm: "p-4",
    md: "p-6",
    lg: "p-8",
  };

  return (
    <div
      className={cn(
        "rounded-xl border border-border bg-surface shadow-sm transition-all duration-200",
        hoverable && "hover:shadow-md hover:border-primary/20 hover:-translate-y-0.5 cursor-pointer",
        onClick && "cursor-pointer",
        className
      )}
      onClick={onClick}
    >
      {(title || subtitle) && (
        <div className="border-b border-border px-6 py-4">
          {title && (
            <h3 className="text-base font-semibold text-foreground">{title}</h3>
          )}
          {subtitle && (
            <p className="mt-0.5 text-sm text-muted-foreground">{subtitle}</p>
          )}
        </div>
      )}
      <div className={cn(paddingClasses[padding])}>{children}</div>
      {footer && (
        <div className="border-t border-border px-6 py-3">{footer}</div>
      )}
    </div>
  );
}
