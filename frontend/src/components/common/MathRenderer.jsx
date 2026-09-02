// File Name: MathRenderer.jsx
// Description: Standard KaTeX LaTeX math renderer preserving Vietnamese text spaces and isolating math formulas.
// Created At: 2026-09-01
// Created By: Tam Khang
// Updated At: 2026-09-02
// Updated By: Tam Khang

import React, { useMemo } from 'react';
import katex from 'katex';
import 'katex/dist/katex.min.css';

/**
 * Safely render a LaTeX math string to HTML using KaTeX.
 */
function renderKatex(mathStr, displayMode = false) {
  try {
    return katex.renderToString(mathStr, {
      displayMode,
      throwOnError: false,
      output: 'htmlAndMathml',
    });
  } catch {
    return mathStr;
  }
}

const VIETNAMESE_WORDS = /[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]/i;

/**
 * Preprocess raw text to identify and wrap standalone math expressions into standard $...$ delimiters.
 */
function preprocessMathText(text) {
  if (!text || typeof text !== 'string') return text || '';

  // 1. Normalize vector arrow characters
  let str = text
    .replace(/([a-zA-Z])[\u20d7\u2192⃗]/g, '\\vec{$1}')
    .replace(/[\u20d7\u2192⃗]([a-zA-Z])/g, '\\vec{$1}');

  // If already contains standard delimiters ($...$ or $$...$$ or \(...\) or \[...\]), keep as is
  if (/(\$\$[\s\S]+?\$\$|\$[^\$\n]+?\$|\\\[[\s\S]+?\\\]|\\\([^\n]+?\\\))/.test(str)) {
    return str;
  }

  // 2. If entire string is a math formula or choice with NO Vietnamese words
  if (!VIETNAMESE_WORDS.test(str)) {
    const trimmed = str.replace(/^[A-D]\.\s*/, '').trim();
    if (trimmed.length > 0 && (/[=\\+\-*/^_{}()\[\]<>]/.test(trimmed) || /^-?\d+(\.\d+)?$/.test(trimmed))) {
      const prefix = str.match(/^[A-D]\.\s*/)?.[0] || '';
      return `${prefix}$${trimmed}$`;
    }
  }

  // 3. For mixed Vietnamese + Math text, extract math expressions
  const regex = /(\\vec\{[a-zA-Z0-9]+\}\s*=\s*\([^)]+\)|[A-Z]\(\s*[-+]?\d+(?:\.\d+)?\s*;\s*[-+]?\d+(?:\.\d+)?(?:\s*;\s*[-+]?\d+(?:\.\d+)?)?\s*\)|[\(\[]\s*[-+]?(?:\d+|\\infty|∞)\s*;\s*[-+]?(?:\d+|\\infty|∞)\s*[\)\]]|\b(?:f|g|h|P|Q)\([a-zA-Z0-9\s;,+-]+\)\s*=\s*(?:\\frac\{[^{}]*\}\{[^{}]*\}|[a-zA-Z0-9\(\)\^\{\}\+\-\*\/\s\.]+)+|\b(?:y|x)\s*=\s*(?:\\frac\{[^{}]*\}\{[^{}]*\}|[a-zA-Z0-9\(\)\^\{\}\+\-\*\/\s\.]+)+|\\(?:frac|sqrt|log|ln|vec|int|sum|lim)(?:_[0-9a-zA-Z\{\}\+\-]+)?(?:\^[0-9a-zA-Z\{\}\+\-]+)?(?:\{[^{}]*\}|\([^\n)]+\))*(?:\s*[=><+\-*\/]\s*[a-zA-Z0-9\(\)\^\{\}\+\-\*\/]+)?|[a-zA-Z0-9]+\^\{[^{}]+\}(?:\s*[\+\-\*\/=><]\s*[a-zA-Z0-9\^\{\}\+\-\*\/]+)*)/g;

  return str.replace(regex, (match) => {
    if (VIETNAMESE_WORDS.test(match)) return match;
    const cleanMatch = match.trim().replace(/[.,;:]$/, '');
    const trailingPunct = match.slice(cleanMatch.length);
    return `$${cleanMatch}$${trailingPunct}`;
  });
}

/**
 * MathRenderer component for rendering LaTeX formulas cleanly across Vietnamese text.
 */
export default function MathRenderer({ text, className = '' }) {
  const content = useMemo(() => {
    if (!text || typeof text !== 'string') return text || '';

    const formattedText = preprocessMathText(text);

    // Split by standard LaTeX delimiters
    const delimiterPattern = /(\$\$[\s\S]+?\$\$|\$[^\$\n]+?\$|\\\[[\s\S]+?\\\]|\\\([^\n]+?\\\))/g;
    const hasDelimiters = delimiterPattern.test(formattedText);

    if (hasDelimiters) {
      const parts = formattedText.split(delimiterPattern);
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

