/**
 * Playwright Configuration for E2E Testing
 * ---------------------------------------------------------------------------
 * End-to-end test configuration for BedaanWaves platform.
 * 
 * FEATURES:
 * - Multi-browser testing (Chromium, Firefox, WebKit)
 * - Mobile viewport testing
 * - Parallel test execution
 * - Screenshot and video capture on failure
 * - HTML report generation
 * 
 * USAGE:
 *   npx playwright test                    # Run all tests
 *   npx playwright test --headed          # Run in headed mode
 *   npx playwright test --ui              # Run with UI
 *   npx playwright test --debug           # Run in debug mode
 *   npx playwright show-report            # Show HTML report
 */

import { defineConfig, devices } from '@playwright/test';
import path from 'path';

// Configuration
const BASE_URL = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3005';
const IS_CI = process.env.CI === 'true';
const WORKERS = IS_CI ? 1 : 4;
const RETRIES = IS_CI ? 2 : 0;

export default defineConfig({
  // Test directory
  testDir: './e2e',
  
  // Test match patterns
  testMatch: [
    '**/*.spec.ts',
    '**/*.test.ts',
  ],
  
  // Global setup/teardown
  globalSetup: require.resolve('./e2e/setup/global-setup.ts'),
  globalTeardown: require.resolve('./e2e/setup/global-teardown.ts'),
  
  // Parallel execution
  fullyParallel: true,
  workers: WORKERS,
  
  // Retries
  retries: RETRIES,
  
  // Timeout settings
  timeout: 30000,
  expect: {
    timeout: 5000,
  },
  
  // Reporters
  reporter: [
    ['list'],
    ['html', { 
      outputFolder: 'playwright-report',
      open: !IS_CI ? 'on-failure' : 'never',
    }],
    ['junit', { 
      outputFile: 'playwright-report/junit.xml',
    }],
    ...(IS_CI ? [['github']] : []),
  ],
  
  // Shared settings for all projects
  use: {
    // Base URL
    baseURL: BASE_URL,
    
    // Viewport
    viewport: { width: 1280, height: 720 },
    
    // Screenshots
    screenshot: 'only-on-failure',
    
    // Videos
    video: 'on-first-retry',
    
    // Traces
    trace: 'on-first-retry',
    
    // Action timeout
    actionTimeout: 10000,
    
    // Navigation timeout
    navigationTimeout: 15000,
    
    // Permissions
    permissions: [],
    
    // Locale
    locale: 'en-US',
    
    // Timezone
    timezoneId: 'America/New_York',
    
    // JavaScript enabled
    javaScriptEnabled: true,
    
    // Bypass CSP
    bypassCSP: false,
    
    // Ignore HTTPS errors (for development only)
    ignoreHTTPSErrors: true,
    
    // Accept downloads
    acceptDownloads: true,
  },
  
  // Project configurations for different browsers and viewports
  projects: [
    // ==========================================
    // Desktop Chromium
    // ==========================================
    {
      name: 'chromium',
      use: {
        browserName: 'chromium',
        channel: 'chromium',
      },
    },
    
    // Desktop Chromium (dark mode)
    {
      name: 'chromium-dark',
      use: {
        browserName: 'chromium',
        colorScheme: 'dark',
      },
    },
    
    // ==========================================
    // Desktop Firefox
    // ==========================================
    {
      name: 'firefox',
      use: {
        browserName: 'firefox',
        launchOptions: {
          firefoxUserPrefs: {
            'devtools.chrome.enabled': true,
            'devtools.debugger.remote-enabled': true,
          },
        },
      },
    },
    
    // ==========================================
    // Desktop WebKit (Safari)
    // ==========================================
    {
      name: 'webkit',
      use: {
        browserName: 'webkit',
      },
    },
    
    // ==========================================
    // Mobile Viewports
    // ==========================================
    {
      name: 'mobile-chromium',
      use: {
        browserName: 'chromium',
        ...devices['Pixel 5'],
      },
    },
    {
      name: 'mobile-webkit',
      use: {
        browserName: 'webkit',
        ...devices['iPhone 14'],
      },
    },
    
    // ==========================================
    // Tablet Viewports
    // ==========================================
    {
      name: 'tablet-chromium',
      use: {
        browserName: 'chromium',
        ...devices['iPad Pro 11'],
      },
    },
    
    // ==========================================
    // CI-specific configurations
    // ==========================================
    ...(IS_CI ? [
      {
        name: 'ci-chromium',
        use: {
          browserName: 'chromium',
          viewport: { width: 1280, height: 720 },
        },
      },
    ] : []),
  ],
  
  // Web server configuration for local testing
  webServer: {
    command: 'npm run dev',
    url: BASE_URL,
    timeout: 120 * 1000,  // 120 seconds
    reuseExistingServer: !IS_CI,
    env: {
      NODE_ENV: 'test',
    },
  },
  
  // Output directory
  outputDir: 'playwright-output',
  
  // Preserve output files
  preserveOutput: 'failures-only',
  
  // Update snapshots
  updateSnapshots: IS_CI ? 'none' : 'missing',
  
  // Snapshot path template
  snapshotPathTemplate: '{testDir}/__snapshots__/{testFilePath}/{arg}{ext}',
  
  // Test ignore patterns
  testIgnore: [
    '**/node_modules/**',
    '**/.next/**',
    '**/playwright-output/**',
    '**/playwright-report/**',
  ],
  
  // Quiet mode
  quiet: false,
  
  // Debug mode
  debug: false,
};
