// File Name: gradeClassification.js
// Description: Single source of truth for student academic classification and Vietnamese name ordering.
// Created At: 2026-11-12
// Created By: AI Agent
// Updated At: 2026-11-12
// Updated By: AI Agent

export const CLASSIFICATION_LABELS = {
  excellent: 'Xuất sắc',
  good: 'Giỏi',
  fair: 'Khá',
  none: 'Chưa đạt',
};

/**
 * Classify a student from subject scores.
 * Excellent: >= 6 subjects >= 9.0 and none < 6.5.
 * Good: >= 6 subjects >= 8.0 and none < 6.5.
 * Fair: >= 6 subjects >= 6.5 and none <= 5.0.
 */
export function classifyStudent(scores) {
  const s = (scores || []).map(Number).filter((n) => Number.isFinite(n));
  const count = (min) => s.filter((n) => n >= min).length;
  const min = s.length ? Math.min(...s) : 0;
  if (count(9.0) >= 6 && min >= 6.5) return 'excellent';
  if (count(8.0) >= 6 && min >= 6.5) return 'good';
  if (count(6.5) >= 6 && min > 5.0) return 'fair';
  return 'none';
}

/** Compare names in Vietnamese order: last word (given name) first, then full name. */
export function compareVietnameseNames(a, b) {
  const last = (n) => (n || '').trim().split(/\s+/).pop();
  return (
    last(a).localeCompare(last(b), 'vi') ||
    (a || '').localeCompare(b || '', 'vi')
  );
}
