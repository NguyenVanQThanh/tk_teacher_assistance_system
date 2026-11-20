// File Name: fontScale.js
// Description: Pure helpers for the student exercise font-size control (steps, clamping, storage key).
// Created At: 2026-11-20
// Created By: AI Agent
// Updated At: 2026-11-20
// Updated By: AI Agent

export const FONT_SCALE_STEPS = [1, 1.1, 1.25, 1.4, 1.5];
export const FONT_SCALE_KEY = 'student_exercise_font_scale';

/** Clamp an arbitrary step index to the valid range; non-numbers fall back to 0. */
export const clampStep = (i) => {
  const n = Math.round(Number(i));
  if (!Number.isFinite(n)) return 0;
  return Math.min(FONT_SCALE_STEPS.length - 1, Math.max(0, n));
};
