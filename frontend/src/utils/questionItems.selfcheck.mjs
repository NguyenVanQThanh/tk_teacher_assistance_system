// File Name: questionItems.selfcheck.mjs
// Description: Assert-based self-check for getQuestionItems (short answer segments must not become options).
// Created At: 2026-11-12
// Created By: AI Agent
// Updated At: 2026-11-12
// Updated By: AI Agent
import assert from 'node:assert';
import { getQuestionItems, sortQuestionsByPart } from './questionItems.js';

const shortAnswer = {
  question_type: 'ShortAnswer', answer_options: [],
  segments: [{ type: 'text', content: 'Khi nhận' }, { type: 'math', latex: '35{,}4' }, { type: 'text', content: 'kJ' }],
};
assert.strictEqual(getQuestionItems(shortAnswer).length, 0);

const tf = {
  question_type: 'TrueFalse', answer_options: [],
  segments: [{ key: 'a', statement: 'S1', is_correct: true }, { key: 'b', statement: 'S2', is_correct: false }],
};
assert.strictEqual(getQuestionItems(tf).length, 2);
const mixed = [
  { question_type: 'ShortAnswer', display_order: 1 },
  { question_type: 'MultipleChoice', display_order: 2 },
  { question_type: 'TrueFalse', display_order: 3 },
  { question_type: 'MultipleChoice', display_order: 4 },
];
assert.deepStrictEqual(sortQuestionsByPart(mixed).map((q) => q.display_order), [2, 4, 3, 1]);
console.log('questionItems selfcheck passed');
