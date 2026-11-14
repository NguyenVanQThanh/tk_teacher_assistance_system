// File Name: MathRenderer.jsx
// Description: Standard KaTeX LaTeX math renderer preserving Vietnamese text spaces, isolating math formulas, and harmonizing exam typography.
// Created At: 2026-09-01
// Created By: Tam Khang
// Updated At: 2026-10-04
// Updated By: Tam Khang

import React, { useMemo } from 'react';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import MarkdownTable from './MarkdownTable';
import { splitTableBlocks } from './tableMarkdown';

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

    // Markdown tables inside the text render as real tables (cells call back into MathRenderer)
    if (text.includes('|') && text.includes('---')) {
      const blocks = splitTableBlocks(text);
      if (blocks.some((b) => b.type === 'table')) {
        return blocks.map((b, i) => (b.type === 'table'
          ? <MarkdownTable key={i} markdown={b.value} />
          : <MathRenderer key={i} text={b.value} />));
      }
    }

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

/**
 * Resolve a media URL (image) to an absolute URL.
 * Relative paths returned by the BE (e.g. /uploads/questions/...) are prefixed
 * with the configured API base URL.
 */
export function resolveMediaUrl(url) {
  if (!url || typeof url !== 'string') return '';
  if (/^(https?:|data:|blob:)/i.test(url)) return url;
  const base = (import.meta.env && import.meta.env.VITE_API_BASE_URL) || '';
  return `${base}${url.startsWith('/') ? '' : '/'}${url}`;
}

const IMAGE_MD_REGEX = /!\[([^\]]*)\]\(([^)\s]+)(?:\s+"[^"]*")?\)/g;

/**
 * Render a single text line: markdown images become <img>, everything else
 * goes through MathRenderer so inline $...$ formulas are visualized.
 */
export function MathInline({ text }) {
  const parts = String(text || '').split(IMAGE_MD_REGEX);
  const out = [];
  for (let i = 0; i < parts.length; i += 3) {
    const pre = parts[i];
    const alt = parts[i + 1];
    const url = parts[i + 2];
    if (pre) out.push(<MathRenderer key={`${i}-t`} text={pre} />);
    if (url !== undefined) {
      out.push(
        <img
          key={`${i}-img`}
          src={resolveMediaUrl(url)}
          alt={alt || ''}
          className="math-content-image"
        />
      );
    }
  }
  return <>{out}</>;
}

/**
 * Render multi-line content safely: blank-line separated blocks, lines that are
 * complete $$...$$ display formulas render as centered formula cards, everything
 * else renders line-by-line. An unclosed $$ while typing falls back to plain text
 * so KaTeX never breaks mid-edit.
 */
export function MathContent({ text, className = '' }) {
  const content = useMemo(() => {
    if (!text || typeof text !== 'string') return null;

    const blocks = text.split(/\n\s*\n/);
    return blocks.map((block, bIdx) => {
      const trimmed = block.trim();
      if (!trimmed) return null;

      if (trimmed.startsWith('$$') && trimmed.endsWith('$$') && trimmed.length > 4) {
        return (
          <div key={bIdx} className="math-content-display">
            <MathRenderer text={trimmed} />
          </div>
        );
      }

      return (
        <div key={bIdx} className="math-content-block">
          {block.split('\n').map((line, lIdx) => {
            const t = line.trim();
            if (!t) return null;
            if (t.startsWith('$$') && t.endsWith('$$') && t.length > 4) {
              return (
                <div key={lIdx} className="math-content-display">
                  <MathRenderer text={t} />
                </div>
              );
            }
            return (
              <div key={lIdx} className="math-content-line">
                <MathInline text={line} />
              </div>
            );
          })}
        </div>
      );
    });
  }, [text]);

  if (!text) return null;
  return <div className={`math-content ${className}`}>{content}</div>;
}
