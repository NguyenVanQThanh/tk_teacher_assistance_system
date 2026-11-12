// File Name: QuestionContentView.jsx
// Description: Renders one question content segment exactly like the teacher's edit
// page (EditExerciseModal renderLiveContent): markdown tables become MarkdownTable,
// blank-line separated blocks are split per line, standalone $$...$$ lines render as
// formula cards, and normal lines go through MathInline so inline $...$ math AND
// markdown images ![]() both work.
// Created At: 2026-11-12
// Created By: AI Agent

import React, { useMemo } from 'react';
import MathRenderer, { MathInline } from './MathRenderer';
import MarkdownTable from './MarkdownTable';
import { splitTableBlocks } from './tableMarkdown';
import './QuestionContentView.css';

const isDisplayFormula = (t) => t.startsWith('$$') && t.endsWith('$$') && t.length > 4;

/**
 * Render the non-table part of a content string: blocks split by blank lines;
 * a block (or single line) that is exactly $$...$$ becomes a formula card;
 * every other line renders through MathInline (KaTeX + inline markdown images).
 * Returns an array of React nodes (mirrors renderLiveText of the edit page).
 */
export function renderQuestionTextBlocks(rawText) {
  if (!rawText || !rawText.trim()) return null;
  const blocks = rawText.split(/\n\s*\n/);
  return blocks.map((block, bIdx) => {
    const trimmed = block.trim();
    if (!trimmed) return null;

    if (isDisplayFormula(trimmed)) {
      return (
        <div key={`f${bIdx}`} className="qcv-formula-card">
          <MathRenderer text={trimmed} />
        </div>
      );
    }

    return (
      <div key={`b${bIdx}`} className="qcv-text-block">
        {block.split('\n').map((line, lIdx) => {
          const t = line.trim();
          if (!t) return null;
          if (isDisplayFormula(t)) {
            return (
              <div key={`f${bIdx}-${lIdx}`} className="qcv-formula-card">
                <MathRenderer text={t} />
              </div>
            );
          }
          return (
            <div key={`l${bIdx}-${lIdx}`} className="qcv-text-line">
              <MathInline text={line} />
            </div>
          );
        })}
      </div>
    );
  });
}

/**
 * Full content renderer (mirrors renderLiveContent of the edit page):
 * splitTableBlocks first so markdown tables render as real tables; the remaining
 * text blocks go through renderQuestionTextBlocks.
 * Returns an array of React nodes.
 */
export function renderQuestionContent(text) {
  if (!text || typeof text !== 'string' || !text.trim()) return null;
  const parts = splitTableBlocks(text);
  return parts.map((part, pIdx) => (part.type === 'table'
    ? <MarkdownTable key={`t${pIdx}`} markdown={part.value} />
    : <React.Fragment key={`x${pIdx}`}>{renderQuestionTextBlocks(part.value)}</React.Fragment>));
}

/**
 * Component wrapper around renderQuestionContent.
 * Props: text (string), className (optional extra class on the wrapper).
 */
export default function QuestionContentView({ text, className = '' }) {
  const content = useMemo(() => renderQuestionContent(text), [text]);
  if (!text || typeof text !== 'string' || !text.trim()) return null;
  return <div className={`question-content-view ${className}`}>{content}</div>;
}
