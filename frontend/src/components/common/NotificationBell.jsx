// File Name: NotificationBell.jsx
// Description: Shared bell button with unread badge and dropdown list, used by admin, teacher and student headers.
// Created At: 2026-11-15
// Created By: AI Agent
// Updated At: 2026-11-15
// Updated By: AI Agent

import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Bell } from 'lucide-react';
import useNotifications from '../../hooks/useNotifications';
import { badgeText, formatRelativeTime } from '../../utils/notificationUtils';
import './NotificationBell.css';

export default function NotificationBell() {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);
  const navigate = useNavigate();
  const { unread, items, loading, error, markRead, markAllRead } = useNotifications(open);

  useEffect(() => {
    const onDown = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener('mousedown', onDown);
    return () => document.removeEventListener('mousedown', onDown);
  }, []);

  const handleItem = (n) => {
    if (!n.is_read) markRead(n.notification_id);
    if (n.link) { setOpen(false); navigate(n.link); }
  };

  const badge = badgeText(unread);

  return (
    <div className="nbell" ref={ref}>
      <button
        type="button"
        className="nbell-btn"
        onClick={() => setOpen((v) => !v)}
        aria-label={badge ? `Thông báo, ${unread} chưa đọc` : 'Thông báo'}
        title="Thông báo"
      >
        <Bell size={19} />
        {badge && <span className="nbell-badge">{badge}</span>}
      </button>

      {open && (
        <div className="nbell-panel" role="dialog" aria-label="Thông báo">
          <div className="nbell-head">
            <span className="nbell-title">Thông báo</span>
            <button type="button" className="nbell-link" onClick={markAllRead} disabled={unread === 0}>
              Đánh dấu tất cả đã đọc
            </button>
          </div>
          {error && <div className="nbell-error">Không thể tải thông báo. Vui lòng thử lại sau.</div>}
          <div className="nbell-list">
            {loading && items.length === 0 && !error && <div className="nbell-empty">Đang tải...</div>}
            {!loading && !error && items.length === 0 && <div className="nbell-empty">Bạn chưa có thông báo nào.</div>}
            {items.map((n) => (
              <button
                type="button"
                key={n.notification_id}
                className={`nbell-item${n.is_read ? '' : ' unread'}`}
                onClick={() => handleItem(n)}
              >
                <span className="nbell-item-title">{n.title}</span>
                {n.body && <span className="nbell-item-body">{n.body}</span>}
                <span className="nbell-item-time">{formatRelativeTime(n.created_at)}</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
