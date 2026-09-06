"use client";

import { useState } from "react";
import { Trash2 } from "lucide-react";
import {
  FilterCondition as FilterConditionType,
  FilterableField,
  Level,
  LEVEL_LABELS,
  LEVEL_COLORS,
} from "@/types/filter";

interface ConditionRowProps {
  condition: FilterConditionType;
  fields: FilterableField[];
  onUpdate: (updater: (c: FilterConditionType) => FilterConditionType) => void;
  onRemove: () => void;
}

export function ConditionRow({ condition, fields, onUpdate, onRemove }: ConditionRowProps) {
  const [valueTypeError, setValueTypeError] = useState(false);

  const selectedField = fields.find((f) => f.name === condition.field);
  const operators = selectedField?.operators ?? [];
  const fieldType = selectedField?.type ?? "text";

  const handleFieldChange = (field: string) => {
    const f = fields.find((ff) => ff.name === field);
    onUpdate((c) => ({
      ...c,
      field,
      operator: (f?.operators[0] ?? "==") as FilterConditionType["operator"],
      value: "",
      level: (f?.levels[0] ?? c.level) as Level,
    }));
    setValueTypeError(false);
  };

  const handleOperatorChange = (operator: string) => {
    onUpdate((c) => ({ ...c, operator: operator as FilterConditionType["operator"], value: "" }));
    setValueTypeError(false);
  };

  const handleValueChange = (raw: string) => {
    const field = fields.find((f) => f.name === condition.field);
    const op = condition.operator;

    if (op === "is_null" || op === "is_not_null") {
      onUpdate((c) => ({ ...c, value: null }));
      return;
    }

    if (field?.type === "numeric") {
      if (op === "between") {
        const parts = raw.split(",").map((s) => s.trim());
        const nums = parts.map(Number);
        if (parts.length === 2 && nums.every((n) => !Number.isNaN(n))) {
          onUpdate((c) => ({ ...c, value: [nums[0], nums[1]] }));
          setValueTypeError(false);
        } else {
          setValueTypeError(true);
        }
        return;
      }
      const num = Number(raw);
      if (raw === "" || Number.isNaN(num)) {
        setValueTypeError(true);
        return;
      }
      onUpdate((c) => ({ ...c, value: num }));
      setValueTypeError(false);
      return;
    }

    if (field?.type === "date") {
      onUpdate((c) => ({ ...c, value: raw }));
      setValueTypeError(false);
      return;
    }

    onUpdate((c) => ({ ...c, value: raw }));
    setValueTypeError(false);
  };

  const inputClass = "h-9 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-1 text-sm text-[var(--color-text-primary)] focus:border-[var(--color-primary)] focus:outline-none disabled:cursor-not-allowed disabled:opacity-50 transition duration-fast ease-flow";

  const renderValueInput = () => {
    if (condition.operator === "is_null" || condition.operator === "is_not_null") {
      return (
        <span className="text-xs text-[var(--color-text-secondary)] italic px-2">No value required</span>
      );
    }
    if (condition.operator === "in_list" || condition.operator === "not_in_list") {
      const arrVal = Array.isArray(condition.value) ? condition.value.join(", ") : String(condition.value ?? "");
      return (
        <input
          type="text"
          value={arrVal}
          onChange={(e) => handleValueChange(e.target.value)}
          placeholder="Comma-separated values"
          className={`${inputClass} ${valueTypeError ? "border-error" : ""}`}
        />
      );
    }
    if (condition.operator === "between") {
      const betweenVal = Array.isArray(condition.value) ? (condition.value as number[]).join(", ") : String(condition.value ?? "");
      return (
        <input
          type="text"
          value={betweenVal}
          onChange={(e) => handleValueChange(e.target.value)}
          placeholder="min, max"
          className={`${inputClass} ${valueTypeError ? "border-error" : ""}`}
        />
      );
    }
    if (fieldType === "date") {
      return (
        <input
          type="date"
          value={String(condition.value ?? "")}
          onChange={(e) => handleValueChange(e.target.value)}
          className={inputClass}
        />
      );
    }
    return (
      <input
        type={fieldType === "numeric" ? "number" : "text"}
        value={String(condition.value ?? "")}
        onChange={(e) => handleValueChange(e.target.value)}
        placeholder="Value"
        className={`${inputClass} ${valueTypeError ? "border-error" : ""}`}
      />
    );
  };

  const levelColor = LEVEL_COLORS[condition.level] ?? "#666";
  const levelBadgeClass = `inline-flex items-center rounded-full whitespace-nowrap border px-2 py-0.5 text-[10px] font-medium`;
  const levelBadgeStyle = {
    backgroundColor: `${levelColor}15`,
    color: levelColor,
    borderColor: `${levelColor}40`,
  };

  return (
    <div className="flex flex-wrap items-center gap-2 rounded-lg bg-[var(--color-background)] p-3">
      <span className={levelBadgeClass} style={levelBadgeStyle}>
        {LEVEL_LABELS[condition.level] ?? condition.level}
      </span>

      <select
        value={condition.field}
        onChange={(e) => handleFieldChange(e.target.value)}
        className="h-9 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-2 py-1 text-sm text-[var(--color-text-primary)] focus:border-[var(--color-primary)] focus:outline-none"
      >
        {fields
          .filter((f) => f.levels.includes(condition.level))
          .map((f) => (
            <option key={f.name} value={f.name}>{f.label}</option>
          ))}
      </select>

      <select
        value={condition.operator}
        onChange={(e) => handleOperatorChange(e.target.value)}
        className="h-9 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-2 py-1 text-sm text-[var(--color-text-primary)] focus:border-[var(--color-primary)] focus:outline-none"
      >
        {operators.map((op) => (
          <option key={op} value={op}>{op}</option>
        ))}
      </select>

      <div className="min-w-[140px] flex-1">{renderValueInput()}</div>

      <button
        type="button"
        onClick={onRemove}
        className="rounded-lg p-2 text-[var(--color-text-secondary)] hover:bg-error/10 hover:text-error"
      >
        <Trash2 className="h-4 w-4" />
      </button>
    </div>
  );
}
