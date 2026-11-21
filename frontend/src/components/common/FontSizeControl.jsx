// File Name: FontSizeControl.jsx
// Description: useExerciseFontScale hook and compact A- / A / A+ control for exercise content size.
// Created At: 2026-11-20
// Created By: AI Agent
// Updated At: 2026-11-20
// Updated By: AI Agent
import React, { useState, useCallback } from 'react';
import { FONT_SCALE_STEPS, FONT_SCALE_KEY, clampStep } from '../../utils/fontScale';

/** Returns {step, scale, inc, dec, reset}; persisted in localStorage when available. */
export function useExerciseFontScale() {
  const [step, setStep] = useState(() => {
    try { return clampStep(localStorage.getItem(FONT_SCALE_KEY)); } catch { return 0; }
  });
  const update = useCallback((fn) => setStep((s) => {
    const next = clampStep(fn(s));
    try { localStorage.setItem(FONT_SCALE_KEY, String(next)); } catch { /* storage unavailable */ }
    return next;
  }), []);
  return {
    step,
    scale: FONT_SCALE_STEPS[step],
    inc: () => update((s) => s + 1),
    dec: () => update((s) => s - 1),
    reset: () => update(() => 0),
  };
}

export default function FontSizeControl({ step, onInc, onDec, onReset }) {
  const max = FONT_SCALE_STEPS.length - 1;
  return (
    <div className="font-size-control" role="group" aria-label="Cỡ chữ nội dung bài làm">
      <button type="button" className="exam-icon-btn" aria-label="Giảm cỡ chữ" title="Giảm cỡ chữ" disabled={step <= 0} onClick={onDec}>A-</button>
      <button type="button" className="exam-icon-btn" aria-label={`Cỡ chữ ${Math.round(FONT_SCALE_STEPS[step] * 100)}%, bấm để đặt lại`} title="Đặt lại cỡ chữ" onClick={onReset}>{Math.round(FONT_SCALE_STEPS[step] * 100)}%</button>
      <button type="button" className="exam-icon-btn" aria-label="Tăng cỡ chữ" title="Tăng cỡ chữ" disabled={step >= max} onClick={onInc}>A+</button>
    </div>
  );
}
