import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

export function TarotCard({
  children,
  icon,
  title,
  className,
  onClick }: {
  children: ReactNode;
  icon?: ReactNode;
  title?: string;
  className?: string;
  onClick?: () => void;
}) {
  return (
    <div
      className={cn(
        "bg-[var(--color-surface)] border border-[var(--color-border)] rounded-md p-6 shadow-md transition-shadow duration-150 ease-out",
        onClick && "cursor-pointer",
        className
      )}
      onClick={onClick}
    >
      {title && (
        <div className="mb-4">
          <h3 className="text-xl font-semibold text-[var(--color-text-primary)]">{title}</h3>
        </div>
      )}
      {children}
    </div>
  );
}
