// File Name: CredentialModal.jsx
// Description: One-time modal showing a server-generated temporary password with a copy button; never persisted.
// Created At: 2026-11-15
// Created By: AI Agent
// Updated At: 2026-11-15
// Updated By: AI Agent

import React, { useState } from 'react';

const overlay = { position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.45)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 2000, padding: 16 };
const card = { background: '#fff', borderRadius: 14, padding: 24, width: '100%', maxWidth: 440, fontFamily: 'Be Vietnam Pro, sans-serif', color: '#332B4F' };

/**
 * @param {{ title: string, fullName?: string, code?: string, phone?: string, email?: string, temporaryPassword: string } | null} result
 * The password lives only in the parent's state; closing calls onClose so the parent clears it.
 */
export default function CredentialModal({ result, onClose }) {
  const [copied, setCopied] = useState(false);
  if (!result) return null;

  const handleClose = () => { setCopied(false); onClose(); };
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(result.temporaryPassword || '');
      setCopied(true);
    } catch (err) {
      console.error('Clipboard copy failed:', err);
    }
  };

  return (
    <div style={overlay} role="dialog" aria-modal="true" data-testid="credential-modal">
      <div style={card} onClick={(e) => e.stopPropagation()}>
        <h3 style={{ margin: '0 0 12px', fontSize: 18 }}>{result.title || 'Thông tin đăng nhập'}</h3>
        {result.fullName && <p style={{ margin: '0 0 4px' }}>Người dùng: <strong>{result.fullName}</strong></p>}
        {result.code && <p style={{ margin: '0 0 4px' }}>Mã định danh: <strong>{result.code}</strong></p>}
        {result.phone && <p style={{ margin: '0 0 4px' }}>Số điện thoại: <strong>{result.phone}</strong></p>}
        <p style={{ margin: '12px 0 6px' }}>Mật khẩu tạm thời:</p>
        <div style={{ display: 'flex', gap: 8 }}>
          <code data-testid="credential-password" style={{ flex: 1, padding: '10px 12px', background: '#F3ECFF', borderRadius: 8, fontSize: 16, wordBreak: 'break-all' }}>
            {result.temporaryPassword}
          </code>
          <button type="button" onClick={handleCopy} style={{ padding: '0 14px', borderRadius: 8, border: '1px solid #DCD6E8', background: '#fff', color: '#4D308D', fontWeight: 600, cursor: 'pointer' }}>
            {copied ? 'Đã sao chép' : 'Sao chép'}
          </button>
        </div>
        <p style={{ fontSize: 12, color: '#B45309', margin: '10px 0 16px' }}>
          Mật khẩu chỉ hiển thị một lần. Hãy sao chép và gửi cho người dùng trước khi đóng.
        </p>
        <div style={{ textAlign: 'right' }}>
          <button type="button" onClick={handleClose} style={{ padding: '9px 18px', borderRadius: 10, border: 'none', background: '#4D308D', color: '#fff', fontWeight: 600, cursor: 'pointer' }}>
            Đóng
          </button>
        </div>
      </div>
    </div>
  );
}
