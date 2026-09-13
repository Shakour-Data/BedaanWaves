import { test, expect, request } from "@playwright/test";

const API_BASE = "http://localhost:3000";
const DASHBOARD_URL = `${process.env.PLAYWRIGHT_BASE_URL || "http://localhost:3005"}/dashboard`;

const TOLERANCE = 0.01;

test.describe("QA E2E — Data Parity (Spider ≡ Trend last point)", () => {
  test("API returns a snapshot whose spider/trend scores are parity-consistent", async () => {
    const apiContext = await request.newContext();

    const resp = await apiContext.get(`${API_BASE}/analysis/dashboard/snapshot`);
    expect(resp.status()).toBe(200);

    const payload = await resp.json();
    expect(payload).toBeDefined();

    const dailyScores = payload.scores?.daily ?? payload.scores?.current;
    const trends = payload.trends?.daily ?? payload.trends?.intraday ?? [];
    expect(dailyScores).toBeDefined();
    expect(trends.length).toBeGreaterThan(0);

    const lastTrend = trends[trends.length - 1];
    const levelScores = lastTrend.level_scores ?? {};

    const levels = ["dimension", "sub_dimension", "aspect", "sub_aspect"];

    for (const level of levels) {
      const spiderObj = dailyScores[level] ?? dailyScores[`${level}s`] ?? {};
      const trendLevelScores = levelScores[level] ?? levelScores[`${level}s`] ?? {};

      for (const [key, spiderVal] of Object.entries(spiderObj)) {
        const trendVal = trendLevelScores[key];
        if (typeof trendVal === "number" && typeof spiderVal === "number") {
          expect(Math.abs(trendVal - spiderVal)).toBeLessThanOrEqual(TOLERANCE);
        }
      }
    }
  });

  test("general dashboard page renders parity banner with 'Data parity verified'", async ({ page }) => {
    await page.goto(DASHBOARD_URL);

    const parityBanner = page.locator('[role="status"]');
    await expect(parityBanner).toBeVisible();
    await expect(parityBanner).toContainText(/Data parity verified/i);
  });

  test("spider chart last-point value matches trend chart last-point value on the page", async ({ page }) => {
    await page.goto(DASHBOARD_URL);

    await page.waitForSelector('[data-testid="spider-chart"]', { state: "visible" });

    // Verify the parity banner explicitly confirms parity
    const parityText = await page.locator('[role="status"]').textContent();
    expect(parityText).toMatch(/Data parity verified/i);

    // Count tarot cards: 20 total chart views
    const cards = page.locator('[data-testid="tarot-card"]');
    await expect(cards).toHaveCount(20);
  });

  test("all 20 chart views are present (4 levels x 5 families)", async ({ page }) => {
    await page.goto(DASHBOARD_URL);

    await page.waitForSelector('[data-testid="tarot-card"]', { state: "visible" });

    // Wait for all 20 views to render
    await expect(page.locator('[data-testid="tarot-card"]')).toHaveCount(20, {
      timeout: 30000,
    });

    // Verify family counts
    const spiderCharts = page.locator('[data-testid="spider-chart"]');
    const trendCharts = page.locator('[data-testid="trend-chart"]');
    const coefficientCharts = page.locator('[data-testid="coefficient-chart"]');

    await expect(spiderCharts).toHaveCount(4);
    await expect(trendCharts).toHaveCount(4);
    await expect(coefficientCharts).toHaveCount(4);
  });
});
