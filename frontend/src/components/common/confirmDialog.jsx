/*
File Name: confirmDialog.jsx
Description: Promise-based themed confirm dialog replacing window.confirm. No provider needed.
Created At: 2026-11-12
Created By: AI Agent
Updated At: 2026-11-12
Updated By: AI Agent
*/
import React from 'react';
import { createRoot } from 'react-dom/client';

const S = {
  overlay: {
    position: 'fixed', inset: 0, zIndex: 100000, display: 'flex', alignItems: 'center',
    justifyContent: 'center', padding: 16, background: 'rgba(51, 43, 79, 0.45)',
    fontFamily: 'Be Vietnam Pro, sans-serif',
  },
  box: {
    width: 'min(420px, 100%)', background: '#FFFFFF', borderRadius: 14, padding: 24,
    boxShadow: '0 20px 50px rgba(77, 48, 141, 0.25)', border: '1px solid #DCD6E8',
  },
  title: { margin: '0 0 8px', fontSize: 17, fontWeight: 700, color: '#332B4F' },
  msg: { margin: '0 0 20px', fontSize: 14, lineHeight: 1.5, color: '#6E6784' },
  row: { display: 'flex', justifyContent: 'flex-end', gap: 10 },
  cancel: {
    padding: '9px 18px', borderRadius: 10, border: '1px solid #DCD6E8', background: '#FFFFFF',
    color: '#4D308D', fontWeight: 600, fontSize: 14, cursor: 'pointer',
  },
  ok: {
    padding: '9px 18px', borderRadius: 10, border: 'none', background: '#4D308D',
    color: '#FFFFFF', fontWeight: 600, fontSize: 14, cursor: 'pointer',
  },
};

function Dialog({ title, message, confirmText, cancelText, onDone }) {
  React.useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') onDone(false); };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [onDone]);
  return (
    <div style={S.overlay} onClick={() => onDone(false)} role="presentation">
      <div style={S.box} role="alertdialog" aria-modal="true" onClick={(e) => e.stopPropagation()}>
        <h3 style={S.title}>{title}</h3>
        <p style={S.msg}>{message}</p>
        <div style={S.row}>
          <button type="button" style={S.cancel} onClick={() => onDone(false)}>{cancelText}</button>
          <button type="button" style={S.ok} autoFocus onClick={() => onDone(true)}>{confirmText}</button>
        </div>
      </div>
    </div>
  );
}

/** Shows the themed dialog; resolves true on confirm, false on cancel/Esc/backdrop. */
export default function confirmDialog(message, { title = 'Xác nhận', confirmText = 'Đồng ý', cancelText = 'Hủy' } = {}) {
  return new Promise((resolve) => {
    const host = document.createElement('div');
    document.body.appendChild(host);
    const root = createRoot(host);
    const onDone = (v) => {
      root.unmount();
      host.remove();
      resolve(v);
    };
    root.render(<Dialog {...{ title, message, confirmText, cancelText, onDone }} />);
  });
}
