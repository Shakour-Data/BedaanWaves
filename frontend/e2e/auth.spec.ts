import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
  });

  test('should display login form', async ({ page }) => {
    await expect(page.locator('h1, h2')).toContainText(/login|sign in/i);
    await expect(page.locator('input[type="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test('should show validation errors for empty fields', async ({ page }) => {
    await page.locator('button[type="submit"]').click();
    await expect(page.locator('text=email|text=password')).toBeVisible();
  });

  test('should navigate to leaderboard after successful login', async ({ page }) => {
    await page.locator('input[type="email"]').fill('test@example.com');
    await page.locator('input[type="password"]').fill('password123');
    await page.locator('button[type="submit"]').click();

    await page.waitForURL('/leaderboard');
    await expect(page.locator('text=Leaderboard')).toBeVisible();
  });

  test('should show error message for invalid credentials', async ({ page }) => {
    await page.locator('input[type="email"]').fill('wrong@example.com');
    await page.locator('input[type="password"]').fill('wrongpassword');
    await page.locator('button[type="submit"]').click();

    await expect(page.locator('text=invalid|text=error|text=credential')).toBeVisible();
  });
});

test.describe('Leaderboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/leaderboard');
  });

  test('should load leaderboard with top performers', async ({ page }) => {
    await expect(page.locator('text=Leaderboard')).toBeVisible();
  });

  test('should display ranked entries', async ({ page }) => {
    await expect(page.locator('text=Top Performers')).toBeVisible();
  });

  test('should have filterable levels', async ({ page }) => {
    await expect(page.locator('text=Overall')).toBeVisible();
  });
});