/*
File Name: mathDocSerializer.selfcheck.mjs
Description: Runnable assert-based self-check for mathDocSerializer.
Created At: 2026-11-11
Created By: AI Agent
Updated At: 2026-11-11
Updated By: AI Agent
*/
import assert from 'node:assert/strict';
import { parseToDoc, serializeDoc, stripPlaceholders } from './mathDocSerializer.js';

const rt = (s, o) => serializeDoc(parseToDoc(s, o));
for (const s of [
  '', 'Cho hàm số $f(x) = x^2$ và $g(x)$.',
  'Dòng 1\n\n$$ax^2 + bx + c = 0$$\nDòng 3',
  'Ảnh: ![hinh](/uploads/questions/a.png) xong',
  '$\\ln(x^2+1) + C$', 'Không có công thức',
]) assert.equal(rt(s), s);
assert.equal(rt('Câu \\(x\\) và \\[y\\]'), 'Câu $x$ và $$y$$');
assert.equal(rt('a\nb', { singleLine: true }), 'a b');
assert.equal(stripPlaceholders('\\placeholder{}x^2+\\placeholder{3}'), 'x^2+3');
assert.equal(serializeDoc({ type: 'doc', content: [{ type: 'paragraph', content: [
  { type: 'text', text: 'A ' }, { type: 'mathField', attrs: { latex: '\\placeholder{}', display: false } } ] }] }), 'A ');
console.log('mathDocSerializer selfcheck passed');
