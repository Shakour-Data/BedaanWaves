import { defineConfig } from '@playwright/test';

const BASE_URL = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3005';
const IS_CI = process.env.CI === 'true';
const WORKERS = IS_CI ? 1 : 4;
const RETRIES = IS_CI ? 2 : 0;

export default defineConfig({
  testDir: './e2e',
  testMatch: ['**/*.spec.ts', '**/*.test.ts'],
  globalSetup: './e2e/setup/global-setup.ts',
  globalTeardown: './e2e/setup/global-teardown.ts',
  fullyParallel: true,
  workers: WORKERS,
  retries: RETRIES,
  timeout: 300000,
  expect: { timeout: 10000 },
  reporter: [
    ['list'],
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
  ],
  use: {
    baseURL: BASE_URL,
    viewport: { width: 1280, height: 720 },
    screenshot: 'only-on-failure',
    video: 'on-first-retry',
    trace: 'on-first-retry',
    actionTimeout: 15000,
    navigationTimeout: 60000,
    locale: 'en-US',
    timezoneId: 'America/New_York',
    javaScriptEnabled: true,
    bypassCSP: false,
    ignoreHTTPSErrors: true,
    acceptDownloads: true,
  },
  projects: [
    {
      name: 'chromium',
      use: {
        browserName: 'chromium',
      },
    },
  ],
  webServer: IS_CI ? {
    command: 'npm run dev',
    url: BASE_URL,
    timeout: 120000,
    reuseExistingServer: true,
    env: { NODE_ENV: 'test' },
  } : undefined,
  outputDir: 'playwright-output',
  preserveOutput: 'failures-only',
  updateSnapshots: IS_CI ? 'none' : 'missing',
  snapshotPathTemplate: '{testDir}/__snapshots__/{testFilePath}/{arg}{ext}',
  testIgnore: [
    '**/node_modules/**',
    '**/.next/**',
    '**/playwright-output/**',
    '**/playwright-report/**',
  ],
  quiet: false,
  debug: false,
});
