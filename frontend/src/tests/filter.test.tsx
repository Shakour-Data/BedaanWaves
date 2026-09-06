import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { FilterBuilder } from "@/components/filter/FilterBuilder";
import { ActiveFilters } from "@/components/filter/ActiveFilters";
import { IndustryQuickFilter } from "@/components/filter/IndustryQuickFilter";
import type { FilterGroup, FilterableField, AdvancedFilterResponse } from "@/types/filter";

const mockFields: FilterableField[] = [
  { name: "overall_score", type: "numeric", levels: ["overall"], operators: [">", "<"], label: "Overall Score", group: "Score" },
  { name: "industry", type: "text", levels: ["overall"], operators: ["==", "contains"], label: "Industry", group: "Classification" },
  { name: "dimension_score", type: "numeric", levels: ["dimension"], operators: [">", "<"], label: "Dimension Score", group: "Score" },
];

const initialQuery: FilterGroup = {
  id: "g_1",
  logic: "AND",
  conditions: [
    { id: "c_1", field: "overall_score", operator: ">", value: 500, level: "overall" },
  ],
};

describe("FilterBuilder", () => {
  it("renders an initial condition", () => {
    render(
      <FilterBuilder
        query={initialQuery}
        fields={mockFields}
        onChange={() => {}}
        onApply={() => {}}
      />,
    );
    expect(screen.getByText("Filter Builder")).toBeDefined();
    expect(screen.getByText("Overall Score")).toBeDefined();
  });

  it("calls onApply when Apply Filters is clicked", () => {
    const onApply = vi.fn();
    render(
      <FilterBuilder
        query={initialQuery}
        fields={mockFields}
        onChange={() => {}}
        onApply={onApply}
      />,
    );
    fireEvent.click(screen.getByText("Apply Filters"));
    expect(onApply).toHaveBeenCalled();
  });

  it("adds a new condition when Add Condition is clicked", () => {
    const onChange = vi.fn();
    render(
      <FilterBuilder
        query={initialQuery}
        fields={mockFields}
        onChange={onChange}
        onApply={() => {}}
      />,
    );
    fireEvent.click(screen.getByText("Add Condition"));
    expect(onChange).toHaveBeenCalled();
  });
});

describe("ActiveFilters", () => {
  const applied: AdvancedFilterResponse["applied_filters"] = [
    { field: "overall_score", operator: ">", value: 750, level: "overall", path: "overall_score" },
    { field: "industry", operator: "==", value: "Technology", level: "overall", path: "industry" },
  ];

  it("renders chips for applied filters", () => {
    render(<ActiveFilters applied={applied} onClearAll={() => {}} />);
    expect(screen.getByText("overall_score")).toBeDefined();
    expect(screen.getByText("industry")).toBeDefined();
  });

  it("renders Clear All button", () => {
    render(<ActiveFilters applied={applied} onClearAll={() => {}} />);
    expect(screen.getByText("Clear All")).toBeDefined();
  });
});

describe("IndustryQuickFilter", () => {
  it("renders the Industry button", () => {
    render(<IndustryQuickFilter fields={mockFields} selected={[]} onChange={() => {}} />);
    expect(screen.getByText("Industry")).toBeDefined();
  });

  it("opens dropdown on click", () => {
    render(<IndustryQuickFilter fields={mockFields} selected={[]} onChange={() => {}} />);
    fireEvent.click(screen.getByText("Industry"));
    expect(screen.getByPlaceholderText("Search industries...")).toBeDefined();
  });

  it("shows selected count badge", () => {
    render(<IndustryQuickFilter fields={mockFields} selected={["Technology"]} onChange={() => {}} />);
    expect(screen.getByText("1")).toBeDefined();
  });
});
