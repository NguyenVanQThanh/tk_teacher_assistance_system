/*
File Name: MathRenderer.selfcheck.mjs
Description: Self-check that prose is not wrapped in math delimiters while formulas still are.
Created At: 2026-11-17
Created By: AI Agent
Updated At: 2026-11-17
Updated By: AI Agent
*/
import assert from 'node:assert/strict';
import { preprocessMathText as p } from '../../utils/mathPreprocess.js';

assert.ok(!p('General Vo Nguyen Giap (1911-2013) was a genius.').includes('$'));
assert.ok(!p('Read the text and mark (1) A.').includes('$'));
assert.equal(p('x^2+1'), '$x^2+1$');
assert.equal(p('\\sin x'), '$\\sin x$');
assert.equal(p('-3'), '$-3$');
console.log('MathRenderer selfcheck OK');
