/*
File Name: MarkdownTable.jsx
Description: Render a parsed markdown table (merged header cells supported) with KaTeX-aware cells.
Created At: 2026-11-12
Created By: AI Agent
Updated At: 2026-11-12
Updated By: AI Agent
*/
import React from 'react';
import MathRenderer from './MathRenderer';
import { parseMarkdownTable } from './tableMarkdown';
import './MarkdownTable.css';

const NUMERIC = /^[-+]?[\d.,\s]+$/;

/** Renders a markdown table string; falls back to a <pre> when it cannot be parsed. */
export default function MarkdownTable({ markdown }) {
  const tbl = parseMarkdownTable(markdown);
  if (!tbl) return <pre className="qm-table-raw">{markdown}</pre>;
  return (
    <div className="qm-table-wrap">
      <table className="qm-table">
        <thead>
          {tbl.headRows.map((hr, ri) => (
            <tr key={ri}>
              {hr.map((h, c) => (
                <th key={c} colSpan={h.colSpan}><MathRenderer text={h.text} /></th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {tbl.rows.map((r, ri) => (
            <tr key={ri}>
              {r.map((cell, c) => (
                <td key={c} className={NUMERIC.test(cell) ? 'qm-num' : ''}><MathRenderer text={cell} /></td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
