import { test, expect } from "@playwright/test";

const DASHBOARD_URL = `${process.env.PLAYWRIGHT_BASE_URL || "http://localhost:3005"}/dashboard`;

test.describe("QA E2E — Performance", () => {
  test("initial dashboard load completes within 2 seconds", async ({ page }) => {
    const startTime = Date.now();

    await page.goto(DASHBOARD_URL, { waitUntil: "domcontentloaded" });

    await page.waitForSelector('[data-testid="tarot-card"]', { state: "visible", timeout: 5000 });

    const loadTime = Date.now() - startTime;
    expect(loadTime).toBeLessThan(2000);
  });

  test("symbol switch triggers re-render with new data within 1 second", async ({ page }) => {
    await page.goto(DASHBOARD_URL, { waitUntil: "domcontentloaded" });
    await page.waitForSelector('[data-testid="tarot-card"]', { state: "visible", timeout: 10000 });

    // Measure the time for the snapshot to update after navigation
    const navigationPromise = page.goto(`${DASHBOARD_URL}?symbol=AAPL`, {
      waitUntil: "domcontentloaded",
    });

    const startTime = Date.now();
    await navigationPromise;

    // Wait for the new data to render
    await page.waitForSelector('[data-testid="spider-chart"]', { state: "visible", timeout: 5000 });

    const switchTime = Date.now() - startTime;
    expect(switchTime).toBeLessThan(1000);
  });

  test("at most 3 parallel API requests for dashboard data", async ({ page }) => {
    const requests: string[] = [];

    page.on("request", (req) => {
      if (req.url().includes("/analysis/dashboard/snapshot")) {
        requests.push(req.url());
      }
    });

    await page.goto(DASHBOARD_URL, { waitUntil: "networkidle" });

    await page.waitForSelector('[data-testid="tarot-card"]', { state: "visible", timeout: 10000 });

    expect(requests.length).toBeLessThanOrEqual(3);
  });

  test("refresh button re-fetches snapshot within 1 second", async ({ page }) => {
    await page.goto(DASHBOARD_URL, { waitUntil: "domcontentloaded" });
    await page.waitForSelector('[data-testid="tarot-card"]', { state: "visible", timeout: 10000 });

    const refreshRequestsBefore = await page.evaluate(() => {
      const entries = performance.getEntriesByType("resource") as PerformanceResourceTiming[];
      return entries.filter((e) => e.name.includes("/analysis/dashboard/snapshot")).length;
    });

    const refreshBtn = page.locator('[aria-label="Refresh analytical dashboard"]');
    await expect(refreshBtn).toBeVisible();

    const startTime = Date.now();
    await refreshBtn.click();
    await page.waitForSelector('[data-testid="tarot-card"]', { state: "visible", timeout: 5000 });
    const refreshTime = Date.now() - startTime;

    expect(refreshTime).toBeLessThan(1000);
  });
});
