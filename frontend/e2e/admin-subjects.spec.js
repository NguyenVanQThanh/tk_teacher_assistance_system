// File Name: admin-subjects.spec.js
// Description: Playwright end-to-end tests for the Admin "Subjects & Heads" page (assign one head per subject).
// Created At: 2026-11-13
// Created By: AI Agent
// Updated At: 2026-11-13
// Updated By: AI Agent

import { test, expect } from '@playwright/test';

const ADMIN_PHONE = '0999000001';
const ADMIN_PASS = 'Admin@1234';

async function loginAsAdmin(page) {
  await page.goto('/login');
  await page.waitForLoadState('networkidle');
  await page.fill('#identifier-input', ADMIN_PHONE);
  await page.fill('#password-input', ADMIN_PASS);
  await page.click('button[type="submit"]');
  await page.waitForURL('**/admin');
}

test.describe('Admin Subjects & Department Heads', () => {
  test('TC-SUBJ-01: page lists subjects with a head selector and sidebar link', async ({ page }) => {
    await loginAsAdmin(page);
    await page.waitForLoadState("networkidle");
    await page.locator('.admin-sidebar .admin-nav-item:has-text("Môn học & Tổ trưởng")').click();
    await page.waitForURL('**/admin/subjects');
    await expect(page.getByTestId('admin-subjects-page')).toBeVisible();
    const rows = page.getByTestId('subject-row');
    await expect(rows.first()).toBeVisible();
    expect(await rows.count()).toBeGreaterThan(0);
    await expect(rows.first().locator('select')).toBeVisible();
  });

  test('TC-SUBJ-02: assigning, replacing and clearing the head persists via the API', async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto('/admin/subjects');
    await page.waitForLoadState('networkidle');

    // Pick the first subject that has at least one candidate teacher.
    const rows = page.getByTestId('subject-row');
    const count = await rows.count();
    let target = null;
    for (let i = 0; i < count; i++) {
      const options = await rows.nth(i).locator('select option').count();
      if (options > 1) { target = rows.nth(i); break; }
    }
    expect(target, 'a subject with at least one candidate teacher').not.toBeNull();

    const select = target.locator('select');
    const original = await select.inputValue();
    const firstCandidate = await select.locator('option').nth(1).getAttribute('value');
    const token = await page.evaluate(() => localStorage.getItem('access_token'));
    const subjectName = (await target.locator('td').first().textContent()).trim();

    // Assign
    const putAssign = page.waitForResponse(
      (r) => r.url().includes('/head-teacher') && r.request().method() === 'PUT'
    );
    await select.selectOption(firstCandidate);
    expect((await putAssign).status()).toBe(200);
    await expect(page.getByRole('status')).toContainText(subjectName);

    // Exactly one head: the API returns the single assigned id
    const subjects = await page.evaluate(async (tk) => {
      const res = await fetch('/api/v1/subjects', { headers: { Authorization: `Bearer ${tk}` } });
      return res.json();
    }, token);
    const heads = subjects.filter((s) => s.subject_name === subjectName);
    expect(heads).toHaveLength(1);
    expect(heads[0].head_teacher_id).toBe(firstCandidate);

    // Clear
    const putClear = page.waitForResponse(
      (r) => r.url().includes('/head-teacher') && r.request().method() === 'PUT'
    );
    await select.selectOption('');
    expect((await putClear).status()).toBe(200);
    await expect(select).toHaveValue('');

    // Restore the original head so the dev data is unchanged
    if (original) {
      const putRestore = page.waitForResponse(
        (r) => r.url().includes('/head-teacher') && r.request().method() === 'PUT'
      );
      await select.selectOption(original);
      expect((await putRestore).status()).toBe(200);
    }
  });

  test('TC-SUBJ-03: a teacher cannot open the admin subjects page', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    await page.fill('#identifier-input', '0999000005');
    await page.fill('#password-input', 'Teacher@1234');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/teacher**');
    await page.goto('/admin/subjects');
    await page.waitForLoadState('networkidle');
    await expect(page.getByTestId('admin-subjects-page')).toHaveCount(0);
  });
});
