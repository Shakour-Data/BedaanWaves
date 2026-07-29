import type { NewsItem } from "@/lib/dashboard-data";

export function NewsList({ items }: { items: NewsItem[] }) {
  return (
    <ul className="flex flex-col gap-3">
      {items.map((n, i) => (
        <li key={i} className="border-b border-border/60 pb-3 last:border-0 last:pb-0">
          <p className="text-sm font-medium leading-snug">{n.title}</p>
          <p className="mt-1 text-xs text-muted-foreground">
            {n.source} · {n.time}
          </p>
        </li>
      ))}
    </ul>
  );
}
