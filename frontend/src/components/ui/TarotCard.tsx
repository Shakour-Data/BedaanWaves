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
        "rounded-xl border border-[#E2E8F0] bg-[#FFFFFF] p-4 shadow-sm",
        "transition-shadow duration-150 hover:shadow-md",
        className
      )}
    >
      {(icon || title) && (
        <div className="mb-3 flex items-center gap-2">
          {icon ? <span className="text-base">{icon}</span> : null}
          {title ? (
            <span className="text-sm font-semibold text-[#1E293B]">{title}</span>
          ) : null}
        </div>
      )}
      {children}
    </div>
  );
}
