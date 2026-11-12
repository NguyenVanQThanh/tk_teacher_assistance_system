// File Name: gradebookExport.js
// Description: Builds and downloads a gradebook CSV from attempt list items (per student or per class).
// Created At: 2026-11-12
// Created By: AI Agent
// Updated At: 2026-11-12
// Updated By: AI Agent

const esc = (v) => `"${String(v ?? '').replace(/"/g, '""')}"`;

/** Download attempts as CSV (UTF-8 BOM so Excel reads Vietnamese). */
export function downloadGradebookCsv(attempts, filename) {
  const header = ['Student', 'Student code', 'Class', 'Subject', 'Exercise', 'Score', 'Status', 'Submitted at'];
  const rows = attempts.map((a) => [
    a.student_name, a.student_code, a.class_name, a.subject_name, a.assignment_title || a.exercise_title,
    a.score ?? '', a.score != null ? 'Completed' : a.is_finished ? 'Submitted' : 'In progress',
    a.end_time ? new Date(a.end_time).toLocaleString('vi-VN') : '',
  ]);
  const csv = [header, ...rows].map((r) => r.map(esc).join(',')).join('\r\n');
  const url = URL.createObjectURL(new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8' }));
  const el = document.createElement('a');
  el.href = url;
  el.download = filename;
  el.click();
  URL.revokeObjectURL(url);
}
