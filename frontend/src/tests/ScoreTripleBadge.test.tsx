import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ScoreTripleBadge } from "@/components/scoring/ScoreTripleBadge";

describe("ScoreTripleBadge (AC5 3-score reference frame)", () => {
  const baseScores = {
    daily: { overall: 62.4, dimensions: {}, sub_dimensions: {}, aspects: {}, sub_aspects: {} },
    hourly: { overall: 63.8, dimensions: {}, sub_dimensions: {}, aspects: {}, sub_aspects: {} },
    current: { overall: 64.2, dimensions: {}, sub_dimensions: {}, aspects: {}, sub_aspects: {} },
  };

  const baseDeltas = {
    hourly_vs_daily: { overall: 1.4, overall_pct: 2.2436, dimensions: {}, sub_dimensions: {}, aspects: {}, sub_aspects: {} },
    current_vs_hourly: { overall: 0.4, overall_pct: 0.6269, dimensions: {}, sub_dimensions: {}, aspects: {}, sub_aspects: {} },
    current_vs_daily: { overall: 1.8, overall_pct: 2.8846, dimensions: {}, sub_dimensions: {}, aspects: {}, sub_aspects: {} },
  };

  it("renders all three frame labels: PREV DAY, PREV HOUR, CURRENT", () => {
    render(<ScoreTripleBadge scores={baseScores} deltas={baseDeltas} />);

    expect(screen.getByText(/PREV DAY/i)).not.toBeNull();
    expect(screen.getByText(/PREV HOUR/i)).not.toBeNull();
    expect(screen.getByText(/CURRENT/i)).not.toBeNull();
  });

  it("renders all three numeric overall scores", () => {
    render(<ScoreTripleBadge scores={baseScores} deltas={baseDeltas} />);

    expect(screen.getByText("62.4")).not.toBeNull();
    expect(screen.getByText("63.8")).not.toBeNull();
    expect(screen.getByText("64.2")).not.toBeNull();
  });

  it("renders UP label for positive delta between CURRENT and PREV DAY", () => {
    render(<ScoreTripleBadge scores={baseScores} deltas={baseDeltas} showDailyDelta />);

    const upTexts = screen.getAllByText(/UP/);
    expect(upTexts.length).toBeGreaterThan(0);
  });

  it("renders DOWN label when CURRENT < PREV HOUR", () => {
    const downDeltas = {
      ...baseDeltas,
      current_vs_hourly: { ...baseDeltas.current_vs_hourly, overall: -0.5, overall_pct: -0.7837 },
    };
    render(<ScoreTripleBadge scores={baseScores} deltas={downDeltas} />);

    const downTexts = screen.getAllByText(/DOWN/);
    expect(downTexts.length).toBeGreaterThan(0);
  });

  it("applies role=group with aria-label for screen readers (WCAG 4.1.2)", () => {
    const { container } = render(<ScoreTripleBadge scores={baseScores} deltas={baseDeltas} />);
    const group = container.querySelector('[role="group"]');
    expect(group).not.toBeNull();
    const label = group!.getAttribute("aria-label");
    expect(label).not.toBeNull();
    expect(label!.length).toBeGreaterThan(0);
  });

  it("respects size variants: sm, md, lg differ in rendered layout", () => {
    const { container: smContainer } = render(
      <ScoreTripleBadge scores={baseScores} deltas={baseDeltas} size="sm" />
    );
    const { container: lgContainer } = render(
      <ScoreTripleBadge scores={baseScores} deltas={baseDeltas} size="lg" />
    );
    const smOuter = smContainer.firstElementChild!;
    const lgOuter = lgContainer.firstElementChild!;
    expect(smOuter.className).not.toEqual(lgOuter.className);
  });

  it("LIVE ring text appears next to CURRENT frame", () => {
    render(<ScoreTripleBadge scores={baseScores} deltas={baseDeltas} />);
    const live = screen.getByText(/LIVE/);
    expect(live).not.toBeNull();
  });
});
