// File Name: MathRenderer.jsx
// Description: Standard KaTeX LaTeX math renderer preserving Vietnamese text spaces and isolating math formulas.
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
 * Clean & resilient MathRenderer:
 * 1. Parses standard LaTeX delimiters ($...$, $$...$$, \(...\), \[...\]).
 * 2. Parses standalone math tokens (e.g., \infty, \frac, \sqrt, \vec).
 * 3. Never renders entire Vietnamese sentences as math mode to preserve spaces.
 */
export default function MathRenderer({ text, className = '' }) {
  const content = useMemo(() => {
    if (!text || typeof text !== 'string') return text || '';

    // If text contains standard LaTeX delimiters, split by delimiter
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

        // Regular text segment: check if there are standalone inline commands like (-\infty; 9) or \vec{a}
        if (/\\[a-zA-Z]+/.test(part) && !/[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]/i.test(part)) {
          return (
            <span
              key={index}
              dangerouslySetInnerHTML={{ __html: renderKatex(part, false) }}
            />
          );
        }

        // Plain text segment
        return <span key={index}>{part}</span>;
      });
    }

    // If string has NO Vietnamese characters and contains LaTeX command or math formula (like "(-\infty;9)", "\vec{a}", "m < -2")
    const hasVietnamese = /[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]/i.test(text);
    if (!hasVietnamese && (/\\[a-zA-Z]+/.test(text) || /^[\s0-9a-zA-Z\(\)\[\]\{\}\+\-\*\/\=\<\>\,\.\;\:\^\|\_]+$/.test(text) && /[=\<\>\^\\\|]/.test(text))) {
      return (
        <span
          dangerouslySetInnerHTML={{ __html: renderKatex(text, false) }}
        />
      );
    }

    // Default: render exact text from Backend without modification to preserve formatting & spaces
    return text;
  }, [text]);

  return <span className={`math-renderer-wrapper ${className}`}>{content}</span>;
}
