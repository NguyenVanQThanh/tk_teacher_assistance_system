// File Name: teacher-portal.spec.js
// Description: Comprehensive Playwright end-to-end automation test suite covering all Teacher Portal features.
// Created At: 2026-10-07
// Created By: Tam Khang
// Updated At: 2026-10-07
// Updated By: Tam Khang

import { test, expect } from '@playwright/test';

test.describe('Teacher Portal End-to-End Automation Test Suite', () => {
  const TEACHER_PHONE = '0999000002';
  const TEACHER_PASS = 'Teacher@1234';

  test.beforeEach(async ({ page }) => {
    // Navigate to login page
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
  });

  test('TC-01: Teacher Authentication & Session Establishment', async ({ page }) => {
    // 1. Fill login credentials
    await page.fill('#identifier-input', TEACHER_PHONE);
    await page.fill('#password-input', TEACHER_PASS);
    
    // 2. Click login button
    await page.click('button[type="submit"]');

    // 3. Verify redirection to teacher portal
    await page.waitForURL('**/teacher', { timeout: 15000 });
    expect(page.url()).toContain('/teacher');

    // 4. Verify persistent access token in localStorage
    const token = await page.evaluate(() => localStorage.getItem('access_token'));
    expect(token).toBeTruthy();
  });

  test('TC-02: Teacher Dashboard Overview & Metrics Loading', async ({ page }) => {
    // Login
    await page.fill('#identifier-input', TEACHER_PHONE);
    await page.fill('#password-input', TEACHER_PASS);
    await page.click('button[type="submit"]');
    await page.waitForURL('**/teacher');

    // Verify main navigation buttons in teacher sidebar
    await expect(page.locator('.sidebar-nav .nav-item-btn:has-text("Lớp học của tôi")')).toBeVisible();
    await expect(page.locator('.sidebar-nav .nav-item-btn:has-text("Chấm bài & Phản hồi")')).toBeVisible();
    await expect(page.locator('.sidebar-nav .nav-item-btn:has-text("Kho tài liệu")')).toBeVisible();
    await expect(page.locator('.sidebar-nav .nav-item-btn:has-text("Kho bài tập")')).toBeVisible();
  });

  test('TC-03: Curriculum Document Repository (/teacher/documents)', async ({ page }) => {
    // Login & navigate
    await page.fill('#identifier-input', TEACHER_PHONE);
    await page.fill('#password-input', TEACHER_PASS);
    await page.click('button[type="submit"]');
    await page.waitForURL('**/teacher');

    await page.goto('/teacher/documents');
    await page.waitForLoadState('networkidle');

    // Verify document page title / header
    const pageText = await page.textContent('body');
    expect(pageText).toContain('Kho tài liệu');

    // Verify search or filter input exists
    const searchInput = page.locator('input[type="text"], input[placeholder*="Tìm"], input[placeholder*="search" i]').first();
    await expect(searchInput).toBeVisible();
  });

  test('TC-04: Exercise Repository & Management (/teacher/exercises)', async ({ page }) => {
    // Login & navigate
    await page.fill('#identifier-input', TEACHER_PHONE);
    await page.fill('#password-input', TEACHER_PASS);
    await page.click('button[type="submit"]');
    await page.waitForURL('**/teacher');

    await page.goto('/teacher/exercises');
    await page.waitForLoadState('networkidle');

    // Verify exercise page heading
    const pageText = await page.textContent('body');
    expect(pageText).toContain('Kho bài tập');

    // Verify exercise items render
    const exerciseItems = page.locator('.exercise-card, .exercise-row, .exercise-item, tr');
    await expect(exerciseItems.first()).toBeVisible();

    // Verify search functionality works
    const searchInput = page.locator('input[placeholder*="Tìm"], input[type="text"]').first();
    if (await searchInput.isVisible()) {
      await searchInput.fill('Toán');
      await page.waitForTimeout(500);
      expect(await page.textContent('body')).toContain('Toán');
    }
  });

  test('TC-05: Create Exercise Builder Navigation (/teacher/exercises/create-manual)', async ({ page }) => {
    // Login & navigate
    await page.fill('#identifier-input', TEACHER_PHONE);
    await page.fill('#password-input', TEACHER_PASS);
    await page.click('button[type="submit"]');
    await page.waitForURL('**/teacher');

    await page.goto('/teacher/exercises/create-manual');
    await page.waitForLoadState('networkidle');

    // Verify create manual page loads
    const pageText = await page.textContent('body');
    expect(pageText.toLowerCase()).toMatch(/(tạo bài tập|thêm bài tập|thủ công|tiêu đề)/i);
  });

  test('TC-06: Class Management & Teaching Assignment (/teacher/classes)', async ({ page }) => {
    // Login & navigate
    await page.fill('#identifier-input', TEACHER_PHONE);
    await page.fill('#password-input', TEACHER_PASS);
    await page.click('button[type="submit"]');
    await page.waitForURL('**/teacher');

    await page.goto('/teacher/classes');
    await page.waitForLoadState('networkidle');

    // Verify class list page
    const pageText = await page.textContent('body');
    expect(pageText).toContain('12A1');

    // Click on class 12A1 to open class detail
    const classCard = page.locator('text=12A1').first();
    await classCard.click();

    // Expect navigation to class detail
    await page.waitForURL(/\/teacher\/classes\/.+/, { timeout: 10000 });
    await page.waitForLoadState('networkidle');

    // Wait for class details to finish loading
    await page.waitForSelector('.detail-header-card, .class-detail-container, h1, h2', { timeout: 10000 });
    const detailText = await page.textContent('body');
    expect(detailText).toMatch(/(12A1|Chi tiết lớp học|Danh sách học sinh)/);
  });

  test('TC-07: Homeroom Class Management (/teacher/homeroom)', async ({ page }) => {
    // Login & navigate
    await page.fill('#identifier-input', TEACHER_PHONE);
    await page.fill('#password-input', TEACHER_PASS);
    await page.click('button[type="submit"]');
    await page.waitForURL('**/teacher');

    await page.goto('/teacher/homeroom');
    await page.waitForLoadState('networkidle');

    // Verify homeroom class loads
    const pageText = await page.textContent('body');
    expect(pageText).toMatch(/(chủ nhiệm|12a1|học sinh)/i);
  });

  test('TC-08: Grading & Evaluation Workflow (/teacher/grading)', async ({ page }) => {
    // Login & navigate
    await page.fill('#identifier-input', TEACHER_PHONE);
    await page.fill('#password-input', TEACHER_PASS);
    await page.click('button[type="submit"]');
    await page.waitForURL('**/teacher');

    await page.goto('/teacher/grading');
    await page.waitForLoadState('networkidle');

    // Verify tabs exist: Chờ chấm and Đã duyệt
    const pendingTab = page.locator('button, span, div').filter({ hasText: 'Chờ chấm' }).first();
    await expect(pendingTab).toBeVisible();

    // Click on a pending submission to open grading modal
    const pendingCard = page.locator('.pending-item-card, .submission-card, .grading-table-row, [role="button"]').filter({ hasText: 'Chờ chấm' }).first();
    if (await pendingCard.isVisible()) {
      await pendingCard.click();

      // Verify GradingFeedbackModal opened
      const modal = page.locator('.grading-feedback-modal-overlay, .grading-modal-container');
      await expect(modal).toBeVisible({ timeout: 5000 });

      // Check banner message
      const modalText = await modal.textContent();
      expect(modalText).toContain('Chế độ chấm bài');

      // Verify close modal works
      const closeBtn = page.locator('.modal-close-btn, button:has-text("✕"), button[aria-label="Close"]').first();
      if (await closeBtn.isVisible()) {
        await closeBtn.click();
        await expect(modal).not.toBeVisible();
      }
    }
  });

  test('TC-09: Teaching Schedule & Timetable (/teacher/schedule)', async ({ page }) => {
    // Login & navigate
    await page.fill('#identifier-input', TEACHER_PHONE);
    await page.fill('#password-input', TEACHER_PASS);
    await page.click('button[type="submit"]');
    await page.waitForURL('**/teacher');

    await page.goto('/teacher/schedule');
    await page.waitForLoadState('networkidle');

    // Verify schedule calendar/timetable renders
    const pageText = await page.textContent('body');
    expect(pageText).toMatch(/(thời khóa biểu|lịch|tháng|tuần|giảng dạy)/i);
  });

  test('TC-10: Teacher Profile & Logout Flow', async ({ page }) => {
    // Login & navigate
    await page.fill('#identifier-input', TEACHER_PHONE);
    await page.fill('#password-input', TEACHER_PASS);
    await page.click('button[type="submit"]');
    await page.waitForURL('**/teacher');

    await page.goto('/teacher/profile');
    await page.waitForLoadState('networkidle');

    // Verify profile page renders teacher information
    const pageText = await page.textContent('body');
    expect(pageText).toMatch(/(Nguyen Van A|Nguyễn Văn A)/i);

    // Test logout via topbar user dropdown
    const userProfileBtn = page.locator('.user-profile-btn');
    await expect(userProfileBtn).toBeVisible();
    await userProfileBtn.click();

    // Click logout button in dropdown popover
    const logoutBtn = page.locator('.account-menu-item.item-logout, button:has-text("Đăng xuất tài khoản")');
    await expect(logoutBtn).toBeVisible();
    await logoutBtn.click();

    // Verify redirection back to login
    await page.waitForURL('**/login', { timeout: 10000 });
    expect(page.url()).toContain('/login');
  });
});
