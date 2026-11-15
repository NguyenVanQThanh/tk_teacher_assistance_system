// File Name: notificationUtils.selfcheck.mjs
// Description: Runnable assert-based check for notificationUtils (node, no framework).
// Created At: 2026-11-15
// Created By: AI Agent
// Updated At: 2026-11-15
// Updated By: AI Agent

import assert from 'node:assert/strict';
import { formatRelativeTime, badgeText } from './notificationUtils.js';

const now = Date.parse('2026-11-15T10:00:00Z');
assert.equal(formatRelativeTime('2026-11-15T09:59:40Z', now), 'Vừa xong');
assert.equal(formatRelativeTime('2026-11-15T09:55:00Z', now), '5 phút trước');
assert.equal(formatRelativeTime('2026-11-15T07:00:00Z', now), '3 giờ trước');
assert.equal(formatRelativeTime('2026-11-13T10:00:00Z', now), '2 ngày trước');
assert.equal(formatRelativeTime('garbage', now), '');
assert.equal(badgeText(0), '');
assert.equal(badgeText(7), '7');
assert.equal(badgeText(150), '99+');
console.log('notificationUtils selfcheck ok');
