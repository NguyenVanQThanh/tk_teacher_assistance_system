/*
File Name: toast.jsx
Description: Themed non-blocking toast replacing window.alert. No provider needed:
             toast('msg'), toast.success('msg'), toast.error('msg'), toast.info('msg').
Created At: 2026-11-13
Created By: AI Agent
Updated At: 2026-11-13
Updated By: AI Agent
*/
import React from 'react';
import { createRoot } from 'react-dom/client';

const COLORS = {
  success: { bg: '#ECFDF5', border: '#A7F3D0', fg: '#065F46', icon: '\u2713' },
  error: { bg: '#FEF2F2', border: '#FECACA', fg: '#991B1B', icon: '!' },
  info: { bg: '#F3EFFB', border: '#DCD6E8', fg: '#4D308D', icon: 'i' },
};
const DURATION_MS = 4000;

let root = null;
let host = null;
let items = [];
let nextId = 1;

function Stack() {
  return (
    <div
      role="status"
      aria-live="polite"
      style={{
        position: 'fixed', top: 20, right: 20, zIndex: 100001, display: 'flex',
        flexDirection: 'column', gap: 10, maxWidth: 'min(380px, calc(100vw - 32px))',
        fontFamily: 'Be Vietnam Pro, sans-serif',
      }}
    >
      {items.map((t) => {
        const c = COLORS[t.type];
        return (
          <div
            key={t.id}
            onClick={() => dismiss(t.id)}
            style={{
              display: 'flex', alignItems: 'flex-start', gap: 10, padding: '12px 14px', cursor: 'pointer',
              background: c.bg, border: `1px solid ${c.border}`, color: c.fg, borderRadius: 12,
              boxShadow: '0 10px 30px rgba(77, 48, 141, 0.18)', fontSize: 14, lineHeight: 1.45,
            }}
          >
            <span
              aria-hidden="true"
              style={{
                flex: '0 0 20px', height: 20, borderRadius: '50%', background: c.fg, color: '#fff',
                fontSize: 12, fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}
            >
              {c.icon}
            </span>
            <span style={{ whiteSpace: 'pre-line', wordBreak: 'break-word' }}>{t.message}</span>
          </div>
        );
      })}
    </div>
  );
}

function render() {
  if (!host) {
    host = document.createElement('div');
    document.body.appendChild(host);
    root = createRoot(host);
  }
  root.render(<Stack />);
}

function dismiss(id) {
  items = items.filter((t) => t.id !== id);
  render();
}

function show(type, message) {
  const id = nextId++;
  items = [...items, { id, type, message: String(message ?? '') }];
  render();
  setTimeout(() => dismiss(id), DURATION_MS);
}

const toast = (message) => show('info', message);
toast.info = (message) => show('info', message);
toast.success = (message) => show('success', message);
toast.error = (message) => show('error', message);

export default toast;
