export type Level = "overall" | "dimension" | "sub_dimension" | "aspect" | "sub_aspect";

export type LogicOperator = "AND" | "OR" | "NOT";

export type NumericOperator = "==" | "!=" | ">" | "<" | ">=" | "<=" | "between" | "is_null" | "is_not_null";

export type TextOperator = "==" | "!=" | "contains" | "does_not_contain" | "starts_with" | "ends_with" | "in_list" | "not_in_list";

export type DateOperator = "==" | "before" | "after" | "between" | "last_n_days" | "next_n_days" | "year_to_date";

export type FilterOperator = NumericOperator | TextOperator | DateOperator;

export interface FilterCondition {
  id: string;
  field: string;
  operator: FilterOperator;
  value: unknown;
  level: Level;
  label?: string;
}

export interface FilterGroup {
  id: string;
  logic: LogicOperator;
  conditions: (FilterGroup | FilterCondition)[];
}

export interface FilterableField {
  name: string;
  type: "numeric" | "text" | "date" | "json";
  levels: Level[];
  operators: string[];
  label: string;
  group: string;
}

export interface AdvancedFilterPayload {
  query: FilterGroup;
  limit: number;
  offset: number;
  sort_by?: string;
  sort_dir?: "asc" | "desc";
}

export interface AdvancedFilterResponse {
  status: string;
  total: number;
  limit: number;
  offset: number;
  results: Record<string, unknown>[];
  applied_filters: Array<{
    field: string;
    operator: string;
    value: unknown;
    level: string;
    path: string;
  }>;
  execution_time_ms: number;
}

export const LEVEL_LABELS: Record<Level, string> = {
  overall: "Overall",
  dimension: "Dimension",
  sub_dimension: "Sub-Dimension",
  aspect: "Aspect",
  sub_aspect: "Sub-Aspect",
};

export const LEVEL_COLORS: Record<Level, string> = {
  overall: "#005A9C",
  dimension: "#10B981",
  sub_dimension: "#2563EB",
  aspect: "#F59E0B",
  sub_aspect: "#EF4444",
};
