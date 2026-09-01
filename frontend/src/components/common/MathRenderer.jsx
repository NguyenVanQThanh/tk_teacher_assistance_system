// File Name: MathRenderer.jsx
// Description: Pure standard KaTeX LaTeX math renderer (inline $...$, $$...$$, \(...\), \[...\]) preserving backend text integrity.
// Created At: 2026-09-01
// Created By: Tam Khang
// Updated At: 2026-09-01
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

/**
 * Clean standard MathRenderer:
 * Only parses explicit LaTeX delimiters ($...$, $$...$$, \(...\), \[...\])
 * preserving exact backend text without ad-hoc regex alterations.
 */
export default function MathRenderer({ text, className = '' }) {
  const content = useMemo(() => {
    if (!text || typeof text !== 'string') return text || '';

    // Check for standard LaTeX delimiters: $$...$$, $...$, \[...\], \(...\)
    const delimiterPattern = /(\$\$[\s\S]+?\$\$|\$[^\$\n]+?\$|\\\[[\s\S]+?\\\]|\\\([^\n]+?\\\))/g;
    const hasDelimiters = delimiterPattern.test(text);

    if (hasDelimiters) {
      const parts = text.split(delimiterPattern);
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

    // If string itself starts with a LaTeX command like \frac, \sqrt, \vec, \alpha, etc.
    if (text.startsWith('\\')) {
      return (
        <span
          dangerouslySetInnerHTML={{ __html: renderKatex(text, false) }}
        />
      );
    }

    // Default: render exact text from Backend without modification
    return text;
  }, [text]);

  return <span className={`math-renderer-wrapper ${className}`}>{content}</span>;
}
