import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import {
  ViewHeaderControls,
  ScoringLevelSelector,
  ParentSelector,
  levelItemsFromHierarchy,
} from "@/components/scoring/ChartWrappers";
import type { HierarchyScores } from "@/store/useDateStore";

describe("ViewHeaderControls (AC6 tabs + windows + view mode)", () => {
  const noop = vi.fn();

  it("renders HISTORICAL and INTRADAY tabs", () => {
    render(
      <ViewHeaderControls
        scoringTab="HISTORICAL"
        onScoringTabChange={noop}
        viewMode="SIMPLE"
        onViewModeChange={noop}
        windowDaily={30}
        onWindowDailyChange={noop}
        windowIntraday="24h"
        onWindowIntradayChange={noop}
      />
    );
    expect(screen.getByText(/HISTORICAL/)).not.toBeNull();
    expect(screen.getByText(/INTRADAY/)).not.toBeNull();
  });

  it("fires onScoringTabChange when INTRADAY tab clicked", () => {
    const onChange = vi.fn();
    render(
      <ViewHeaderControls
        scoringTab="HISTORICAL"
        onScoringTabChange={onChange}
        viewMode="SIMPLE"
        onViewModeChange={noop}
        windowDaily={30}
        onWindowDailyChange={noop}
        windowIntraday="24h"
        onWindowIntradayChange={noop}
      />
    );
    fireEvent.click(screen.getByText(/INTRADAY/));
    expect(onChange).toHaveBeenCalledWith("INTRADAY");
  });

  it("renders SIMPLE / EXPERT toggle buttons", () => {
    render(
      <ViewHeaderControls
        scoringTab="HISTORICAL"
        onScoringTabChange={noop}
        viewMode="EXPERT"
        onViewModeChange={noop}
        windowDaily={90}
        onWindowDailyChange={noop}
        windowIntraday="24h"
        onWindowIntradayChange={noop}
      />
    );
    expect(screen.getByText(/SIMPLE/)).not.toBeNull();
    expect(screen.getByText(/EXPERT/)).not.toBeNull();
  });

  it("renders 30D / 90D / 365D window buttons when HISTORICAL tab active", () => {
    render(
      <ViewHeaderControls
        scoringTab="HISTORICAL"
        onScoringTabChange={noop}
        viewMode="SIMPLE"
        onViewModeChange={noop}
        windowDaily={30}
        onWindowDailyChange={noop}
        windowIntraday="24h"
        onWindowIntradayChange={noop}
      />
    );
    expect(screen.getByText(/30D/)).not.toBeNull();
    expect(screen.getByText(/90D/)).not.toBeNull();
    expect(screen.getByText(/365D/)).not.toBeNull();
  });

  it("renders 6H / 24H / 7D window buttons when INTRADAY tab active", () => {
    render(
      <ViewHeaderControls
        scoringTab="INTRADAY"
        onScoringTabChange={noop}
        viewMode="SIMPLE"
        onViewModeChange={noop}
        windowDaily={30}
        onWindowDailyChange={noop}
        windowIntraday="24h"
        onWindowIntradayChange={noop}
      />
    );
    expect(screen.getByText(/6H/)).not.toBeNull();
    expect(screen.getByText(/24H/)).not.toBeNull();
    expect(screen.getByText(/7D/)).not.toBeNull();
  });

  it("role=tablist aria-label present for a11y", () => {
    const { container } = render(
      <ViewHeaderControls
        scoringTab="HISTORICAL"
        onScoringTabChange={noop}
        viewMode="SIMPLE"
        onViewModeChange={noop}
        windowDaily={30}
        onWindowDailyChange={noop}
        windowIntraday="24h"
        onWindowIntradayChange={noop}
      />
    );
    const tl = container.querySelector('[role="tablist"]');
    expect(tl).not.toBeNull();
  });
});

describe("ScoringLevelSelector (AC6 5-level L0..L4)", () => {
  it("renders five levels: OVERALL, DIM, SUB-DIM, ASP, SUB-ASP", () => {
    render(
      <ScoringLevelSelector
        value="dimension"
        onChange={() => {}}
      />
    );
    expect(screen.getByText(/OVERALL/)).not.toBeNull();
    expect(screen.getByText("DIM")).not.toBeNull();
    expect(screen.getByText("SUB-DIM")).not.toBeNull();
    expect(screen.getByText("ASP")).not.toBeNull();
    expect(screen.getByText("SUB-ASP")).not.toBeNull();
  });

  it("calls onChange when OVERALL level clicked", () => {
    const onChange = vi.fn();
    render(<ScoringLevelSelector value="dimension" onChange={onChange} />);
    fireEvent.click(screen.getByText(/OVERALL/));
    expect(onChange).toHaveBeenCalledWith("overall");
  });
});

describe("ParentSelector (AC6 parent picker + ALL)", () => {
  it("renders provided options", () => {
    render(
      <ParentSelector
        level="dimension"
        value="ALL"
        onChange={() => {}}
        options={["fundamental", "technical", "sentiment"]}
      />
    );
    expect(screen.getByText(/fundamental/)).not.toBeNull();
    expect(screen.getByText(/technical/)).not.toBeNull();
    expect(screen.getByText(/sentiment/)).not.toBeNull();
  });

  it("onChange fires with the clicked option key", () => {
    const onChange = vi.fn();
    render(
      <ParentSelector
        level="dimension"
        value="ALL"
        onChange={onChange}
        options={["risk", "macro"]}
      />
    );
    fireEvent.click(screen.getByText(/risk/));
    expect(onChange).toHaveBeenCalledWith("risk");
  });
});

describe("levelItemsFromHierarchy (3-form tolerance helper)", () => {
  it("reads from legacy hierarchy level1..level4 array form", () => {
    const legacy = {
      overall: 60.0,
      level1: [{ key: "technical", label: "Technical", value: 65.0 }],
    } as unknown as HierarchyScores;
    const out = levelItemsFromHierarchy(legacy, "dimension");
    expect(out.length).toBeGreaterThan(0);
    expect(out[0].key).toBe("technical");
    expect(out[0].score).toBe(65.0);
  });

  it("reads from Pydantic short-key dict form (dimension / sub_dimension)", () => {
    const pydantic = {
      overall: 55.0,
      dimensions: { fundamental: 70.0 },
      sub_dimensions: { valuation: 62.0 },
    } as unknown as HierarchyScores;
    const dims = levelItemsFromHierarchy(pydantic, "dimension");
    const subs = levelItemsFromHierarchy(pydantic, "sub_dimension");
    expect(dims[0].key).toBe("fundamental");
    expect(dims[0].score).toBe(70.0);
    expect(subs[0].key).toBe("valuation");
    expect(subs[0].score).toBe(62.0);
  });

  it("returns empty array when level has no data", () => {
    const empty = { overall: 50.0 } as HierarchyScores;
    const out = levelItemsFromHierarchy(empty, "aspect");
    expect(Array.isArray(out)).toBe(true);
    expect(out.length).toBe(0);
  });
});
