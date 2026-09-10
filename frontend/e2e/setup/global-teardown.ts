export default async function globalTeardown() {
  console.log('[GlobalTeardown] Cleaning up Playwright E2E test environment...');
  console.log('[GlobalTeardown] Done.');
}
