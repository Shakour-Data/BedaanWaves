import { cn } from "@/lib/cn";

interface BadgeProps {
  children: React.ReactNode;
  variant?: "default" | "success" | "error" | "warning" | "info" | "neutral";
  size?: "sm" | "md";
  className?: string;
}

const variantStyles: Record<string, string> = {
  default: "bg-primary/10 text-primary border border-primary/20",
  success: "bg-success/10 text-success border border-success/20",
  error: "bg-error/10 text-error border border-error/20",
  warning: "bg-warning/10 text-warning border border-warning/20",
  info: "bg-primary-light/50 text-primary border border-primary/20",
  neutral: "bg-neutral text-muted-foreground border border-border",
};

const sizeStyles: Record<string, string> = {
  sm: "px-2 py-0.5 text-[10px] font-medium",
  md: "px-2.5 py-1 text-xs font-semibold",
};

export function Badge({ children, variant = "default", size = "md", className }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full whitespace-nowrap",
        variantStyles[variant],
        sizeStyles[size],
        className
      )}
    >
      {children}
    </span>
  );
}
