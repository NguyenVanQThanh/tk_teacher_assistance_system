import assert from 'node:assert/strict';
import { subjectAllowsPart3 } from './subjectParts.js';

assert.equal(subjectAllowsPart3('Tiếng Anh'), false);
assert.equal(subjectAllowsPart3('Giáo dục kinh tế và pháp luật'), false);
assert.equal(subjectAllowsPart3('Lịch sử'), false);
assert.equal(subjectAllowsPart3('Hóa học'), true);
assert.equal(subjectAllowsPart3('Địa lí'), true);
assert.equal(subjectAllowsPart3('Toán học'), true);
console.log('subjectParts selfcheck OK');
