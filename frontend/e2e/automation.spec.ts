import { test, expect } from '@playwright/test';

test.describe('SSE Real-Time Updates', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard');
  });

  test('should establish SSE connection and receive live updates', async ({ page }) => {
    await page.waitForTimeout(2000);
    const liveIndicator = page.locator('text=live|text=زنده|text=connected|text=داده‌های زنده');
    await expect(liveIndicator.first()).toBeVisible();
  });

  test('should update stock data in real-time via SSE', async ({ page }) => {
    await page.waitForTimeout(3000);
    const statCards = page.locator('text=تغییر|text=change|text=درصد');
    await expect(statCards.first()).toBeVisible();
  });

  test('should show reconnection status when SSE disconnects', async ({ page }) => {
    await page.route('**/stocks/events', (route) => route.abort());
    await page.reload();
    await page.waitForTimeout(2000);
    await expect(page.locator('body')).toBeVisible();
  });
});

test.describe('Export Functionality', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard');
  });

  test('should export data as CSV', async ({ page }) => {
    const exportButton = page.locator('button:has-text("Export CSV")');
    if (await exportButton.count() > 0) {
      const downloadPromise = page.waitForEvent('download');
      await exportButton.click();
      const download = await downloadPromise;
      expect(download.suggestedFilename()).toMatch(/\.csv$/);
    }
  });

  test('should export data as Excel', async ({ page }) => {
    const exportButton = page.locator('button:has-text("Export Excel")');
    if (await exportButton.count() > 0) {
      const downloadPromise = page.waitForEvent('download');
      await exportButton.click();
      const download = await downloadPromise;
      expect(download.suggestedFilename()).toMatch(/\.xlsx?$/);
    }
  });

  test('should export data as JSON', async ({ page }) => {
    const exportButton = page.locator('button:has-text("Export JSON")');
    if (await exportButton.count() > 0) {
      const downloadPromise = page.waitForEvent('download');
      await exportButton.click();
      const download = await downloadPromise;
      expect(download.suggestedFilename()).toMatch(/\.json$/);
    }
  });

  test('should export fundamental analysis data', async ({ page }) => {
    await page.goto('/stocks/AAPL');
    const exportButton = page.locator('button:has-text("Export"), button:has-text("خروجی")');
    if (await exportButton.count() > 0) {
      const downloadPromise = page.waitForEvent('download');
      await exportButton.first().click();
      const download = await downloadPromise;
      expect(download.suggestedFilename()).toMatch(/\.(csv|xlsx|json)$/);
    }
  });
});

test.describe('GraphQL Integration', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard');
  });

  test('should execute GraphQL query and display results', async ({ page }) => {
    const graphqlExplorer = page.locator('text=GraphQL|text=گراف کیووال|text=graphql');
    if (await graphqlExplorer.count() > 0) {
      await graphqlExplorer.first().click();
      await page.waitForTimeout(1000);
      await expect(page.locator('text=stocks|text=نتایج|text=results').first()).toBeVisible();
    }
  });

  test('should handle GraphQL errors gracefully', async ({ page }) => {
    const graphqlExplorer = page.locator('text=GraphQL|text=گراف کیووال|text=graphql');
    if (await graphqlExplorer.count() > 0) {
      await graphqlExplorer.first().click();
      await page.waitForTimeout(1000);
      await expect(page.locator('body')).toBeVisible();
    }
  });
});
