"use client";

import type { InputHTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/cn";

export type ValidationState = "idle" | "validating" | "valid" | "invalid";

export interface InputFieldProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "children"> {
  label: string;
  example?: string;
  helpText?: string;
  validationState?: ValidationState;
  validationMessage?: string;
  icon?: ReactNode;
}

export function InputField({
  label,
  example,
  helpText,
  validationState = "idle",
  validationMessage,
  icon,
  className,
  type = "text",
  id,
  ...props
}: InputFieldProps) {
  const inputId = id ?? `field-${label.replace(/\s+/g, "-").toLowerCase()}`;
  const messageId = `${inputId}-message`;
  const describedById = helpText ? `${inputId}-help` : undefined;

  const stateClasses = {
    idle: "border-[var(--color-border)] focus:border-[var(--color-primary)] focus:ring-[var(--color-primary)]/20",
    validating: "border-[var(--color-warning)] focus:border-[var(--color-warning)] focus:ring-[var(--color-warning)]/20",
    valid: "border-[var(--color-success)] focus:border-[var(--color-success)] focus:ring-[var(--color-success)]/20",
    invalid: "border-[var(--color-error)] focus:border-[var(--color-error)] focus:ring-[var(--color-error)]/20" }[validationState];

  const statusIcon: Record<ValidationState, ReactNode> = {
    idle: null,
    validating: (
      <svg className="animate-spin h-4 w-4 text-[var(--color-warning)]" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
    ),
    valid: (
      <svg className="h-4 w-4 text-[var(--color-success)]" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
      </svg>
    ),
    invalid: (
      <svg className="h-4 w-4 text-[var(--color-error)]" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
      </svg>
    ) };

  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={inputId} className="text-sm font-medium text-[var(--color-text-primary)]">
        {label}
      </label>

      {helpText ? (
        <p id={helpText ? `${inputId}-help` : undefined} className="text-xs text-[var(--color-text-secondary)]">
          {helpText}
        </p>
      ) : null}

      <div className="relative">
        {icon ? (
          <span className="absolute inset-y-0 left-3 flex items-center text-[var(--color-text-secondary)]" aria-hidden="true">
            {icon}
          </span>
        ) : null}
        <input
          id={inputId}
          type={type}
          className={cn(
            "peer w-full rounded-md border bg-[var(--color-surface)] px-3 py-2 text-sm text-[var(--color-text-primary)]",
            "outline-none transition-colors duration-150",
            "focus:ring-2 focus:ring-offset-0",
            icon ? "ps-10" : "ps-3",
            stateClasses,
            className,
          )}
          aria-invalid={validationState === "invalid"}
          aria-describedby={describedById}
          {...props}
        />
        {validationState !== "idle" && (
          <span className="absolute inset-y-0 right-3 flex items-center" aria-hidden="true">
            {statusIcon[validationState]}
          </span>
        )}
      </div>

      {example ? (
        <p className="text-xs text-[var(--color-text-secondary)]">e.g. {example}</p>
      ) : null}

      {validationMessage ? (
        <p
          id={messageId}
          className={cn(
            "text-xs",
            validationState === "valid" ? "text-[var(--color-success)]" : "text-[var(--color-error)]",
          )}
          role={validationState === "invalid" ? "alert" : "status"}
          aria-live={validationState === "invalid" ? "polite" : "off"}
        >
          {validationMessage}
        </p>
      ) : null}
    </div>
  );
}
