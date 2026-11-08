// File Name: MathLiveEditor.jsx
// Description: Live "WYSIWYG" math editor: a transparent textarea (real caret/selection)
// sits on top of a rendered backdrop, so inserted LaTeX snippets are visualized
// immediately via KaTeX instead of showing raw LaTeX code while editing.
// Created At: 2026-11-08
// Created By: Tam Khang

import React, { forwardRef, useCallback, useRef } from 'react';
import { MathContent } from './MathRenderer';

const MathLiveEditor = forwardRef(function MathLiveEditor(
  { value, onChange, onFocus, onBlur, onKeyDown, placeholder, rows = 7, className = '', disabled = false },
  ref
) {
  const backdropRef = useRef(null);
  const innerRef = useRef(null);

  const setRefs = useCallback(
    (el) => {
      innerRef.current = el;
      if (typeof ref === 'function') ref(el);
      else if (ref) ref.current = el;
    },
    [ref]
  );

  // Keep the rendered backdrop aligned with the textarea scroll position.
  const handleScroll = useCallback(() => {
    const ta = innerRef.current;
    const bd = backdropRef.current;
    if (ta && bd) {
      bd.scrollTop = ta.scrollTop;
      bd.scrollLeft = ta.scrollLeft;
    }
  }, []);

  return (
    <div
      className={`math-live-editor ${className}`}
      style={{ minHeight: `${Math.round(rows * 1.55 * 12.5) + 20}px` }}
    >
      <div ref={backdropRef} className="math-live-backdrop" aria-hidden="true">
        <MathContent text={value} />
        {!value && placeholder ? (
          <span className="math-live-placeholder">{placeholder}</span>
        ) : null}
        {'\n'}
      </div>
      <textarea
        ref={setRefs}
        className="math-live-textarea"
        value={value}
        onChange={(e) => onChange && onChange(e.target.value)}
        onScroll={handleScroll}
        onFocus={onFocus}
        onBlur={onBlur}
        onKeyDown={onKeyDown}
        spellCheck={false}
        disabled={disabled}
      />
    </div>
  );
});

export default MathLiveEditor;
