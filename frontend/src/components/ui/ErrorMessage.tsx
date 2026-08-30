"use client";

import { useState } from "react";
import { cn } from "@/lib/cn";
import { Modal } from "./Modal";
import { Button } from "./Button";

export interface ActionOption {
  label: string;
  onAction: () => void;
}

export interface ErrorMessageProps {
  message: string;
  actions?: ActionOption[];
  moreHelpSteps?: string[];
  helpTitle?: string;
  className?: string;
}

export function ErrorMessage({
  message,
  actions = [],
  moreHelpSteps = [],
  helpTitle,
  className }: ErrorMessageProps) {
  const hasActions = actions.length > 0;

  return (
    <div
      className={cn(
        "rounded-xl border border-error/20 bg-error/5 px-4 py-3",
        "flex items-start gap-3",
        className,
      )}
      role="alert"
      aria-live="polite"
    >
      <svg
        className="mt-0.5 h-5 w-5 flex-shrink-0 text-error"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        aria-hidden="true"
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M12 9v4m0 4h.01M21 12c0 4.993-4.007 10-10 10S2 16.993 2 12 6.007 2 12 2s10 4.007 10 10z"
        />
      </svg>

      <div className="flex-1">
        <p className="text-sm text-error">{message}</p>

        {hasActions && (
          <div className="mt-2 flex flex-wrap gap-2">
            {actions.map((action, idx) => (
              <Button
                key={idx}
                size="sm"
                variant="outline"
                onClick={action.onAction}
                aria-label={action.label}
              >
                {action.label}
              </Button>
            ))}
          </div>
        )}

        {moreHelpSteps.length > 0 && (
          <HelpDialog steps={moreHelpSteps} title={helpTitle} />
        )}
      </div>
    </div>
  );
}

function HelpDialog({ steps, title }: { steps: string[]; title?: string }) {
  const [open, setOpen] = useState(false);

  if (steps.length === 0) return null;

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="mt-2 text-xs font-medium text-primary hover:underline focus:outline-none focus:ring-1 focus:ring-primary/30"
        aria-label={title ?? "Show step-by-step help"}
      >
        More Help
      </button>

      <Modal isOpen={open} onClose={() => setOpen(false)} title={title ?? "Step-by-step help"} size="sm">
        <ul className="mt-3 space-y-2 text-sm text-foreground">
          {steps.map((step, idx) => (
            <li key={idx} className="flex gap-2">
              <span className="flex-shrink-0 font-bold text-primary">{idx + 1}.</span>
              <span>{step}</span>
            </li>
          ))}
        </ul>
        <div className="mt-4 flex justify-end">
          <Button size="sm" onClick={() => setOpen(false)}>
            Got it
          </Button>
        </div>
      </Modal>
    </>
  );
}
