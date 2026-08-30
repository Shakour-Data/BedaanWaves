import type { ReactNode } from "react";
import { Card } from "./Card";

interface TarotCardProps {
  children: ReactNode;
  icon?: ReactNode;
  title?: string;
  className?: string;
  onClick?: () => void;
}

export function TarotCard({
  children,
  icon,
  title,
  className,
  onClick,
}: TarotCardProps) {
  return (
    <Card title={title} className={className} onClick={onClick} hoverable={!!onClick}>
      {icon && <div className="mb-3 text-muted-foreground">{icon}</div>}
      {children}
    </Card>
  );
}
