"use client";

import { useState } from "react";
import { ChevronDown, X, Plus } from "lucide-react";
import { Button } from "@/components/ui/Button";
import {
  FilterGroup as FilterGroupType,
  FilterCondition as FilterConditionType,
  LogicOperator,
  FilterableField,
  FilterGroup,
  FilterCondition,
} from "@/types/filter";
import { ConditionRow } from "./ConditionRow";

interface GroupRowProps {
  group: FilterGroupType;
  fields: FilterableField[];
  depth: number;
  onAddCondition: (groupId: string) => void;
  onAddGroup: (groupId: string) => void;
  onRemove: (groupId: string, nodeId: string) => void;
  onUpdateNode: (groupId: string, nodeId: string, updater: (node: FilterCondition | FilterGroup) => FilterCondition | FilterGroup) => void;
  onSetLogic: (groupId: string, logic: LogicOperator) => void;
  parentId: string | null;
}

interface GroupRowProps {
  group: FilterGroupType;
  fields: FilterableField[];
  depth: number;
  onAddCondition: (groupId: string) => void;
  onAddGroup: (groupId: string) => void;
  onRemove: (groupId: string, nodeId: string) => void;
  onUpdateNode: (groupId: string, nodeId: string, updater: (node: FilterGroupType["conditions"][number]) => FilterGroupType["conditions"][number]) => void;
  onSetLogic: (groupId: string, logic: LogicOperator) => void;
  parentId: string | null;
}

export function GroupRow({
  group,
  fields,
  depth,
  onAddCondition,
  onAddGroup,
  onRemove,
  onUpdateNode,
  onSetLogic,
  parentId,
}: GroupRowProps) {
  const [collapsed, setCollapsed] = useState(false);

  const logicOptions: LogicOperator[] = depth === 0 && group.conditions.length <= 1
    ? ["AND"]
    : ["AND", "OR", "NOT"];

  return (
    <div className={`space-y-3 ${depth > 0 ? "ml-6 border-l-2 border-[var(--color-border)] pl-4" : ""}`}>
      <div className="flex items-center gap-2">
        {depth > 0 && (
          <select
            value={group.logic}
            onChange={(e) => onSetLogic(group.id, e.target.value as LogicOperator)}
            className="h-8 rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] px-2 py-1 text-xs font-semibold uppercase tracking-wider text-[var(--color-text-primary)] focus:border-[var(--color-primary)] focus:outline-none"
          >
            {logicOptions.map((op) => (
              <option key={op} value={op}>{op}</option>
            ))}
          </select>
        )}
        {depth === 0 && (
          <span className="text-xs font-semibold uppercase tracking-wider text-[var(--color-text-secondary)]">
            {group.logic}
          </span>
        )}
        <button
          type="button"
          onClick={() => setCollapsed(!collapsed)}
          className="rounded-lg p-1 text-[var(--color-text-secondary)] hover:bg-[var(--color-background)] hover:text-[var(--color-text-primary)]"
        >
          <ChevronDown className={`h-4 w-4 transition-transform ${collapsed ? "-rotate-90" : ""}`} />
        </button>
        {depth > 0 && (
          <button
            type="button"
            onClick={() => onRemove(parentId ?? "", group.id)}
            className="rounded-lg p-1 text-[var(--color-text-secondary)] hover:bg-error/10 hover:text-error"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      {!collapsed && (
        <div className="space-y-3">
          {group.conditions.map((node) =>
            "field" in node ? (
              <ConditionRow
                key={node.id}
                condition={node as FilterConditionType}
                fields={fields}
                onUpdate={(updater) => onUpdateNode(group.id, node.id, updater as (node: FilterCondition | FilterGroup) => FilterCondition | FilterGroup)}
                onRemove={() => onRemove(group.id, node.id)}
              />
            ) : (
              <GroupRow
                key={node.id}
                group={node as FilterGroupType}
                fields={fields}
                depth={depth + 1}
                onAddCondition={onAddCondition}
                onAddGroup={onAddGroup}
                onRemove={onRemove}
                onUpdateNode={onUpdateNode}
                onSetLogic={onSetLogic}
                parentId={group.id}
              />
            ),
          )}
          <div className="flex flex-wrap items-center gap-2">
            <Button size="sm" variant="outline" onClick={() => onAddCondition(group.id)}>
              <Plus className="h-4 w-4" /> Add Condition
            </Button>
            {depth < 3 && (
              <Button size="sm" variant="ghost" onClick={() => onAddGroup(group.id)}>
                <Plus className="h-4 w-4" /> Add Group
              </Button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
