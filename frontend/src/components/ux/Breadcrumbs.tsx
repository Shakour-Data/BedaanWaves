"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/cn";

export interface BreadcrumbItem {
  label: string;
  href?: string;
}

interface BreadcrumbsProps {
  items?: BreadcrumbItem[];
  className?: string;
  autoDerive?: boolean;
}

function prettySegment(seg: string): string {
  if (!seg) return "";
  const cleaned = seg.replace(/[-_]+/g, " ").trim();
  return cleaned
    .split(" ")
    .map((w) => (w.length > 0 ? w[0].toUpperCase() + w.slice(1) : w))
    .join(" ");
}

export function Breadcrumbs({ items, className, autoDerive = false }: BreadcrumbsProps) {
  const pathname = usePathname();
  const segments = pathname.split("/").filter(Boolean);

  const derived: BreadcrumbItem[] = segments.map((seg, i) => {
    const href = "/" + segments.slice(0, i + 1).join("/");
    return { label: prettySegment(seg), href };
  });

  const list: BreadcrumbItem[] = autoDerive ? derived : items ?? [];
  if (list.length === 0) return null;

  return (
    <nav aria-label="Breadcrumb" className={cn("mb-4", className)}>
      <ol className="flex flex-wrap items-center gap-1.5 text-sm">
        <li>
          <Link
            href="/dashboard"
            className="text-[var(--color-text-secondary)] hover:text-[var(--color-primary)] transition-colors"
          >
            Home
          </Link>
        </li>
        {list.map((item, index) => {
          const isLast = index === list.length - 1;
          return (
            <li key={`${item.href ?? item.label}-${index}`} className="flex items-center gap-1.5 min-w-0">
              <span aria-hidden="true" className="text-[var(--color-text-muted)]">/</span>
              {isLast || !item.href ? (
                <span
                  className={cn(
                    "font-medium truncate max-w-[280px]",
                    isLast ? "text-[var(--color-text-primary)]" : "text-[var(--color-text-secondary)]"
                  )}
                  aria-current={isLast ? "page" : undefined}
                >
                  {item.label}
                </span>
              ) : (
                <Link
                  href={item.href}
                  className="text-[var(--color-text-secondary)] hover:text-[var(--color-primary)] transition-colors truncate max-w-[200px]"
                >
                  {item.label}
                </Link>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}