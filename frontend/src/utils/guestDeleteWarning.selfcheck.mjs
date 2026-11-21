/*
File Name: guestDeleteWarning.selfcheck.mjs
Description: Assert-based selfcheck for guestDeleteWarning.
Created At: 2026-11-20
Created By: AI Agent
Updated At: 2026-11-20
Updated By: AI Agent
*/
import assert from 'node:assert/strict';
import { guestDeleteWarning, GUEST_DELETE_WARNING } from './guestDeleteWarning.js';

assert.equal(guestDeleteWarning(true), GUEST_DELETE_WARNING);
assert.match(GUEST_DELETE_WARNING, /KHÔNG hoàn lại/);
assert.equal(guestDeleteWarning(false), null);
assert.equal(guestDeleteWarning(undefined), null);
console.log('guestDeleteWarning selfcheck ok');
