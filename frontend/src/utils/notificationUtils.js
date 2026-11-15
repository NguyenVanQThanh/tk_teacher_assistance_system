// File Name: notificationUtils.js
// Description: Pure helpers for the notification bell (Vietnamese relative time, badge text).
// Created At: 2026-11-15
// Created By: AI Agent
// Updated At: 2026-11-15
// Updated By: AI Agent

/** Format an ISO timestamp as a short Vietnamese relative time ("2 phút trước"). */
export function formatRelativeTime(iso, now = Date.now()) {
  const t = new Date(iso).getTime();
  if (Number.isNaN(t)) return '';
  const sec = Math.max(0, Math.floor((now - t) / 1000));
  if (sec < 60) return 'Vừa xong';
  const min = Math.floor(sec / 60);
  if (min < 60) return `${min} phút trước`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr} giờ trước`;
  const day = Math.floor(hr / 24);
  if (day < 30) return `${day} ngày trước`;
  return new Date(t).toLocaleDateString('vi-VN');
}

/** Badge label: hidden at 0, capped at "99+". */
export function badgeText(count) {
  if (!count || count < 1) return '';
  return count > 99 ? '99+' : String(count);
}
