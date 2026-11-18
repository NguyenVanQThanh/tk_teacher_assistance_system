// File Name: mathPreprocess.js
// Description: Pure helper that wraps standalone math expressions in $...$ delimiters (no React/KaTeX imports).
// Created At: 2026-11-17
// Created By: AI Agent
// Updated At: 2026-11-17
// Updated By: AI Agent

const VIETNAMESE_WORDS = /[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]/i;

/**
 * Preprocess raw text to identify and wrap standalone math expressions into standard $...$ delimiters.
 */
export function preprocessMathText(text) {
  if (!text || typeof text !== 'string') return text || '';

  // 1. Normalize vector arrows and radical root characters
  let str = text
    .replace(/([a-zA-Z])[\u20d7\u2192⃗]/g, '\\vec{$1}')
    .replace(/[\u20d7\u2192⃗]([a-zA-Z])/g, '\\vec{$1}')
    .replace(/\bVectơ\s+([A-Z]{2})\b/g, '\\vec{$1}')
    .replace(/[√\u221a]\s*(\d+)/g, (m, num) => `\\sqrt{${num}}`)
    .replace(/[√\u221a]\s*([a-zA-Z])\b/g, (m, v) => `\\sqrt{${v}}`)
    .replace(/[√\u221a]\s*\(([^)]+)\)/g, (m, expr) => `\\sqrt{${expr}}`)
    .replace(/\\sqrt\s+(\d+)/g, (m, num) => `\\sqrt{${num}}`)
    .replace(/[\r\n\s\.]+[√✓\u221a]\s*$/, '.')
    .replace(/[\r\n\s\.]+\(\s*\)\s*$/, '.');

  // If already contains standard delimiters ($...$ or $$...$$ or \(...\) or \[...\]) across lines, keep as is
  if (/(\$\$[\s\S]+?\$\$|\$[^\$]+?\$|\\\[[\s\S]+?\\\]|\\\([\s\S]+?\\\))/.test(str)) {
    return str;
  }

  // 2. If entire string is a math formula or choice with NO Vietnamese words
  // ponytail: prose (two plain words in a row once \commands are removed) is never wrapped
  const looksLikeProse = /[A-Za-z]{2,}\s+[A-Za-z]{2,}/.test(str.replace(/\\[a-zA-Z]+/g, ''));
  // ponytail: rearrangement answers like "C - A - B" are letters, not math; widen if other letter-dash formats appear
  const isRearrangement = /^[a-e](\s*-\s*[a-e])+$/i.test(str.trim());
  if (!VIETNAMESE_WORDS.test(str) && !looksLikeProse && !isRearrangement) {
    const trimmed = str.replace(/^[A-D]\.\s*/, '').trim();
    if (trimmed.length > 0 && (/[=\\+\-*/^_{}()\[\]<>]/.test(trimmed) || /^-?\d+(\.\d+)?$/.test(trimmed))) {
      const prefix = str.match(/^[A-D]\.\s*/)?.[0] || '';
      // Prevent double wrapping if already starts and ends with $
      if (trimmed.startsWith('$') && trimmed.endsWith('$')) {
        return `${prefix}${trimmed}`;
      }
      return `${prefix}$${trimmed}$`;
    }
  }

  // 3. For mixed Vietnamese + Math text, extract math expressions safely without breaking Vietnamese words
  const regex = /(\\vec\{[a-zA-Z0-9]+\}\s*=\s*\([^)]+\)|[A-Z]\(\s*[-+]?\d+(?:\.\d+)?\s*;\s*[-+]?\d+(?:\.\d+)?(?:\s*;\s*[-+]?\d+(?:\.\d+)?)?\s*\)|[\(\[]\s*[-+]?(?:\d+|\\infty|∞)\s*;\s*[-+]?(?:\d+|\\infty|∞)\s*[\)\]]|\b(?:f|g|h|P|Q)\([a-zA-Z0-9\s;,+-]+\)\s*=\s*(?:\\frac\{[^{}]*\}\{[^{}]*\}|[a-zA-Z0-9\(\)\^\{\}\+\-\*\/\s\.]+)+|\b(?:y|x)\s*=\s*(?:\\frac\{[^{}]*\}\{[^{}]*\}|[a-zA-Z0-9\(\)\^\{\}\+\-\*\/\s\.]+)+|\\(?:frac|sqrt|log|ln|vec|int|sum|lim)(?:_[0-9a-zA-Z\{\}\+\-]+)?(?:\^[0-9a-zA-Z\{\}\+\-]+)?(?:\{[^{}]*\}|\([^\n)]+\))*(?:\s*[=><+\-*\/]\s*[a-zA-Z0-9\(\)\^\{\}\+\-\*\/]+)?|(?<![a-zA-Z\u00C0-\u1EF9])(?:[a-zA-Z0-9]+)\^\{[^{}]+\}(?:\s*[\+\-\*\/=><]\s*[a-zA-Z0-9\^\{\}\+\-\*\/]+)*)/g;

  return str.replace(regex, (match) => {
    if (VIETNAMESE_WORDS.test(match)) return match;
    const cleanMatch = match.trim().replace(/[.,;:]$/, '');
    const trailingPunct = match.slice(cleanMatch.length);
    return `$${cleanMatch}$${trailingPunct}`;
  });
}
