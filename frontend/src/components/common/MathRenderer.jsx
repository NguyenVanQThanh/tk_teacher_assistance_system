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
import { splitCodeBlocks, splitInlineCode } from '../../utils/codeMarkdown';
import { preprocessMathText } from '../../utils/mathPreprocess';

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


/** Fenced code block; code is a React text child (never raw HTML). */
export function CodeBlock({ code, lang }) {
  return <pre className="code-block" data-lang={lang}><code>{code}</code></pre>;
}

/**
 * MathRenderer component for rendering LaTeX formulas cleanly across Vietnamese text.
 * Harmonizes font family with academic serif style ('Times New Roman', 'KaTeX_Main', Times, serif).
 */
export default function MathRenderer({ text, className = '' }) {
  const content = useMemo(() => {
    if (!text || typeof text !== 'string') return text || '';

    // Code fences and inline code render verbatim (no math/table processing)
    if (text.includes('```')) {
      return splitCodeBlocks(text).map((b, i) => (b.type === 'code'
        ? <CodeBlock key={i} code={b.value} lang={b.lang} />
        : <MathRenderer key={i} text={b.value} />));
    }
    if (text.includes('`')) {
      return splitInlineCode(text).map((b, i) => (b.type === 'code'
        ? <code key={i} className="code-inline">{b.value}</code>
        : <MathRenderer key={i} text={b.value} />));
    }

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
