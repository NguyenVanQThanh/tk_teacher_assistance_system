// File Name: GuestLock.jsx
// Description: Wrapper rendering its children as a disabled item with a badge when the signed-in user is a guest.
// Created At: 2026-11-15
// Created By: AI Agent
// Updated At: 2026-11-15
// Updated By: AI Agent

import React from 'react';
import { useAuth } from '../../context/AuthContext';

export const GUEST_LOCK_LABEL = 'Tính năng bị vô hiệu hóa';

/**
 * Renders children unchanged for non-guests (or when `locked` is false);
 * otherwise renders them inert, dimmed, with a small badge.
 */
export default function GuestLock({ locked = true, children, block = false }) {
  const { isGuest } = useAuth();
  if (!isGuest || !locked) return children;
  return (
    <div
      title={GUEST_LOCK_LABEL}
      style={{ position: 'relative', display: block ? 'block' : 'inline-flex', flexDirection: 'column', maxWidth: '100%' }}
    >
      {/* React 18 has no boolean `inert` prop; the empty string renders the native attribute, which also blocks keyboard focus. */}
      <div aria-disabled="true" style={{ opacity: 0.45, pointerEvents: 'none', userSelect: 'none' }} inert="">
        {children}
      </div>
      <span
        style={{
          position: 'absolute', top: 2, right: 2, fontSize: 10, fontWeight: 600, lineHeight: 1.2,
          padding: '2px 6px', borderRadius: 8, background: '#E9DDFF', color: '#4D308D', whiteSpace: 'nowrap',
        }}
      >
        {GUEST_LOCK_LABEL}
      </span>
    </div>
  );
}
