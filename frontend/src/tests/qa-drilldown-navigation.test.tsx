import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { LevelSelector } from "@/components/leaderboard/LevelSelector";

describe("QA Priority 1 - Drill-down Navigation & Back Button", () => {
  it("changes level without unmounting the selector", () => {
    const onLevelChange = vi.fn();
    const onDimensionChange = vi.fn();

    render(
      <LevelSelector
        level="overall"
        dimension="fundamental"
        onLevelChange={onLevelChange}
        onDimensionChange={onDimensionChange}
      />,
    );

    const dimensionButton = screen.getByRole("button", { name: /^dimensions$/i });
    expect(dimensionButton).toBeInTheDocument();

    dimensionButton.click();
    expect(onLevelChange).toHaveBeenCalledWith("dimension");
  });

  it("shows dimension pills when level is not overall", () => {
    const onLevelChange = vi.fn();
    const onDimensionChange = vi.fn();

    render(
      <LevelSelector
        level="dimension"
        dimension="fundamental"
        onLevelChange={onLevelChange}
        onDimensionChange={onDimensionChange}
      />,
    );

    expect(screen.getByText("Fundamental")).toBeInTheDocument();
    expect(screen.getByText("Technical")).toBeInTheDocument();
    expect(screen.getByText("Sentiment")).toBeInTheDocument();
  });

  it("hides dimension pills when level is overall", () => {
    const onLevelChange = vi.fn();
    const onDimensionChange = vi.fn();

    render(
      <LevelSelector
        level="overall"
        onLevelChange={onLevelChange}
        onDimensionChange={onDimensionChange}
      />,
    );

    expect(screen.queryByText("Select Dimension:")).not.toBeInTheDocument();
  });

  it("calls onDimensionChange when a dimension is selected", () => {
    const onLevelChange = vi.fn();
    const onDimensionChange = vi.fn();

    render(
      <LevelSelector
        level="dimension"
        dimension="fundamental"
        onLevelChange={onLevelChange}
        onDimensionChange={onDimensionChange}
      />,
    );

    const technicalButton = screen.getByRole("button", { name: /technical/i });
    technicalButton.click();
    expect(onDimensionChange).toHaveBeenCalledWith("technical");
  });

  it("maintains minimum touch target size (44px) for all interactive elements", () => {
    const onLevelChange = vi.fn();
    const onDimensionChange = vi.fn();

    render(
      <LevelSelector
        level="dimension"
        dimension="fundamental"
        onLevelChange={onLevelChange}
        onDimensionChange={onDimensionChange}
      />,
    );

    const buttons = screen.getAllByRole("button");
    buttons.forEach((button) => {
      expect(button).toHaveClass("min-h-[44px]");
    });
  });
});
