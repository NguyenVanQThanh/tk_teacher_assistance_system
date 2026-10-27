// File Name: MathRenderer.jsx
// Description: Standard KaTeX LaTeX math renderer preserving Vietnamese text spaces, isolating math formulas, and harmonizing exam typography.
// Created At: 2026-09-01
// Created By: Tam Khang
// Updated At: 2026-10-04
// Updated By: Tam Khang

import React, { useMemo } from 'react';
import katex from 'katex';
import 'katex/dist/katex.min.css';

/**
 * Safely render a LaTeX math string to HTML using KaTeX.
 * Handles newline cleanups, delimiter stripping, and auto-escapes standard math operators.
 */
function renderKatex(mathStr, displayMode = false) {
  if (!mathStr || typeof mathStr !== 'string') return '';

  let clean = mathStr.trim();

  // Strip accidental outer delimiters if present
  if (clean.startsWith('$$') && clean.endsWith('$$') && clean.length >= 4) {
    clean = clean.slice(2, -2).trim();
  } else if (clean.startsWith('$') && clean.endsWith('$') && clean.length >= 2) {
    clean = clean.slice(1, -1).trim();
  } else if (clean.startsWith('\\[') && clean.endsWith('\\]') && clean.length >= 4) {
    clean = clean.slice(2, -2).trim();
  } else if (clean.startsWith('\\(') && clean.endsWith('\\)') && clean.length >= 4) {
    clean = clean.slice(2, -2).trim();
  }

  // Replace internal newlines or carriage returns with spaces to prevent KaTeX parse errors
  clean = clean.replace(/[\r\n]+/g, ' ');

  // Auto-prefix unescaped standard functions (ln, log, sin, cos, tan, cot, lim, exp)
  clean = clean.replace(/(?<!\\)\b(ln|log|sin|cos|tan|cot|lim|exp|arcsin|arccos|arctan)\b/g, '\\$1');

  // Normalize radical unicode symbol √ to \sqrt{...}
  clean = clean.replace(/[√\u221a]\s*(\d+)/g, (m, num) => `\\sqrt{${num}}`);
  clean = clean.replace(/[√\u221a]\s*([a-zA-Z])\b/g, (m, v) => `\\sqrt{${v}}`);
  clean = clean.replace(/\\sqrt\s+(\d+)/g, (m, num) => `\\sqrt{${num}}`);

  try {
    return katex.renderToString(clean, {
      displayMode,
      throwOnError: false,
      output: 'htmlAndMathml',
    });
  } catch {
    return clean;
  }
}

const VIETNAMESE_WORDS = /[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]/i;

/**
 * Preprocess raw text to identify and wrap standalone math expressions into standard $...$ delimiters.
 */
function preprocessMathText(text) {
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
  if (!VIETNAMESE_WORDS.test(str)) {
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

/**
 * MathRenderer component for rendering LaTeX formulas cleanly across Vietnamese text.
 * Harmonizes font family with academic serif style ('Times New Roman', 'KaTeX_Main', Times, serif).
 */
export default function MathRenderer({ text, className = '' }) {
  const content = useMemo(() => {
    if (!text || typeof text !== 'string') return text || '';

    const formattedText = preprocessMathText(text);

    // Split by standard LaTeX delimiters without regex lastIndex leak
    const delimiterPattern = /(\$\$[\s\S]+?\$\$|\$[^\$]+?\$|\\\[[\s\S]+?\\\]|\\\([\s\S]+?\\\))/g;
    const parts = formattedText.split(delimiterPattern);

    if (parts.length > 1) {
      return parts.map((part, index) => {
        if (!part) return null;

        // Display math: $$...$$
        if (part.startsWith('$$') && part.endsWith('$$')) {
          const math = part.slice(2, -2).trim();
          return (
            <span
              key={index}
              dangerouslySetInnerHTML={{ __html: renderKatex(math, true) }}
            />
          );
        }

        // Inline math: $...$
        if (part.startsWith('$') && part.endsWith('$')) {
          const math = part.slice(1, -1).trim();
          return (
            <span
              key={index}
              dangerouslySetInnerHTML={{ __html: renderKatex(math, false) }}
            />
          );
        }

        // Display math: \[...\]
        if (part.startsWith('\\[') && part.endsWith('\\]')) {
          const math = part.slice(2, -2).trim();
          return (
            <span
              key={index}
              dangerouslySetInnerHTML={{ __html: renderKatex(math, true) }}
            />
          );
        }

        // Inline math: \(...\)
        if (part.startsWith('\\(') && part.endsWith('\\)')) {
          const math = part.slice(2, -2).trim();
          return (
            <span
              key={index}
              dangerouslySetInnerHTML={{ __html: renderKatex(math, false) }}
            />
          );
        }

        // Plain text segment
        return <span key={index}>{part}</span>;
      });
    }

    return formattedText;
  }, [text]);

  return <span className={`math-renderer-wrapper ${className}`}>{content}</span>;
}

