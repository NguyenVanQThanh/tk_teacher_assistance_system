// File Name: playwright.config.js
// Description: Playwright test configuration for teacher portal end-to-end automation.
// Created At: 2026-10-07
// Created By: Tam Khang
// Updated At: 2026-10-07
// Updated By: Tam Khang

import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  timeout: 45000,
  expect: {
    timeout: 10000
  },
  fullyParallel: false,
  workers: 1, // Single worker to avoid DB race conditions during e2e testing
  retries: 0,
  reporter: [
    ['list'],
    ['html', { outputFolder: 'playwright-report', open: 'never' }]
  ],
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'off',
    headless: true
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
