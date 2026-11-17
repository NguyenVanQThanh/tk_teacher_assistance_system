// File Name: codeMarkdown.selfcheck.mjs
// Description: Assert-based self-check for codeMarkdown helpers.
// Created At: 2026-11-18
// Created By: AI Agent
// Updated At: 2026-11-18
// Updated By: AI Agent
import assert from 'node:assert/strict';
import { splitCodeBlocks, splitInlineCode } from './codeMarkdown.js';

const html = '```html\n<div>\n    <p>x</p>\n</div>\n```';
let p = splitCodeBlocks(html);
assert.equal(p.length, 1);
assert.equal(p[0].lang, 'html');
assert.equal(p[0].value, '<div>\n    <p>x</p>\n</div>');

p = splitCodeBlocks('Before\n```python\nx = 1\n```\nAfter');
assert.deepEqual(p.map((b) => b.type), ['text', 'code', 'text']);
assert.equal(p[0].value, 'Before\n');
assert.equal(p[2].value, '\nAfter');

p = splitCodeBlocks('Open ```python\nx = 1');
assert.deepEqual(p.map((b) => b.type), ['text']);

p = splitCodeBlocks('```\ncost = $5 + $6\n```');
assert.equal(p[0].value, 'cost = $5 + $6');

p = splitInlineCode('Run `print(x)` now');
assert.deepEqual(p.map((b) => b.type), ['text', 'code', 'text']);
assert.equal(p[1].value, 'print(x)');
console.log('codeMarkdown selfcheck OK');
