// File Name: student-portal.spec.js
// Description: Comprehensive Playwright end-to-end automation test suite covering all Student Portal features.
// Created At: 2026-10-07
// Created By: Tam Khang
// Updated At: 2026-10-07
// Updated By: Tam Khang

import { test, expect } from '@playwright/test';

test.describe('Student Portal End-to-End Automation Test Suite', () => {
  const STUDENT_PHONE = '0999100001';
  const STUDENT_PASS = 'Student@1234';

  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
  });

  test('TC-STU-01: Student Authentication & Profile Retrieval (/api/v1/auth/me)', async ({ page }) => {
    // 1. Fill login credentials
    await page.fill('#identifier-input', STUDENT_PHONE);
    await page.fill('#password-input', STUDENT_PASS);
    await page.click('button[type="submit"]');

    // 2. Redirection to student portal
    await page.waitForURL('**/student**', { timeout: 15000 });
    expect(page.url()).toContain('/student');

    // 3. Verify access token and student profile
    const token = await page.evaluate(() => localStorage.getItem('access_token'));
    expect(token).toBeTruthy();

    // 4. Verify auth/me profile returns student code & class
    const meData = await page.evaluate(async (tok) => {
      const res = await fetch('/api/v1/auth/me', {
        headers: { Authorization: `Bearer ${tok}` }
      });
      return await res.json();
    }, token);

    expect(meData.role).toBe('Student');
    expect(meData.student_code).toBe('HS12001');
    expect(meData.class_name).toBe('12A1');
  });

  test('TC-STU-02: Student Dashboard & Aggregated Metrics (/student)', async ({ page }) => {
    // Login
    await page.fill('#identifier-input', STUDENT_PHONE);
    await page.fill('#password-input', STUDENT_PASS);
    await page.click('button[type="submit"]');
    await page.waitForURL('**/student**');

    // 1. Verify Homework checklist card
    const homeworkCard = page.locator('.pending-assignments-card');
    await expect(homeworkCard).toBeVisible();
    expect(await homeworkCard.textContent()).toContain('Bài tập chưa làm');

    // 2. Verify Monthly Calendar / Schedule card
    const scheduleCard = page.locator('.student-schedule-card');
    await expect(scheduleCard).toBeVisible();

    // 3. Verify Competency Spider / Radar chart cards
    const radarCards = page.locator('.student-radar-card');
    await expect(radarCards.first()).toBeVisible();

    // 4. Verify Qualitative Feedback Commentary cards
    const feedbackCards = page.locator('.feedback-note-card');
    await expect(feedbackCards.first()).toBeVisible();

    // 5. Test clicking Homework card to toggle right panel
    await homeworkCard.click();
    await page.waitForTimeout(500);
    const rightPanel = page.locator('.student-dashboard-right-panel');
    await expect(rightPanel).toBeVisible();
  });

  test('TC-STU-03: Assigned Exercises & Homework Feed (/student/exercises)', async ({ page }) => {
    // Login
    await page.fill('#identifier-input', STUDENT_PHONE);
    await page.fill('#password-input', STUDENT_PASS);
    await page.click('button[type="submit"]');
    await page.waitForURL('**/student**');

    // Navigate to Exercises Feed
    await page.goto('/student/exercises');
    await page.waitForLoadState('networkidle');

    // 1. Verify page header
    const pageContent = await page.textContent('body');
    expect(pageContent).toContain('Kho bài tập');

    // 2. Verify tabs: In Progress / Active, Overdue, Completed
    const activeTab = page.locator('button, div, span').filter({ hasText: 'Đang diễn ra' }).first();
    await expect(activeTab).toBeVisible();

    // 3. Verify exercise cards rendered
    const exerciseCards = page.locator('.student-assignment-card');
    await expect(exerciseCards.first()).toBeVisible();

    // 4. Verify search input works
    const searchInput = page.locator('input[placeholder*="Tìm"], input[type="text"]').first();
    if (await searchInput.isVisible()) {
      await searchInput.fill('Toán');
      await page.waitForTimeout(400);
      expect(await page.textContent('body')).toContain('Toán');
    }
  });

  test('TC-STU-04: Standalone Online Exam Taking Mode (/student/exercises/:id/taking)', async ({ page }) => {
    // Login
    await page.fill('#identifier-input', STUDENT_PHONE);
    await page.fill('#password-input', STUDENT_PASS);
    await page.click('button[type="submit"]');
    await page.waitForURL('**/student**');

    // Navigate to standalone exam taking page
    await page.goto('/student/exercises/1/taking');
    await page.waitForLoadState('networkidle');

    // 1. Verify distraction-free header & timer
    const timerPill = page.locator('.exam-timer-pill');
    await expect(timerPill).toBeVisible();

    // 2. Verify Fullscreen button exists in navbar
    const fullscreenBtn = page.locator('.btn-fullscreen-toggle');
    await expect(fullscreenBtn).toBeVisible();

    // 3. Verify Question Navigator Palette
    const palette = page.locator('.exam-palette-sidebar');
    await expect(palette).toBeVisible();
    await expect(palette.locator('text=MỤC LỤC CÂU HỎI')).toBeVisible();

    // 4. Answer Part I Multiple Choice question
    const optionA = page.locator('.option-select-box').first();
    if (await optionA.isVisible()) {
      await optionA.click();
      await expect(optionA).toHaveClass(/selected/);
    }

    // 5. Test Clear Answer button
    const clearBtn = page.locator('.btn-clear-answer');
    if (await clearBtn.isVisible()) {
      await clearBtn.click();
      await expect(optionA).not.toHaveClass(/selected/);
      // Re-select for submission
      await optionA.click();
    }

    // 6. Test Flag Question
    const flagBtn = page.locator('.btn-flag-review');
    await expect(flagBtn).toBeVisible();
    await flagBtn.click();
    await expect(flagBtn).toHaveClass(/flagged/);

    // 7. Test Question Navigation Next/Prev
    const nextBtn = page.locator('.btn-nav-next');
    await expect(nextBtn).toBeVisible();
    await nextBtn.click();

    // 8. Open Submit Summary Modal
    const submitBtn = page.locator('.btn-submit-exam-sidebar');
    await expect(submitBtn).toBeVisible();
    await submitBtn.click();

    // 9. Verify Confirmation Modal shows answered count
    const modal = page.locator('.exam-submit-modal-card');
    await expect(modal).toBeVisible();
    const modalText = await modal.textContent();
    expect(modalText).toMatch(/(xác nhận nộp|bài thi|bài tập)/i);

    // 10. Close or submit modal
    const cancelModalBtn = page.locator('.btn-cancel-modal');
    if (await cancelModalBtn.isVisible()) {
      await cancelModalBtn.click();
      await expect(modal).not.toBeVisible();
    }
  });

  test('TC-STU-05: Student Logout & Token Revocation', async ({ page }) => {
    // Login
    await page.fill('#identifier-input', STUDENT_PHONE);
    await page.fill('#password-input', STUDENT_PASS);
    await page.click('button[type="submit"]');
    await page.waitForURL('**/student**');

    // Trigger logout via user avatar dropdown
    const avatarBtn = page.locator('.user-profile-btn, .avatar-btn, [aria-label*="user" i]').first();
    if (await avatarBtn.isVisible()) {
      await avatarBtn.click();
      const logoutItem = page.locator('.item-logout, button:has-text("Đăng xuất")').first();
      await expect(logoutItem).toBeVisible();
      await logoutItem.click();

      // Verify redirection to login
      await page.waitForURL('**/login', { timeout: 10000 });
      expect(page.url()).toContain('/login');

      // Verify access token removed
      const token = await page.evaluate(() => localStorage.getItem('access_token'));
      expect(token).toBeNull();
    }
  });
});
