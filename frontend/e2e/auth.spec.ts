import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
  });

  test('should display login form', async ({ page }) => {
    await expect(page.locator('h1, h2')).toContainText(/login|sign in|ورود/i);
    await expect(page.locator('input[type="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test('should show validation errors for empty fields', async ({ page }) => {
    await page.locator('button[type="submit"]').click();
    await expect(page.locator('text=email|text=password|text=ایمیل|text=رمز')).toBeVisible();
  });

  test('should navigate to dashboard after successful login', async ({ page }) => {
    await page.locator('input[type="email"]').fill('test@example.com');
    await page.locator('input[type="password"]').fill('password123');
    await page.locator('button[type="submit"]').click();

    await page.waitForURL('/dashboard');
    await expect(page.locator('text=داشبورد|text=Dashboard')).toBeVisible();
  });

  test('should show error message for invalid credentials', async ({ page }) => {
    await page.locator('input[type="email"]').fill('wrong@example.com');
    await page.locator('input[type="password"]').fill('wrongpassword');
    await page.locator('button[type="submit"]').click();

    await expect(page.locator('text=invalid|text=error|text=credential|text=خطا|text=ناموفق')).toBeVisible();
  });
});

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard');
  });

  test('should load dashboard with market stats', async ({ page }) => {
    await expect(page.locator('text=شاخص|text=بازار|text=Market')).toBeVisible();
  });

  test('should display asset table', async ({ page }) => {
    await expect(page.locator('table, .overflow-x-auto')).toBeVisible();
  });

  test('should display news feed', async ({ page }) => {
    await expect(page.locator('text=اخبار|text=News')).toBeVisible();
  });

  test('should have live data indicator', async ({ page }) => {
    const liveIndicator = page.locator('text=live|text=زنده|text=connected|text=داده‌های زنده');
    await expect(liveIndicator.first()).toBeVisible();
  });
});
