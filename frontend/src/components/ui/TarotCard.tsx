import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

interface TarotCardProps {
  children: ReactNode;
  /** آیکون ساده‌شده‌ی طبیعت (خورشید، کوه، درخت) برای بیداری آرکیتایپ کهن */
  icon?: ReactNode;
  title?: string;
  className?: string;
}

/**
 * کارت‌های محتوا (The Tarot Cards)
 * سایه‌ی رنگ‌شده برای انتقال حس «حضور یک نیروی نامرئی». (FrontEnd.txt - فصل چهارم)
 */
export function TarotCard({
  children,
  icon,
  title,
  className,
}: TarotCardProps) {
  return (
    <article className={cn("tarot-card", className)}>
      {icon ? <div className="mb-3 text-secondary text-2xl">{icon}</div> : null}
      {title ? <h3 className="text-lg font-semibold mb-2">{title}</h3> : null}
      {children}
    </article>
  );
}
