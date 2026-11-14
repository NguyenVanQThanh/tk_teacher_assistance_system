// File Name: tableMarkdown.selfcheck.mjs
// Description: Assert-based self-check for markdown table helpers.
// Created At: 2026-11-12
// Created By: AI Agent
// Updated At: 2026-11-12
// Updated By: AI Agent
import assert from 'node:assert';
import { parseMarkdownTable, splitTableBlocks, buildTableTemplate } from './tableMarkdown.js';

const t = parseMarkdownTable('| Thời gian $\tau$ (s) | Nhiệt độ | P (W) |\n|---|---|---|\n| 0 | 0 | 11,13 |\n| 120 | 0 | 11,09 |');
assert.strictEqual(t.headRows[0][0].text, 'Thời gian $\tau$ (s)');
assert.strictEqual(t.rows.length, 2);
assert.deepStrictEqual(t.rows[1], ['120', '0', '11,09']);

// merged header + sub-header row from OCR
const m = parseMarkdownTable('| Chế độ | Nhiệt độ nước | | | | |\n|---|---|---|---|---|---|\n| | 1 phút | 2 phút | 3 phút | 4 phút | 5 phút |\n| Không gió | 46 | 43,5 | 41,5 | 40 | 39 |');
assert.strictEqual(m.headRows.length, 2);
assert.strictEqual(m.headRows[0][1].colSpan, 5);
assert.strictEqual(m.rows.length, 1);

assert.strictEqual(parseMarkdownTable('chỉ là văn bản | có gạch'), null);
const blocks = splitTableBlocks('Đề bài:\n| a | b |\n|---|---|\n| 1 | 2 |\nKết thúc');
assert.deepStrictEqual(blocks.map((b) => b.type), ['text', 'table', 'text']);
assert.strictEqual(buildTableTemplate(2, 3).length, 4);
console.log('tableMarkdown selfcheck passed');
