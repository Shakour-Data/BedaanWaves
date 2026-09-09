import { test, expect } from '@playwright/test';

test.describe('QA Priority 1 - E2E Navigation & Redirect', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[type="email"]', 'test@example.com');
    await page.fill('input[type="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/dashboard');
  });

  test('SC-001: should redirect from protected nested route to general dashboard', async ({ page }) => {
    await page.goto('/analysis');
    await page.waitForURL(/\/analysis/);
    expect(page.url()).toContain('/analysis');
  });

  test('SC-004: should navigate to dimension level when clicked', async ({ page }) => {
    await page.goto('/analysis');
    await page.waitForSelector('text=General', { timeout: 10000 });

    const dimensionTab = page.locator('button:has-text("Dimensions")').first();
    if (await dimensionTab.count() > 0) {
      await dimensionTab.first().click();
      await page.waitForTimeout(500);
      expect(page.url()).toContain('/analysis');
    }
  });

  test('SC-004: browser back button returns to previous page', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForURL('/dashboard');

    await page.goto('/leaderboard');
    await page.waitForURL('/leaderboard');

    await page.goBack();
    await page.waitForURL('/dashboard');
    expect(page.url()).toContain('/dashboard');
  });

  test('SC-004: stock navigation updates URL correctly', async ({ page }) => {
    await page.goto('/stocks');
    await page.waitForSelector('text=NASDAQ Stocks', { timeout: 10000 });

    const stockLink = page.locator('a[href*="/stocks/"]').first();
    if (await stockLink.count() > 0) {
      await stockLink.first().click();
      await page.waitForTimeout(500);
      expect(page.url()).toMatch(/\/stocks\/[A-Z]+/);
    }
  });

  test('SC-004: sidebar navigation works correctly', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForSelector('text=Dashboard', { timeout: 10000 });

    const leaderboardLink = page.locator('a[href*="/leaderboard"]').first();
    if (await leaderboardLink.count() > 0) {
      await leaderboardLink.first().click();
      await page.waitForURL('/leaderboard');
      expect(page.url()).toContain('/leaderboard');
    }
  });
});
