import { FullConfig } from '@playwright/test';

async function globalTeardown(config: FullConfig) {
  console.log('[GlobalTeardown] Cleaning up Playwright E2E test environment...');
  console.log('[GlobalTeardown] Done.');
}

export default globalTeardown;
