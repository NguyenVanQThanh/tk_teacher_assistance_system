/*
File Name: MathSymbolToolbar.jsx
Description: Compact formula symbol table (subject tabs + symbol chips) that inserts into a MathTextEditor via a callback. Shares its symbol data with the teacher editor.
Created At: 2026-11-12
Created By: AI Agent
Updated At: 2026-11-12
Updated By: AI Agent
*/
import React, { useState } from 'react';
import MathRenderer from './MathRenderer';
import { symbolCategoriesBySubject } from './mathSymbols';

export default function MathSymbolToolbar({ onInsert }) {
  const [tab, setTab] = useState('math');
  const data = symbolCategoriesBySubject[tab] || symbolCategoriesBySubject.math;
  return (
    <section className="formula-toolbar-container">
      <div className="formula-subject-tabs">
        {Object.entries(symbolCategoriesBySubject).map(([key, subj]) => (
          <button
            key={key}
            type="button"
            className={`subject-tab-btn ${tab === key ? 'active' : ''}`}
            onClick={() => setTab(key)}
          >
            <span className="tab-icon">{subj.icon}</span>
            <span>{subj.name}</span>
          </button>
        ))}
      </div>
      <div className="formula-categories-row">
        {data.groups.map((cat) => (
          <div key={cat.group} className="formula-group-seg">
            <span className="formula-group-title">{cat.group}</span>
            <div className="formula-chips-wrap">
              {cat.items.map((item) => (
                <button
                  key={item.code}
                  type="button"
                  className="formula-chip-btn"
                  onMouseDown={(e) => e.preventDefault()}
                  onClick={() => onInsert(item.tpl || item.code)}
                  title={`${item.tip} (${item.code})`}
                >
                  <MathRenderer text={`$${item.display}$`} />
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
