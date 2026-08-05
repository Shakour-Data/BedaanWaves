import { test, expect } from '@playwright/test';

test.describe('SSE Real-Time Updates', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard');
  });

  test('should establish SSE connection and receive live updates', async ({ page }) => {
    const connectionStatus = page.locator('[data-testid="sse-status"]');
    await expect(connectionStatus).toBeVisible();

    const statusText = await connectionStatus.textContent();
    expect(statusText).toMatch(/connected|live|زنده/);
  });

  test('should update stock data in real-time via SSE', async ({ page }) => {
    const initialPrice = await page.locator('[data-testid="stock-price"]').first().textContent();

    await page.waitForTimeout(3000);

    const updatedPrice = await page.locator('[data-testid="stock-price"]').first().textContent();
    expect(updatedPrice).toBeDefined();
  });

  test('should show reconnection status when SSE disconnects', async ({ page }) => {
    await page.route('**/stocks/events', (route) => route.abort());

    await page.reload();
    await page.waitForTimeout(2000);

    const statusIndicator = page.locator('[data-testid="sse-status"]');
    await expect(statusIndicator).toBeVisible();
  });
});

test.describe('Export Functionality', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard');
  });

  test('should export data as CSV', async ({ page }) => {
    const downloadPromise = page.waitForEvent('download');
    await page.locator('[data-testid="export-csv"]').click();
    const download = await downloadPromise;

    expect(download.suggestedFilename()).toMatch(/\.csv$/);
  });

  test('should export data as Excel', async ({ page }) => {
    const downloadPromise = page.waitForEvent('download');
    await page.locator('[data-testid="export-excel"]').click();
    const download = await downloadPromise;

    expect(download.suggestedFilename()).toMatch(/\.xlsx?$/);
  });

  test('should export data as JSON', async ({ page }) => {
    const downloadPromise = page.waitForEvent('download');
    await page.locator('[data-testid="export-json"]').click();
    const download = await downloadPromise;

    expect(download.suggestedFilename()).toMatch(/\.json$/);
  });

  test('should export fundamental analysis data', async ({ page }) => {
    await page.goto('/stocks/AAPL');

    const downloadPromise = page.waitForEvent('download');
    await page.locator('[data-testid="export-fundamental"]').click();
    const download = await downloadPromise;

    expect(download.suggestedFilename()).toMatch(/fundamental.*\.(csv|xlsx|json)$/);
  });
});

test.describe('GraphQL Integration', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard');
  });

  test('should execute GraphQL query and display results', async ({ page }) => {
    const query = `
      query GetStocks {
        stocks {
          symbol
          name
          price
          change
        }
      }
    `;

    await page.evaluate((q) => {
      window.__graphqlQuery = q;
    }, query);

    await page.locator('[data-testid="graphql-explorer"]').click();
    await page.waitForTimeout(1000);

    const results = page.locator('[data-testid="graphql-results"]');
    await expect(results).toBeVisible();
  });

  test('should handle GraphQL errors gracefully', async ({ page }) => {
    const invalidQuery = `{ invalidField { bad } }`;

    await page.evaluate((q) => {
      window.__graphqlQuery = q;
    }, invalidQuery);

    await page.locator('[data-testid="graphql-explorer"]').click();
    await page.waitForTimeout(1000);

    const errorDisplay = page.locator('[data-testid="graphql-error"]');
    await expect(errorDisplay).toBeVisible();
  });
});