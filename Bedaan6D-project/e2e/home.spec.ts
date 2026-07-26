import { expect, test } from '@playwright/test';

test.describe('Bedaan6D E2E', () => {
  test('shows landing page core content', async ({ page }) => {
    await page.goto('/', { waitUntil: 'networkidle' });

    await expect(page.getByText('بازار بورس را')).toBeVisible();
    await expect(page.getByRole('button', { name: 'ورود به پلتفرم' })).toBeVisible();
    await expect(page.getByText('تحلیل چندبعدی، تصمیم هوشمند')).toBeVisible();
    await expect(page.getByRole('button', { name: 'ورود به داشبورد تحلیلی' })).toBeVisible();
  });

  test('opens and closes scientific references modal from landing page', async ({ page }) => {
    await page.goto('/', { waitUntil: 'networkidle' });

    await page.getByRole('button', { name: 'مراجع علمی' }).click();
    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible();
    await expect(dialog.getByRole('button', { name: 'باز کردن تحلیل تکنیکال' })).toBeVisible();

    await page.getByTestId('references-close-top').click();
    await expect(page.getByRole('dialog')).toHaveCount(0);
  });

  test('downloads the project archive from landing page', async ({ page }) => {
    await page.goto('/', { waitUntil: 'networkidle' });

    const downloadPromise = page.waitForEvent('download');
    await page.getByRole('button', { name: 'دانلود پروژه' }).click();
    const download = await downloadPromise;

    expect(download.suggestedFilename()).toBe('Bedaan6D-project.zip');
  });

  test('opens symbol detail dialog from dashboard', async ({ page }) => {
    await page.goto('/?view=dashboard', { waitUntil: 'networkidle' });

    await page.waitForFunction(() => document.body.textContent?.includes('امتیاز کلی بازار'));
    await page.getByTestId('top-gainer-0').click();

    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible();
    await expect(dialog.getByText('قیمت')).toBeVisible();
    await expect(dialog.getByText('حجم معاملات')).toBeVisible();
    await expect(dialog.getByText('امتیاز کلی')).toBeVisible();
  });

  test('shows offline fallback state when market APIs fail', async ({ page }) => {
    await page.route('**/api/market', (route) => route.abort());
    await page.route('**/api/indices', (route) => route.abort());
    await page.route('**/api/news', (route) => route.abort());
    await page.route('**/api/gold-currency', (route) => route.abort());

    await page.goto('/?view=dashboard', { waitUntil: 'networkidle' });

    await expect(page.getByText('حالت آفلاین')).toBeVisible();
    await expect(page.getByText('صعودی‌ترین نمادها')).toBeVisible();
    await expect(page.getByText('اخبار بازار')).toBeVisible();
  });

  test('enters dashboard and opens scientific roadmap', async ({ page }) => {
    await page.goto('/?view=dashboard', { waitUntil: 'networkidle' });

    await page.waitForFunction(() => document.body.textContent?.includes('امتیاز کلی بازار'));
    await expect(page.getByText('امتیاز کلی بازار')).toBeVisible();
    await expect(page.getByText('صعودی‌ترین نمادها')).toBeVisible();

    await page.getByRole('button', { name: 'نقشه راه علمی' }).click();
    await expect(page.getByRole('dialog')).toBeVisible();
    await expect(page.getByText('نقشه راه علمی Bedaan6D')).toBeVisible();
  });
});
