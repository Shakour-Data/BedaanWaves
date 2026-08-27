import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

export function TarotCard({
  children,
  icon,
  title,
  className,
}: {
  children: ReactNode;
  icon?: ReactNode;
  title?: string;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "rounded-xl border border-border bg-surface p-4 shadow-sm",
        "transition duration-fast ease-flow hover:shadow-md",
        className
      )}
    >
      {(icon || title) && (
        <div className="mb-3 flex items-center gap-2">
          {icon ? <span className="text-base">{icon}</span> : null}
          {title ? (
            <span className="text-sm font-semibold text-foreground">{title}</span>
          ) : null}
        </div>
      )}
      {children}
    </div>
  );
}
