/*
File Name: guestDeleteWarning.js
Description: Guest-only warning text for delete confirmations; guest quotas count soft-deleted rows.
Created At: 2026-11-20
Created By: AI Agent
Updated At: 2026-11-20
Updated By: AI Agent
*/

export const GUEST_DELETE_WARNING =
  'Xóa tài nguyên này sẽ KHÔNG hoàn lại lượt dùng thử của tài khoản khách.';

/** Returns the warning for guests, or null for everyone else. */
export const guestDeleteWarning = (isGuest) => (isGuest ? GUEST_DELETE_WARNING : null);
