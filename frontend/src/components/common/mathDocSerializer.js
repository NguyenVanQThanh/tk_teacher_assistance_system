/*
File Name: mathDocSerializer.js
Description: Pure converters between the stored math string ($...$, $$...$$, ![alt](url), \n) and ProseMirror JSON.
Created At: 2026-11-11
Created By: AI Agent
Updated At: 2026-11-11
Updated By: AI Agent
*/

const TOKEN_RE =
  /(\$\$[\s\S]+?\$\$|\$[^$\n]+?\$|\\\[[\s\S]+?\\\]|\\\([\s\S]+?\\\)|!\[[^\]]*\]\([^)\s]+(?:\s+"[^"]*")?\))/g;

/** Remove MathLive \placeholder{...} wrappers, keeping their content. */
export function stripPlaceholders(latex) {
  return String(latex ?? '')
    .replace(/\\placeholder(?:\[[^\]]*\])?\{([^{}]*)\}/g, '$1')
    .trim();
}

function parseLine(line) {
  const content = [];
  const pushText = (t) => {
    if (t) content.push({ type: 'text', text: t });
  };
  let last = 0;
  line.replace(TOKEN_RE, (m, _g, offset) => {
    pushText(line.slice(last, offset));
    last = offset + m.length;
    if (m.startsWith('$$')) {
      content.push({ type: 'mathField', attrs: { latex: m.slice(2, -2).trim(), display: true } });
    } else if (m.startsWith('\\[')) {
      content.push({ type: 'mathField', attrs: { latex: m.slice(2, -2).trim(), display: true } });
    } else if (m.startsWith('$')) {
      content.push({ type: 'mathField', attrs: { latex: m.slice(1, -1).trim(), display: false } });
    } else if (m.startsWith('\\(')) {
      content.push({ type: 'mathField', attrs: { latex: m.slice(2, -2).trim(), display: false } });
    } else {
      const im = /^!\[([^\]]*)\]\(([^)\s]+)/.exec(m);
      content.push({ type: 'image', attrs: { src: im[2], alt: im[1] } });
    }
    return m;
  });
  pushText(line.slice(last));
  return content.length ? { type: 'paragraph', content } : { type: 'paragraph' };
}

/** Parse a stored string into a ProseMirror doc JSON. */
export function parseToDoc(value, { singleLine = false } = {}) {
  let text = value ?? '';
  // Display math must stay inside one paragraph.
  text = text.replace(/\$\$[\s\S]+?\$\$/g, (m) => m.replace(/\r?\n/g, ' '));
  const lines = singleLine ? [text.replace(/\r?\n/g, ' ')] : text.split(/\r?\n/);
  return { type: 'doc', content: lines.map(parseLine) };
}

function serializeInline(node) {
  if (node.type === 'text') return node.text || '';
  if (node.type === 'image') return `![${node.attrs?.alt ?? ''}](${node.attrs?.src ?? ''})`;
  if (node.type === 'mathField') {
    const clean = stripPlaceholders(node.attrs?.latex);
    if (!clean) return '';
    return node.attrs?.display ? `$$${clean}$$` : `$${clean}$`;
  }
  return '';
}

/** Serialize a ProseMirror doc JSON back to the stored string. */
export function serializeDoc(doc) {
  return (doc?.content || [])
    .map((p) => (p.content || []).map(serializeInline).join(''))
    .join('\n');
}
