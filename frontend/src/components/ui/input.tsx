import * as React from "react";
import { cn } from "@/lib/cn";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: boolean;
  helperText?: string;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, error, helperText, ...props }, ref) => {
    return (
      <div className="w-full space-y-1">
        <input
          type={type}
          className={cn(
            "flex h-10 w-full rounded-xl border border-border bg-surface px-3 py-2 text-sm text-foreground",
            "file:border-0 file:bg-transparent file:text-sm file:font-medium",
            "placeholder:text-muted-foreground",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/20 focus-visible:border-primary",
            "disabled:cursor-not-allowed disabled:opacity-50",
            "transition duration-fast ease-flow",
            error && "border-error focus-visible:ring-error/20 focus-visible:border-error",
            className
          )}
          ref={ref}
          {...props}
        />
        {helperText && (
          <p className={cn("text-[10px] px-1", error ? "text-error font-medium" : "text-muted-foreground")}>
            {helperText}
          </p>
        )}
      </div>
    );
  }
);
Input.displayName = "Input";

export { Input };