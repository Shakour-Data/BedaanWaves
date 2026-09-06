import { chromium, FullConfig } from '@playwright/test';

async function globalSetup(config: FullConfig) {
  console.log('[GlobalSetup] Initializing Playwright E2E test environment...');
  console.log('[GlobalSetup] Using baseURL:', config.projects[0]?.use?.baseURL || process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3005');
  console.log('[GlobalSetup] Done.');
}

export default globalSetup;
