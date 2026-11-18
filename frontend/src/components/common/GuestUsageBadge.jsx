// File Name: GuestUsageBadge.jsx
// Description: Guest-only header chip (next to the notification bell) with a quota popover and a limit-reached banner.
// Created At: 2026-11-18
// Created By: AI Agent
// Updated At: 2026-11-18
// Updated By: AI Agent

import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { authApi } from '../../services/api';
import { ERROR_CODE_MESSAGES } from '../../utils/errorMessages';

const ROWS = [
  ['documents', 'Tải tài liệu'],
  ['ai', 'Tạo đề / bài tập AI'],
  ['imports', 'Nhập đề từ tệp'],
];

export default function GuestUsageBadge() {
  const { isGuest } = useAuth();
  const [usage, setUsage] = useState(null);
  const [banner, setBanner] = useState('');
  const [open, setOpen] = useState(false);
  const box = useRef(null);

  const refresh = useCallback(async () => {
    try {
      setUsage((await authApi.getMe()).guest_usage || null);
    } catch {
      /* informational only */
    }
  }, []);

  useEffect(() => {
    if (!isGuest) return undefined;
    refresh();
    const onLimit = (e) => { setBanner(ERROR_CODE_MESSAGES[e.detail] || 'Tài khoản khách đã hết lượt sử dụng.'); setOpen(true); refresh(); };
    const onDown = (e) => { if (box.current && !box.current.contains(e.target)) setOpen(false); };
    document.addEventListener('mousedown', onDown);
    window.addEventListener('guest:usage-changed', refresh);
    window.addEventListener('jobs:finished', refresh);
    window.addEventListener('guest:limit', onLimit);
    const id = setInterval(refresh, 15000);
    return () => {
      clearInterval(id);
      document.removeEventListener('mousedown', onDown);
      window.removeEventListener('guest:usage-changed', refresh);
      window.removeEventListener('jobs:finished', refresh);
      window.removeEventListener('guest:limit', onLimit);
    };
  }, [isGuest, refresh]);

  if (!isGuest || !usage) return null;
  const rows = ROWS.filter(([k]) => usage[k]);
  const anyFull = rows.some(([k]) => usage[k].used >= usage[k].limit);
  return (
    <div ref={box} style={{ position: 'relative' }}>
      <button type="button" onClick={() => setOpen((o) => !o)} aria-expanded={open}
        title="Lượt dùng tài khoản khách"
        style={{ border: `1px solid ${anyFull ? '#C62828' : '#E5E0F0'}`, background: '#fff', borderRadius: 999,
          padding: '4px 10px', fontSize: 12, fontWeight: 600, cursor: 'pointer',
          color: anyFull ? '#C62828' : '#4D308D' }}>
        Khách
      </button>
      {open && (
        <div style={{ position: 'absolute', right: 0, top: 'calc(100% + 8px)', zIndex: 9998, width: 250, background: '#fff',
          border: '1px solid #E5E0F0', borderRadius: 12, padding: 12, fontSize: 13, color: '#2D2342',
          boxShadow: '0 4px 16px rgba(77,48,141,.15)' }}>
          <div style={{ fontWeight: 600, marginBottom: 6 }}>Lượt dùng tài khoản khách</div>
          {rows.map(([k, label]) => {
            const { used, limit } = usage[k];
            return (
              <div key={k} style={{ display: 'flex', justifyContent: 'space-between', color: used >= limit ? '#C62828' : '#6B6480' }}>
                <span>{label}</span><b>{used}/{limit}</b>
              </div>
            );
          })}
          {banner && (
            <div role="alert" style={{ marginTop: 8, padding: 8, borderRadius: 8, background: '#FDECEA', color: '#C62828' }}>
              {banner}
              <button type="button" onClick={() => setBanner('')}
                style={{ marginLeft: 8, border: 0, background: 'none', color: 'inherit', cursor: 'pointer' }}>Đóng</button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
