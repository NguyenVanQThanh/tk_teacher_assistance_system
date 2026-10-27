// File Name: admin-portal.spec.js
// Description: Comprehensive Playwright end-to-end automation test suite covering all Admin Portal features.
// Created At: 2026-10-07
// Created By: Tam Khang
// Updated At: 2026-10-07
// Updated By: Tam Khang

import { test, expect } from '@playwright/test';

test.describe('Admin Portal End-to-End Automation Test Suite', () => {
  const ADMIN_PHONE = '0999000001';
  const ADMIN_PASS = 'Admin@1234';

  test.beforeEach(async ({ page }) => {
    // Navigate to login page
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
  });

  test('TC-01: Admin Authentication & Session Establishment', async ({ page }) => {
    // 1. Fill admin login credentials
    await page.fill('#identifier-input', ADMIN_PHONE);
    await page.fill('#password-input', ADMIN_PASS);

    // 2. Click login button
    await page.click('button[type="submit"]');

    // 3. Verify redirection to admin dashboard
    await page.waitForURL('**/admin', { timeout: 15000 });
    expect(page.url()).toContain('/admin');

    // 4. Verify persistent access token in localStorage
    const token = await page.evaluate(() => localStorage.getItem('access_token'));
    expect(token).toBeTruthy();
  });

  test('TC-02: Admin Dashboard Overview & Core KPIs (/admin)', async ({ page }) => {
    // Login
    await page.fill('#identifier-input', ADMIN_PHONE);
    await page.fill('#password-input', ADMIN_PASS);
    await page.click('button[type="submit"]');
    await page.waitForURL('**/admin');
    await page.waitForLoadState('networkidle');

    // Verify welcome greeting
    const welcomeTitle = page.locator('.admin-welcome-title');
    await expect(welcomeTitle).toBeVisible();
    expect(await welcomeTitle.textContent()).toContain('Quản trị viên');

    // Verify AI status card
    const aiCard = page.locator('.header-ai-status-card');
    await expect(aiCard).toBeVisible();
    expect(await aiCard.textContent()).toContain('API AI Tạo bài tập');

    // Verify admin sidebar navigation items
    const sidebar = page.locator('.admin-sidebar');
    await expect(sidebar).toBeVisible();
    await expect(sidebar.locator('.admin-nav-item:has-text("Bảng điều khiển")')).toBeVisible();
    await expect(sidebar.locator('.admin-nav-item:has-text("Quản lý người dùng")')).toBeVisible();
    await expect(sidebar.locator('.admin-nav-item:has-text("Quản lý trường lớp")')).toBeVisible();
    await expect(sidebar.locator('.admin-nav-item:has-text("Phân quyền & Vai trò")')).toBeVisible();
    await expect(sidebar.locator('.admin-nav-item:has-text("Báo cáo & Thống kê")')).toBeVisible();
  });

  test('TC-03: Dynamic LMS Traffic Chart & Timeframe Toggle (/admin)', async ({ page }) => {
    // Login
    await page.fill('#identifier-input', ADMIN_PHONE);
    await page.fill('#password-input', ADMIN_PASS);
    await page.click('button[type="submit"]');
    await page.waitForURL('**/admin');
    await page.waitForLoadState('networkidle');

    // Verify SVG traffic chart
    const chart = page.locator('.admin-svg-chart');
    await expect(chart).toBeVisible();

    // Toggle to monthly timeframe
    const monthPill = page.locator('.admin-toggle-pill:has-text("Theo tháng")');
    await expect(monthPill).toBeVisible();
    await monthPill.click();
    await expect(monthPill).toHaveClass(/active/);

    // Toggle back to weekly timeframe
    const weekPill = page.locator('.admin-toggle-pill:has-text("Theo tuần")');
    await expect(weekPill).toBeVisible();
    await weekPill.click();
    await expect(weekPill).toHaveClass(/active/);
  });

  test('TC-04: Pending Approval Requests Queue & Actions (/admin)', async ({ page }) => {
    // Login
    await page.fill('#identifier-input', ADMIN_PHONE);
    await page.fill('#password-input', ADMIN_PASS);
    await page.click('button[type="submit"]');
    await page.waitForURL('**/admin');
    await page.waitForLoadState('networkidle');

    // Verify requests section exists
    const requestPanel = page.locator('.requests-panel, .admin-panel:has-text("Hàng đợi phê duyệt"), .admin-panel:has-text("phê duyệt")');
    await expect(requestPanel.first()).toBeVisible();

    // If approval buttons exist, test clicking approve
    const approveBtn = page.locator('.btn-req-approve, button:has-text("Duyệt"), button:has-text("Phê duyệt")').first();
    if (await approveBtn.isVisible()) {
      await approveBtn.click();
      await page.waitForTimeout(1000);
    }
  });

  test('TC-05: System Audit Logs Timeline & Audit Trail Dialog (/admin)', async ({ page }) => {
    // Login
    await page.fill('#identifier-input', ADMIN_PHONE);
    await page.fill('#password-input', ADMIN_PASS);
    await page.click('button[type="submit"]');
    await page.waitForURL('**/admin');
    await page.waitForLoadState('networkidle');

    // Verify audit logs or operations section
    const auditSection = page.locator('.audit-panel, .admin-panel:has-text("Nhật ký"), .admin-panel:has-text("hoạt động")');
    await expect(auditSection.first()).toBeVisible();

    // Click "Xem toàn bộ nhật ký kiểm toán" button
    const viewAllBtn = page.locator('.audit-view-all-btn');
    if (await viewAllBtn.isVisible()) {
      await viewAllBtn.click();
      const auditModal = page.locator('.admin-modal-backdrop .modal-lg, .admin-modal-backdrop .admin-modal-card');
      await expect(auditModal).toBeVisible({ timeout: 5000 });
      expect(await auditModal.textContent()).toMatch(/(toàn bộ nhật ký kiểm toán|mức độ|hệ thống)/i);

      // Close audit modal
      const closeBtn = page.locator('.admin-modal-close').first();
      await closeBtn.click();
      await expect(auditModal).not.toBeVisible();
    }
  });

  test('TC-06: User Directory Navigation, Search & Dynamic Filter Tags (/admin/users)', async ({ page }) => {
    // Login
    await page.fill('#identifier-input', ADMIN_PHONE);
    await page.fill('#password-input', ADMIN_PASS);
    await page.click('button[type="submit"]');
    await page.waitForURL('**/admin');

    // Navigate to /admin/users
    await page.goto('/admin/users');
    await page.waitForLoadState('networkidle');

    // Verify User table is visible
    const usersTable = page.locator('.users-table');
    await expect(usersTable).toBeVisible();

    // Verify table headers
    const headerText = await usersTable.locator('thead').textContent();
    expect(headerText).toContain('MÃ ĐỊNH DANH');
    expect(headerText).toContain('HỌ VÀ TÊN & LIÊN HỆ');
    expect(headerText).toContain('VAI TRÒ');
    expect(headerText).toContain('TRẠNG THÁI');

    // Test Role Tabs: Students
    const studentTab = page.locator('.users-tab-pill:has-text("Học sinh")');
    await studentTab.click();
    await page.waitForTimeout(600);
    expect(await studentTab.getAttribute('class')).toContain('active');

    // Test Role Tabs: Teachers
    const teacherTab = page.locator('.users-tab-pill:has-text("Giáo viên")');
    await teacherTab.click();
    await page.waitForTimeout(600);
    expect(await teacherTab.getAttribute('class')).toContain('active');

    // Test Role Tabs: Pending / Inactive
    const pendingTab = page.locator('.users-tab-pill:has-text("Chờ kích hoạt")');
    await pendingTab.click();
    await page.waitForTimeout(600);
    expect(await pendingTab.getAttribute('class')).toContain('active');

    // Switch back to All tab
    const allTab = page.locator('.users-tab-pill:has-text("Tất cả")');
    await allTab.click();
    await page.waitForTimeout(600);

    // Test Search Box
    const searchInput = page.locator('.filter-search-input');
    await expect(searchInput).toBeVisible();
    await searchInput.fill('0999');
    await page.waitForTimeout(600);
    const bodyText = await page.textContent('.users-table-scroll-wrapper');
    expect(bodyText).toContain('0999');

    // Test Search Clear button
    const clearBtn = page.locator('.filter-search-clear');
    if (await clearBtn.isVisible()) {
      await clearBtn.click();
      await page.waitForTimeout(500);
    }

    // Test Dynamic Filter Tags Row & Instant Clear All
    const activeTagsRow = page.locator('.users-active-tags-row');
    if (await activeTagsRow.isVisible()) {
      expect(await activeTagsRow.textContent()).toContain('Bộ lọc đang áp dụng:');

      // Click "Xóa tất cả" button
      const clearAllTagsBtn = page.locator('.tags-clear-all');
      await expect(clearAllTagsBtn).toBeVisible();
      await clearAllTagsBtn.click();
      await page.waitForTimeout(600);
      await expect(activeTagsRow).not.toBeVisible();
    }
  });

  test('TC-07: User Detail Modal Inspection (/admin/users)', async ({ page }) => {
    // Login & navigate
    await page.fill('#identifier-input', ADMIN_PHONE);
    await page.fill('#password-input', ADMIN_PASS);
    await page.click('button[type="submit"]');
    await page.waitForURL('**/admin');

    await page.goto('/admin/users');
    await page.waitForLoadState('networkidle');

    // Wait for table to load
    await page.waitForSelector('.table-row-actions', { timeout: 10000 });

    // Locate and click the View Details button on the first user row
    const viewBtn = page.locator('button[title="Xem chi tiết hồ sơ"]').first();
    await expect(viewBtn).toBeVisible({ timeout: 10000 });
    await viewBtn.click();

    // Verify user details modal opens
    const modal = page.locator('.admin-modal-backdrop .admin-modal-card');
    await expect(modal).toBeVisible({ timeout: 5000 });
    const modalText = await modal.textContent();
    expect(modalText).toMatch(/(chi tiết tài khoản|hồ sơ người dùng|thông tin|mã định danh|email)/i);

    // Close the modal
    const closeBtn = page.locator('.admin-modal-close').first();
    if (await closeBtn.isVisible()) {
      await closeBtn.click();
      await expect(modal).not.toBeVisible();
    }
  });

  test('TC-08: Add User Modal, Input Validations & Code Collision Check (/admin/users)', async ({ page }) => {
    // Login & navigate
    await page.fill('#identifier-input', ADMIN_PHONE);
    await page.fill('#password-input', ADMIN_PASS);
    await page.click('button[type="submit"]');
    await page.waitForURL('**/admin');

    await page.goto('/admin/users');
    await page.waitForLoadState('networkidle');

    // Click "+ Thêm người dùng mới" button
    const addBtn = page.locator('.btn-add-user');
    await expect(addBtn).toBeVisible();
    await addBtn.click();

    // Verify Add User Modal opens
    const modal = page.locator('.admin-modal-backdrop .modal-add-user');
    await expect(modal).toBeVisible({ timeout: 5000 });

    // Verify code collision check indicator
    const helperText = modal.locator('.input-helper-text').first();
    await expect(helperText).toBeVisible();

    // Click "Tạo tự động" to trigger generateCode & checkCode API
    const autoGenBtn = modal.locator('.btn-auto-generate');
    await expect(autoGenBtn).toBeVisible();
    await autoGenBtn.click();
    await page.waitForTimeout(600);
    expect(await helperText.textContent()).toContain('khả dụng');

    // Verify segmented birth date input fields
    const dayInput = page.locator('.dob-day');
    const monthInput = page.locator('.dob-month');
    const yearInput = page.locator('.dob-year');
    await expect(dayInput).toBeVisible();
    await expect(monthInput).toBeVisible();
    await expect(yearInput).toBeVisible();

    // Fill valid birth date: 15/05/1990
    await dayInput.fill('15');
    await monthInput.fill('05');
    await yearInput.fill('1990');

    // Close modal without submitting
    const closeBtn = page.locator('.admin-modal-close').first();
    if (await closeBtn.isVisible()) {
      await closeBtn.click();
      await expect(modal).not.toBeVisible();
    }
  });

  test('TC-08b: Import Users from Excel / CSV Template Modal (/admin/users)', async ({ page }) => {
    // Login & navigate
    await page.fill('#identifier-input', ADMIN_PHONE);
    await page.fill('#password-input', ADMIN_PASS);
    await page.click('button[type="submit"]');
    await page.waitForURL('**/admin');

    await page.goto('/admin/users');
    await page.waitForLoadState('networkidle');

    // Click "Nhập Excel" button
    const importBtn = page.locator('.btn-sync-import-excel');
    await expect(importBtn).toBeVisible();
    await importBtn.click();

    // Verify Import Modal opens
    const importModal = page.locator('.admin-modal-backdrop .admin-modal-card');
    await expect(importModal).toBeVisible({ timeout: 5000 });
    expect(await importModal.textContent()).toMatch(/(nhập danh sách|excel|csv)/i);

    // Verify file input exists
    const fileInput = importModal.locator('input[type="file"]');
    await expect(fileInput).toBeAttached();

    // Close modal
    const cancelBtn = importModal.locator('.admin-btn-cancel, .admin-modal-close').first();
    await cancelBtn.click();
    await expect(importModal).not.toBeVisible();
  });

  test('TC-09: School & Classes Directory Management (/admin/classes)', async ({ page }) => {
    // Login & navigate
    await page.fill('#identifier-input', ADMIN_PHONE);
    await page.fill('#password-input', ADMIN_PASS);
    await page.click('button[type="submit"]');
    await page.waitForURL('**/admin');

    await page.goto('/admin/classes');
    await page.waitForLoadState('networkidle');

    // Verify classes page renders
    const pageText = await page.textContent('body');
    expect(pageText).toMatch(/(quản lý trường lớp|danh sách lớp học|khối 10|khối 11|khối 12)/i);

    // Verify grade tabs
    const gradeTabs = page.locator('.classes-tab-pill, button:has-text("Khối 10"), button:has-text("Tất cả")');
    await expect(gradeTabs.first()).toBeVisible();
  });

  test('TC-10: Roles & Permissions Matrix Management (/admin/roles)', async ({ page }) => {
    // Login & navigate
    await page.fill('#identifier-input', ADMIN_PHONE);
    await page.fill('#password-input', ADMIN_PASS);
    await page.click('button[type="submit"]');
    await page.waitForURL('**/admin');

    await page.goto('/admin/roles');
    await page.waitForLoadState('networkidle');

    // Verify roles list & permission matrix
    const pageText = await page.textContent('body');
    expect(pageText).toMatch(/(phân quyền|vai trò|quản trị viên|giáo viên|học sinh)/i);

    // Verify role cards / items
    const roleItems = page.locator('.role-item-card, .role-nav-btn, .roles-list');
    await expect(roleItems.first()).toBeVisible();
  });

  test('TC-11: Academic Reports & Analytics Dashboard (/admin/reports)', async ({ page }) => {
    // Login & navigate
    await page.fill('#identifier-input', ADMIN_PHONE);
    await page.fill('#password-input', ADMIN_PASS);
    await page.click('button[type="submit"]');
    await page.waitForURL('**/admin');

    await page.goto('/admin/reports');
    await page.waitForLoadState('networkidle');

    // Verify reports page
    const pageText = await page.textContent('body');
    expect(pageText).toMatch(/(báo cáo|thống kê|kết quả học tập|gpa|học kỳ)/i);
  });

  test('TC-12: System Settings Configuration (/admin/settings)', async ({ page }) => {
    // Login & navigate
    await page.fill('#identifier-input', ADMIN_PHONE);
    await page.fill('#password-input', ADMIN_PASS);
    await page.click('button[type="submit"]');
    await page.waitForURL('**/admin');

    await page.goto('/admin/settings');
    await page.waitForLoadState('networkidle');

    // Verify settings page
    const pageText = await page.textContent('body');
    expect(pageText).toMatch(/(cài đặt hệ thống|hồ sơ trường|bảo mật|thông báo)/i);
  });

  test('TC-13: Admin Secure Logout & Protected Layout Redirection', async ({ page }) => {
    // Login
    await page.fill('#identifier-input', ADMIN_PHONE);
    await page.fill('#password-input', ADMIN_PASS);
    await page.click('button[type="submit"]');
    await page.waitForURL('**/admin');

    // Click Logout in Admin Sidebar
    const logoutBtn = page.locator('.admin-sidebar .logout-btn');
    await expect(logoutBtn).toBeVisible();
    await logoutBtn.click();

    // Verify redirection to /login
    await page.waitForURL('**/login', { timeout: 10000 });
    expect(page.url()).toContain('/login');

    // Verify token removed
    const token = await page.evaluate(() => localStorage.getItem('access_token'));
    expect(token).toBeFalsy();

    // Attempt navigating back to /admin directly
    await page.goto('/admin');
    await page.waitForURL('**/login', { timeout: 10000 });
    expect(page.url()).toContain('/login');
  });
});
