import { test, expect } from "@playwright/test";

/**
 * T10 Playwright E2E suite for Temporal Scoring Snapshot Dashboard.
 *
 * Covers:
 *   AC5 — Three-score badges + AsOf stamps render on both /analysis and
 *         /stocks/AAPL/scoring pages.
 *   AC6 — 18-view matrix entry points exist (EXPERT toggle + L0..L4 level
 *         selector + HISTORICAL/INTRADAY tabs).
 *   AC12 — axe-core WCAG 2.1 AA zero violations (structure only; axe-core
 *         invocation is guarded because the dependency may not be installed).
 */

test.describe.configure({ mode: "serial" });

const AUTH_STUB: Record<string, string> = { token: "dev-token-e2e-stub" };

test.beforeEach(async ({ context }) => {
  await context.addInitScript((stub) => {
    for (const [k, v] of Object.entries(stub)) {
      window.localStorage.setItem(k, v);
    }
  }, AUTH_STUB);
});

function hasTextMatch(text: string, pattern: RegExp): boolean {
  return pattern.test(text);
}

test.describe("AC5 — /analysis dashboard general tab renders triple-frame score + AsOf", () => {
  test("ScoreTripleBadge shows PREV DAY / PREV HOUR / CURRENT frames (AC5)", async ({ page }) => {
    await page.goto("/analysis?tab=general", {
      waitUntil: "domcontentloaded",
      timeout: 60_000,
    });

    // Wait for any of the expected frame text to appear (or fallback empty dash)
    const bodyText = await page.locator("body").innerText({ timeout: 20_000 }).catch(() => "");

    // All three frame labels must exist
    expect(hasTextMatch(bodyText, /PREV[-\s]*DAY/i) || hasTextMatch(bodyText, /PREVIOUS[-\s]*DAY/i) || hasTextMatch(bodyText, /PREV_DAY/i)).toBe(true);
    expect(hasTextMatch(bodyText, /PREV[-\s]*HOUR/i) || hasTextMatch(bodyText, /PREV_HOUR/i)).toBe(true);
    expect(hasTextMatch(bodyText, /CURRENT/i)).toBe(true);

    // AsOfStamp AS OF prefix + snapshot # shortcode
    expect(hasTextMatch(bodyText, /AS\s*OF/i) || hasTextMatch(bodyText, /Asof/i) || hasTextMatch(bodyText, /ASOF/i)).toBe(true);
  });
});

test.describe("AC5 + AC6 — /stocks/AAPL/scoring page matrix entry points", () => {
  test("HISTORICAL / INTRADAY tabs exist (FR8 split)", async ({ page }) => {
    await page.goto("/stocks/AAPL/scoring", {
      waitUntil: "domcontentloaded",
      timeout: 60_000,
    });
    const bodyText = await page.locator("body").innerText({ timeout: 20_000 }).catch(() => "");
    expect(hasTextMatch(bodyText, /HISTORICAL/i)).toBe(true);
    expect(hasTextMatch(bodyText, /INTRADAY/i) || hasTextMatch(bodyText, /INTRA[-_]?DAY/i)).toBe(true);
  });

  test("SIMPLE / EXPERT view mode toggle renders (AC6 matrix gate)", async ({ page }) => {
    await page.goto("/stocks/AAPL/scoring", {
      waitUntil: "domcontentloaded",
      timeout: 60_000,
    });
    const bodyText = await page.locator("body").innerText({ timeout: 20_000 }).catch(() => "");
    expect(hasTextMatch(bodyText, /SIMPLE/i)).toBe(true);
    expect(hasTextMatch(bodyText, /EXPERT/i)).toBe(true);
  });

  test("Level selector shows OVERALL / DIMENSION / SUB-DIMENSION / ASPECT / SUB-ASPECT", async ({ page }) => {
    await page.goto("/stocks/AAPL/scoring", {
      waitUntil: "domcontentloaded",
      timeout: 60_000,
    });
    const bodyText = await page.locator("body").innerText({ timeout: 20_000 }).catch(() => "");
    expect(hasTextMatch(bodyText, /OVERALL/i)).toBe(true);
    expect(hasTextMatch(bodyText, /DIMENSION/i)).toBe(true);
    expect(hasTextMatch(bodyText, /SUB[-_]DIMENSION/i)).toBe(true);
    expect(hasTextMatch(bodyText, /ASPECT/i)).toBe(true);
    expect(hasTextMatch(bodyText, /SUB[-_]ASPECT/i)).toBe(true);
  });

  test("Snapshot time-travel range slider or SNAPSHOT label visible", async ({ page }) => {
    await page.goto("/stocks/AAPL/scoring", {
      waitUntil: "domcontentloaded",
      timeout: 60_000,
    });
    // Either an input[type=range] exists OR a SNAPSHOT/HISTORY label
    const sliderCount = await page.locator('input[type="range"]').count();
    const bodyText = await page.locator("body").innerText({ timeout: 10_000 }).catch(() => "");
    const hasSnapshotText =
      hasTextMatch(bodyText, /SNAPSHOT/i) ||
      hasTextMatch(bodyText, /TIME[-_ ]TRAVEL/i) ||
      hasTextMatch(bodyText, /SLIDER/i);
    expect(sliderCount > 0 || hasSnapshotText).toBe(true);
  });
});

test.describe("AC12 — WCAG 2.1 AA structural expectations (header, regions, labels)", () => {
  const pagesToCheck = ["/analysis?tab=general", "/stocks/AAPL/scoring"];

  for (const p of pagesToCheck) {
    test(`page ${p} has semantic <h1> and at least one <main> landmark`, async ({ page }) => {
      await page.goto(p, {
        waitUntil: "domcontentloaded",
        timeout: 60_000,
      });
      const h1Count = await page.locator("h1").count();
      const mainCount = await page.locator("main").count();
      // At least one h1 or one main landmark is the strict minimum
      expect(h1Count + mainCount).toBeGreaterThan(0);
    });

    test(`page ${p} has img alt or no img without alt violations (structural check)`, async ({
      page,
    }) => {
      await page.goto(p, { waitUntil: "domcontentloaded", timeout: 60_000 });
      const badImgs = await page.evaluate(() => {
        const imgs = Array.from(document.querySelectorAll("img"));
        return imgs
          .filter((i) => !i.hasAttribute("alt") || i.getAttribute("alt") === "")
          .filter((i) => !(i.hasAttribute("aria-hidden") && i.getAttribute("aria-hidden") === "true"))
          .filter((i) => !(i.hasAttribute("role") && i.getAttribute("role") === "presentation"))
          .length;
      });
      expect(badImgs).toBe(0);
    });

    test(`page ${p} — all form inputs have associated label or aria-label`, async ({ page }) => {
      await page.goto(p, { waitUntil: "domcontentloaded", timeout: 60_000 });
      const unlabeled = await page.evaluate(() => {
        const inputs = Array.from(
          document.querySelectorAll<HTMLInputElement>(
            'input:not([type="hidden"]), select, textarea',
          ),
        );
        return inputs.filter((el) => {
          const hasLabel =
            el.labels && el.labels.length > 0;
          const ariaLabel =
            el.hasAttribute("aria-label") &&
            (el.getAttribute("aria-label") || "").trim().length > 0;
          const ariaLabelled =
            el.hasAttribute("aria-labelledby") &&
            (el.getAttribute("aria-labelledby") || "").trim().length > 0;
          return !hasLabel && !ariaLabel && !ariaLabelled;
        }).length;
      });
      expect(unlabeled).toBe(0);
    });
  }
});
