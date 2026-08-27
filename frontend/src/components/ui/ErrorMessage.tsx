"use client";

import { useState } from "react";
import { cn } from "@/lib/cn";

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
  className,
}: ErrorMessageProps) {
  const hasActions = actions.length > 0;

  return (
    <div
      className={cn(
        "rounded-xl border border-[#EF4444]/20 bg-[#EF4444]/5 px-4 py-3",
        "flex items-start gap-3",
        className,
      )}
      role="alert"
      aria-live="polite"
    >
      <svg
        className="mt-0.5 h-5 w-5 flex-shrink-0 text-[#EF4444]"
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
        <p className="text-sm text-[#EF4444]">{message}</p>

        {hasActions && (
          <div className="mt-2 flex flex-wrap gap-2">
            {actions.map((action, idx) => (
              <button
                key={idx}
                type="button"
                onClick={action.onAction}
                className={cn(
                  "inline-flex items-center justify-center rounded-lg",
                  "border border-[#005A9C] px-4 py-1.5 text-sm font-medium",
                  "text-[#005A9C] transition-colors duration-150",
                  "hover:bg-[#005A9C]/5 focus:outline-none focus:ring-2",
                  "focus:ring-[#005A9C]/30",
                )}
                aria-label={action.label}
              >
                {action.label}
              </button>
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
        className="mt-2 text-xs font-medium text-[#005A9C] hover:underline focus:outline-none focus:ring-1 focus:ring-[#005A9C]/30"
        aria-label={title ?? "Show step-by-step help"}
      >
        More Help
      </button>

      {open && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
          role="dialog"
          aria-modal="true"
          aria-labelledby="morehelp-title"
        >
          <div className="w-full max-w-sm rounded-xl bg-[#FFFFFF] p-5 shadow-xl">
            <h3 id="morehelp-title" className="text-sm font-semibold text-[#1E293B]">
              {title ?? "Step-by-step help"}
            </h3>
            <ul className="mt-3 space-y-2 text-sm text-[#1E293B]">
              {steps.map((step, idx) => (
                <li key={idx} className="flex gap-2">
                  <span className="flex-shrink-0 font-bold text-[#005A9C]">{idx + 1}.</span>
                  <span>{step}</span>
                </li>
              ))}
            </ul>
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="mt-4 w-full rounded-lg bg-[#005A9C] py-2 text-sm font-medium text-[#FFFFFF] hover:bg-[#005A9C]/90 focus:outline-none focus:ring-2 focus:ring-[#005A9C]/30"
              aria-label="Close help"
            >
              Got it
            </button>
          </div>
        </div>
      )}
    </>
  );
}
