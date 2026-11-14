# Task: F-ADMIN-01 Admin User Management & Automatic Credential Dispatch

> Path: `docs/tasks/f_admin_01/task_f_admin_01_user_management.md`  
> Slice: `F-ADMIN-01-SL01` · Type: `feature` · Size: `L` · SP: `8`  
> Depends on: `f_auth_01_spec.md`, `f_admin_01_user_management_spec.md`  
> Status: `ready to test`  
> Created At: `2026-09-29`  
> Updated At: `2026-09-29`  
> Created By: `Tam Khang`  
> Updated By: `Tam Khang`  

## 1. Overview
Implement end-to-end Administrative User Management for SmartLMS with strict validations, restored original layout, and backend connection:
- Restored original table and filter layout matching UI design specifications (6 horizontal action icons under THAO TÁC: Eye, Edit, Key, Lock/Unlock, Trash, More).
- Segmented Birth Date input (`DD/MM/YYYY`) with numeric-only constraints, auto `/` separators, auto field advancement on 2 digits, isolated editing/deletion per segment, and calendar verification (rejecting invalid dates like `31/02/2020`).
- Strict Full Name validation (letters and Vietnamese accents only; numbers and special characters blocked on keyboard).
- Strict Phone Number validation (numeric only, exactly 10 digits starting with `0`).
- Unique Identifier Code generation via Backend API (`GET /api/v1/admin/users/generate-code`), set to `readOnly` to prevent manual modification and collision.
- Automatic default password generation without redundant modal notice boxes.
- Full CRUD API and frontend connection: list with search & filter, view details, edit user, status toggle, soft delete (`status = 'DELETED'`), restore (`status = 'ACTIVE'`), reset password, and Excel/CSV import/export.

## 2. Completed Items
- [x] Backend Admin Module (`backend/app/modules/admin/`):
  - [x] Endpoints for `generate-code` and `check-code` guaranteeing uniqueness.
  - [x] Full validation: student age >= 16, teacher age >= 22, phone format `0\d{9}`, name regex.
  - [x] Soft delete only (`status = 'DELETED'`).
  - [x] Automatic default password generation and notification dispatch.
- [x] Frontend UI & Validation (`frontend/src/pages/admin/`):
  - [x] Restored layout matching `media_1790663253434.png`: 6 action icons per row (Eye, Edit, Key, Lock, Trash, 3-dots), filter reset with text & icon, active filter chips row.
  - [x] `DateOfBirthInput`: DD (2 digits), MM (2 digits), YYYY (4 digits) with auto jump, numeric-only keyboard blocker, leap year & exact calendar day checks rejecting `31/02/2020`.
  - [x] Keyboard input blockers for Full Name (no numbers/symbols) and Phone (numbers only).
  - [x] Read-only unique identifier code connected to BE `generateCode`.
  - [x] Removed password notice banner from Add User modal.
- [x] Automated Tests:
  - [x] 9/9 tests passed in `backend/tests/admin/test_admin_users.py`.
  - [x] Frontend production build verified with Vite (0 errors).
