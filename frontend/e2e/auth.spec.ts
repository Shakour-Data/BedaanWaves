import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
  });

  test('should display login form', async ({ page }) => {
    await expect(page.locator('h1')).toContainText(/login|sign in/i);
    await expect(page.locator('input[type="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test('should show validation errors for empty fields', async ({ page }) => {
    await page.locator('button[type="submit"]').click();
    await expect(page.locator('text=email|text=password')).toBeVisible();
  });

  test('should navigate to dashboard after successful login', async ({ page }) => {
    await page.locator('input[type="email"]').fill('test@example.com');
    await page.locator('input[type="password"]').fill('password123');
    await page.locator('button[type="submit"]').click();

    await page.waitForURL('/dashboard');
    await expect(page.locator('[data-testid="dashboard"]')).toBeVisible();
  });

  test('should show error message for invalid credentials', async ({ page }) => {
    await page.locator('input[type="email"]').fill('wrong@example.com');
    await page.locator('input[type="password"]').fill('wrongpassword');
    await page.locator('button[type="submit"]').click();

    await expect(page.locator('text=invalid|text=error|text=credential')).toBeVisible();
  });
});

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard');
  });

  test('should load dashboard with market stats', async ({ page }) => {
    await expect(page.locator('[data-testid="market-stats"]')).toBeVisible();
    const statCards = page.locator('[data-testid="stat-card"]');
    await expect(statCards.first()).toBeVisible();
  });

  test('should display asset table', async ({ page }) => {
    await expect(page.locator('[data-testid="asset-table"]')).toBeVisible();
  });

  test('should display signal list', async ({ page }) => {
    await expect(page.locator('[data-testid="signal-list"]')).toBeVisible();
  });

  test('should display news feed', async ({ page }) => {
    await expect(page.locator('[data-testid="news-list"]')).toBeVisible();
  });

  test('should have live data indicator', async ({ page }) => {
    const liveIndicator = page.locator('text=live|text=زنده|text=connected');
    await expect(liveIndicator.first()).toBeVisible();
  });
});