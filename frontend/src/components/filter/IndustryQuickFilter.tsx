"use client";

import { useState } from "react";
import { X } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import type { FilterableField } from "@/types/filter";

interface IndustryQuickFilterProps {
  fields: FilterableField[];
  selected: string[];
  onChange: (industries: string[]) => void;
}

export function IndustryQuickFilter({ fields, selected, onChange }: IndustryQuickFilterProps) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");

  const industryField = fields.find((f) => f.name === "industry");
  const allIndustries = [
    "Technology",
    "Healthcare",
    "Finance",
    "Retail",
    "Energy",
    "Consumer",
    "Industrial",
    "Materials",
    "Utilities",
    "Real Estate",
  ];

  const filtered = allIndustries.filter((ind) =>
    ind.toLowerCase().includes(search.toLowerCase()),
  );

  const toggle = (ind: string) => {
    if (selected.includes(ind)) {
      onChange(selected.filter((s) => s !== ind));
    } else {
      onChange([...selected, ind]);
    }
  };

  return (
    <div className="relative">
      <Button
        variant="outline"
        size="sm"
        onClick={() => setOpen(!open)}
        className="gap-2"
      >
        Industry
        {selected.length > 0 && (
          <Badge size="sm" variant="default">{selected.length}</Badge>
        )}
      </Button>
      {open && (
        <div className="absolute right-0 z-50 mt-2 w-72 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-3 shadow-lg">
          <div className="mb-2">
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search industries..."
              className="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] px-3 py-2 text-sm text-[var(--color-text-primary)] focus:border-[var(--color-primary)] focus:outline-none"
            />
          </div>
          <div className="max-h-48 space-y-1 overflow-y-auto">
            {filtered.map((ind) => (
              <label
                key={ind}
                className="flex cursor-pointer items-center gap-2 rounded-lg px-2 py-1.5 text-sm hover:bg-[var(--color-background)]"
              >
                <input
                  type="checkbox"
                  checked={selected.includes(ind)}
                  onChange={() => toggle(ind)}
                  className="h-4 w-4 rounded border-[var(--color-border)] accent-[var(--color-primary)]"
                />
                {ind}
              </label>
            ))}
          </div>
          {selected.length > 0 && (
            <div className="mt-2 flex items-center justify-between border-t border-[var(--color-border)] pt-2">
              <span className="text-xs text-[var(--color-text-secondary)]">
                {selected.length} selected
              </span>
              <button
                type="button"
                onClick={() => onChange([])}
                className="text-xs text-[var(--color-error)] hover:underline"
              >
                Clear
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
