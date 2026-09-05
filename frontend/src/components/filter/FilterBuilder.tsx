"use client";

import { useState, useCallback } from "react";
import { Plus } from "lucide-react";
import { Button } from "@/components/ui/Button";
import {
  FilterGroup as FilterGroupType,
  FilterCondition as FilterConditionType,
  LogicOperator,
  FilterableField,
} from "@/types/filter";
import { GroupRow } from "./GroupRow";

function uid(prefix = "f"): string {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

interface FilterBuilderProps {
  query: FilterGroupType;
  fields: FilterableField[];
  onChange: (query: FilterGroupType) => void;
  onApply: () => void;
  loading?: boolean;
}

export function FilterBuilder({ query, fields, onChange, onApply, loading }: FilterBuilderProps) {
  const updateGroup = useCallback(
    (groupId: string, updater: (g: FilterGroupType) => FilterGroupType) => {
      const next = updater(JSON.parse(JSON.stringify(query)) as FilterGroupType);
      onChange(next);
    },
    [query, onChange],
  );

  const addCondition = useCallback(
    (groupId: string) => {
      updateGroup(groupId, (g) => {
        const newCond: FilterConditionType = {
          id: uid("c"),
          field: fields[0]?.name ?? "",
          operator: "==",
          value: "",
          level: "overall",
        };
        return { ...g, conditions: [...g.conditions, newCond] };
      });
    },
    [updateGroup, fields],
  );

  const addGroup = useCallback(
    (groupId: string) => {
      updateGroup(groupId, (g) => {
        const newGroup: FilterGroupType = {
          id: uid("g"),
          logic: "AND",
          conditions: [],
        };
        return { ...g, conditions: [...g.conditions, newGroup] };
      });
    },
    [updateGroup],
  );

  const removeNode = useCallback(
    (groupId: string, nodeId: string) => {
      updateGroup(groupId, (g) => ({
        ...g,
        conditions: g.conditions.filter((c) => c.id !== nodeId),
      }));
    },
    [updateGroup],
  );

  const updateNode = useCallback(
    (groupId: string, nodeId: string, updater: (node: FilterGroupType["conditions"][number]) => FilterGroupType["conditions"][number]) => {
      updateGroup(groupId, (g) => ({
        ...g,
        conditions: g.conditions.map((c) => (c.id === nodeId ? updater(c) : c)),
      }));
    },
    [updateGroup],
  );

  const setLogic = useCallback(
    (groupId: string, logic: LogicOperator) => {
      updateGroup(groupId, (g) => ({ ...g, logic }));
    },
    [updateGroup],
  );

  return (
    <div className="space-y-4 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5 shadow-sm">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-[var(--color-text-primary)]">Filter Builder</h3>
        <Button size="sm" variant="primary" onClick={onApply} disabled={loading}>
          Apply Filters
        </Button>
      </div>
      <GroupRow
        group={query}
        fields={fields}
        depth={0}
        onAddCondition={addCondition}
        onAddGroup={addGroup}
        onRemove={removeNode}
        onUpdateNode={updateNode}
        onSetLogic={setLogic}
        parentId={null}
      />
    </div>
  );
}
