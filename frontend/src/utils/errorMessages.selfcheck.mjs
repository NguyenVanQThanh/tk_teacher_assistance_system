/*
File Name: errorMessages.selfcheck.mjs
Description: Self-check that every backend error code has a Vietnamese mapping.
Created At: 2026-11-15
Created By: AI Agent
Updated At: 2026-11-15
Updated By: AI Agent
*/
import assert from 'node:assert/strict';
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { ERROR_CODE_MESSAGES, getErrorMessage } from './errorMessages.js';

const root = join(dirname(fileURLToPath(import.meta.url)), '../../../backend/app');
const codes = new Set();
const walk = (d) => {
  for (const f of readdirSync(d)) {
    const p = join(d, f);
    if (statSync(p).isDirectory()) walk(p);
    else if (f.endsWith('.py')) {
      for (const m of readFileSync(p, 'utf8').matchAll(/ERR-[A-Z0-9]+-[A-Z0-9_]+/g)) codes.add(m[0]);
    }
  }
};
walk(root);
assert.ok(codes.size > 50);
const vi = /[ạảãàáâậầấẩẫăắằặẳẵéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđ]/i;
for (const c of codes) assert.ok(ERROR_CODE_MESSAGES[c], `missing mapping: ${c}`);
for (const [c, m] of Object.entries(ERROR_CODE_MESSAGES)) assert.ok(vi.test(m), `not Vietnamese: ${c}`);

const quiet = console.error;
console.error = () => {};
const http = (status, detail) => ({ response: { status, data: { detail } } });
assert.equal(getErrorMessage(http(400, { code: 'ERR-DOC-NOT_FOUND', message: 'Doc not found' })), 'Không tìm thấy tài liệu.');
assert.match(getErrorMessage(http(422, [{ msg: 'field required' }])), /không hợp lệ/);
assert.match(getErrorMessage({ message: 'Network Error', request: {} }), /kết nối/);
assert.match(getErrorMessage({ code: 'ECONNABORTED', message: 'timeout of 1ms exceeded' }), /chậm/);
assert.match(getErrorMessage(http(500, 'Traceback boom')), /sự cố/);
assert.equal(getErrorMessage(http(400, { code: 'ERR-X-NEW', message: 'English' }), 'Lỗi.'), 'Lỗi.');
assert.ok(!/English|Traceback/.test(getErrorMessage(http(404, 'Not Found English'))));
console.error = quiet;
console.log(`errorMessages selfcheck passed (${codes.size} codes)`);
