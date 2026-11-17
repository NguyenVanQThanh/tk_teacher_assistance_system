// File Name: subjectParts.js
// Description: Which exam parts a subject supports (mirrors backend subject_allows_part3).
// Created At: 2026-11-17
// Created By: AI Agent
// Updated At: 2026-11-17
// Updated By: AI Agent

// ponytail: duplicates the backend list; expose it from the API if it drifts.
const NO_PART3 = ['tieng anh', 'english', 'ngu van', 'lich su', 'kinh te', 'phap luat', 'tin hoc', 'cong nghe'];

const fold = (s) => String(s || '').toLowerCase().replace(/đ/g, 'd').normalize('NFD').replace(/[̀-ͯ]/g, '');

/** False for subjects without a numeric short-answer Part III. */
export const subjectAllowsPart3 = (subjectName) => !NO_PART3.some((k) => fold(subjectName).includes(k));

export const PART3_NOT_SUPPORTED_MESSAGE = 'Môn học này không có phần Trả lời ngắn. Vui lòng đặt số câu phần III bằng 0.';
