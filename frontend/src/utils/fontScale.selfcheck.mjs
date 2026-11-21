// File Name: fontScale.selfcheck.mjs
// Description: Assert-based self-check for fontScale helpers.
// Created At: 2026-11-20
// Created By: AI Agent
// Updated At: 2026-11-20
// Updated By: AI Agent
import assert from 'node:assert/strict';
import { clampStep, FONT_SCALE_STEPS, FONT_SCALE_KEY } from './fontScale.js';

const last = FONT_SCALE_STEPS.length - 1;
assert.equal(clampStep(-3), 0);
assert.equal(clampStep(99), last);
assert.equal(clampStep('2'), 2);
assert.equal(clampStep(null), 0);
assert.equal(clampStep(undefined), 0);
assert.equal(clampStep('abc'), 0);
assert.equal(FONT_SCALE_STEPS[0], 1);
assert.equal(FONT_SCALE_STEPS[last], 1.5);
assert.equal(FONT_SCALE_KEY, 'student_exercise_font_scale');
console.log('fontScale selfcheck OK');
