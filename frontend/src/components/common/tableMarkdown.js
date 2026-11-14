// File Name: tableMarkdown.js
// Description: Parse simple GitHub-style markdown tables (header, merged header cells, body) and split text into text/table blocks.
// Created At: 2026-11-12
// Created By: AI Agent
// Updated At: 2026-11-12
// Updated By: AI Agent

// ponytail: GFM pipe tables only (no alignment colons, no escaped pipes). Upgrade to remark-gfm if richer markdown is needed.
const splitRow = (line) => {
  let t = line.trim();
  if (t.startsWith('|')) t = t.slice(1);
  if (t.endsWith('|')) t = t.slice(0, -1);
  return t.split('|').map((c) => c.trim());
};

const isSeparator = (line) => /^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$/.test(line);

// OCR renders a merged header cell as "text | | | |": fold the trailing empty cells into colSpan
const foldHeader = (cells) => {
  const out = [];
  for (const text of cells) {
    if (text === '' && out.length > 0 && out[out.length - 1].text !== '') out[out.length - 1].colSpan += 1;
    else out.push({ text, colSpan: 1 });
  }
  return out;
};

/**
 * Return { headRows: [[{text, colSpan}]], rows: string[][] } or null when the text is not a markdown table.
 * Leading body rows whose first cell is empty are sub-header rows (e.g. "| | 1 phút | 2 phút |").
 */
export function parseMarkdownTable(md) {
  const lines = String(md || '').split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
  if (lines.length < 2 || !lines[0].includes('|') || !isSeparator(lines[1])) return null;
  const width = splitRow(lines[0]).length;
  const norm = (l) => {
    const cells = splitRow(l);
    while (cells.length < width) cells.push('');
    return cells.slice(0, width);
  };
  const headRows = [foldHeader(norm(lines[0]))];
  const rows = lines.slice(2).filter((l) => l.includes('|')).map(norm);
  while (rows.length > 1 && rows[0][0] === '' && rows[0].some((c) => c !== '')) {
    headRows.push(rows.shift().map((text) => ({ text, colSpan: 1 })));
  }
  return { headRows, rows };
}

/** Split text into [{type:'text'|'table', value}] so tables can be rendered separately from prose. */
export function splitTableBlocks(text) {
  const lines = String(text || '').split('\n');
  const out = [];
  let buf = [];
  const flush = () => { if (buf.length) out.push({ type: 'text', value: buf.join('\n') }); buf = []; };
  for (let i = 0; i < lines.length; i += 1) {
    if (lines[i].includes('|') && i + 1 < lines.length && isSeparator(lines[i + 1]) && lines[i].trim().length > 1) {
      let j = i + 2;
      while (j < lines.length && lines[j].includes('|')) j += 1;
      flush();
      out.push({ type: 'table', value: lines.slice(i, j).join('\n') });
      i = j - 1;
    } else buf.push(lines[i]);
  }
  flush();
  return out;
}

/** Build a markdown table template with empty body cells. */
export function buildTableTemplate(rows, cols) {
  const r = Math.max(1, Math.min(20, rows)); const c = Math.max(1, Math.min(10, cols));
  const head = `| ${Array.from({ length: c }, (_, i) => `Cột ${i + 1}`).join(' | ')} |`;
  const sep = `|${Array(c).fill('---').join('|')}|`;
  const body = Array.from({ length: r }, () => `|${Array(c).fill('  ').join('|')}|`);
  return [head, sep, ...body];
}
