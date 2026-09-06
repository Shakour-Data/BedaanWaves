import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { AsOfStamp } from "@/components/scoring/AsOfStamp";

describe("AsOfStamp (AC5 as-of timestamp + snapshotId shortcode)", () => {
  it("renders AS OF prefix plus full UTC timestamp", () => {
    render(
      <AsOfStamp
        effectiveAt="2026-09-06T14:30:00Z"
        snapshotId="snap_01H7XYZ123ABC456DEF789GHI0"
      />
    );
    expect(screen.getByText(/AS OF/)).not.toBeNull();
    expect(screen.getByText(/2026-09-06/)).not.toBeNull();
    expect(screen.getByText(/14:30/)).not.toBeNull();
  });

  it("renders snapshotId shortcode prefixed with #", () => {
    render(
      <AsOfStamp
        effectiveAt="2026-09-06T14:30:00Z"
        snapshotId="snap_01H7XYZ123ABC456DEF789GHI0"
      />
    );
    const shortcode = screen.getByText(/#snap_01/);
    expect(shortcode).not.toBeNull();
  });

  it("applies aria-live=polite for accessibility (WCAG 4.1.3 Status Messages)", () => {
    const { container } = render(
      <AsOfStamp
        effectiveAt="2026-09-06T14:30:00Z"
        snapshotId="snap_01H7XYZ123ABC456DEF789GHI0"
      />
    );
    const live = container.querySelector('[aria-live="polite"]');
    expect(live).not.toBeNull();
  });

  it("renders loading state when effectiveAt is null", () => {
    render(<AsOfStamp effectiveAt={null} snapshotId={null} loading />);
    // Loading should NOT render any real timestamp
    expect(screen.queryByText(/AS OF/)).toBeNull();
    // Loading state renders a known neutral placeholder
    const loadingEl = screen.getByText(/LOADING/);
    expect(loadingEl).not.toBeNull();
  });

  it("renders STALE indicator when stale is true", () => {
    render(
      <AsOfStamp
        effectiveAt="2026-09-05T00:00:00Z"
        snapshotId="stale_snap"
        stale
      />
    );
    const stale = screen.getByText(/STALE/);
    expect(stale).not.toBeNull();
  });

  it("supports compact and emphasis variants with different classNames", () => {
    const { container: def } = render(
      <AsOfStamp effectiveAt="2026-09-06T12:00:00Z" snapshotId="abc" variant="default" />
    );
    const { container: comp } = render(
      <AsOfStamp effectiveAt="2026-09-06T12:00:00Z" snapshotId="abc" variant="compact" />
    );
    const { container: emph } = render(
      <AsOfStamp effectiveAt="2026-09-06T12:00:00Z" snapshotId="abc" variant="emphasis" />
    );
    expect(def.firstElementChild!.className).not.toEqual(comp.firstElementChild!.className);
    expect(comp.firstElementChild!.className).not.toEqual(emph.firstElementChild!.className);
  });

  it("no-data state when both effectiveAt and snapshotId are null and loading=false", () => {
    render(<AsOfStamp effectiveAt={null} snapshotId={null} />);
    const noData = screen.getByText(/NO DATA/);
    expect(noData).not.toBeNull();
  });
});
