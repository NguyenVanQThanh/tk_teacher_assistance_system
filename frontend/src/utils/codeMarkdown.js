// File Name: codeMarkdown.js
// Description: Pure helpers that split text into fenced code blocks and inline code spans.
// Created At: 2026-11-18
// Created By: AI Agent
// Updated At: 2026-11-18
// Updated By: AI Agent

/**
 * Split text on ``` fences. Unclosed fences stay plain text.
 * @returns {{type:'code'|'text', value:string, lang?:string}[]}
 */
export function splitCodeBlocks(text) {
  const out = [];
  if (!text) return out;
  const re = /```([\w+-]*)[^\n]*\n([\s\S]*?)\n?```/g;
  let last = 0;
  let m;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) out.push({ type: 'text', value: text.slice(last, m.index) });
    out.push({ type: 'code', value: m[2], lang: m[1] || '' });
    last = m.index + m[0].length;
  }
  if (last < text.length) out.push({ type: 'text', value: text.slice(last) });
  return out;
}

/**
 * Split text on single-backtick inline code spans.
 * @returns {{type:'code'|'text', value:string}[]}
 */
export function splitInlineCode(text) {
  return (text || '').split(/(`[^`\n]+`)/).filter(Boolean).map((s) => (
    s.length > 2 && s.startsWith('`') && s.endsWith('`')
      ? { type: 'code', value: s.slice(1, -1) }
      : { type: 'text', value: s }));
}
