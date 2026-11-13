// File Name: admin-user-import.spec.js
// Description: Playwright test for admin bulk user import (template download, CSV import, per-row errors).
// Created At: 2026-11-14
// Created By: AI Agent
// Updated At: 2026-11-14
// Updated By: AI Agent

import { test, expect } from '@playwright/test';

test('TC-IMPORT-01: download template, import CSV, see per-row errors', async ({ page }) => {
  await page.goto('/login');
  await page.waitForLoadState('networkidle');
  await page.fill('#identifier-input', '0999000001');
  await page.fill('#password-input', 'Admin@1234');
  await page.click('button[type="submit"]');
  await page.waitForURL('**/admin');
  await page.goto('/admin/users');
  await page.waitForLoadState('networkidle');

  await page.locator('.btn-sync-import-excel').click();
  const dl = page.waitForEvent('download');
  await page.getByTestId('download-template-xlsx').click();
  expect((await dl).suggestedFilename()).toBe('user_import_template.xlsx');

  const phone = `09${String(Date.now()).slice(-8)}`;
  const csv = `full_name,role,phone\nNguyen Import Test,Student,${phone}\nBad Role,Wizard,\n`;
  await page.locator('#excel-file-input').setInputFiles({ name: 'u.csv', mimeType: 'text/csv', buffer: Buffer.from(csv) });
  const result = page.getByTestId('import-result');
  await expect(result).toContainText('Thành công: 1');
  await expect(page.getByTestId('import-errors')).toContainText('Wizard');
  await expect(page.getByTestId('download-passwords')).toBeVisible();
});
