// File Name: useNotifications.js
// Description: Polling hook for in-app notifications (unread count always, list while the panel is open).
// Created At: 2026-11-15
// Created By: AI Agent
// Updated At: 2026-11-15
// Updated By: AI Agent

import { useCallback, useEffect, useRef, useState } from 'react';
import { notificationApi } from '../services/api';

const POLL_MS = 45000;

export default function useNotifications(isOpen) {
  const [unread, setUnread] = useState(0);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
  const openRef = useRef(isOpen);
  openRef.current = isOpen;

  const refresh = useCallback(async () => {
    try {
      if (openRef.current) {
        setLoading(true);
        const page = await notificationApi.list({ page: 1, page_size: 20 });
        setItems(page.items);
      }
      const c = await notificationApi.unreadCount();
      setUnread(c.unread_count);
      setError(false);
    } catch (e) {
      // Honest error state: no fallback data, the UI shows an error message.
      setError(true);
    } finally {
      setLoading(false);
    }
  }, []);

  // Poll only while the tab is visible; refetch immediately when it becomes visible again.
  useEffect(() => {
    refresh();
    const tick = () => { if (document.visibilityState === 'visible') refresh(); };
    const id = setInterval(tick, POLL_MS);
    document.addEventListener('visibilitychange', tick);
    return () => {
      clearInterval(id);
      document.removeEventListener('visibilitychange', tick);
    };
  }, [refresh]);

  useEffect(() => { if (isOpen) refresh(); }, [isOpen, refresh]);

  const markRead = useCallback(async (id) => {
    try {
      await notificationApi.markRead(id);
      setItems((prev) => prev.map((n) => (n.notification_id === id ? { ...n, is_read: true } : n)));
      setUnread((u) => Math.max(0, u - 1));
    } catch (e) { setError(true); }
  }, []);

  const markAllRead = useCallback(async () => {
    try {
      await notificationApi.markAllRead();
      setItems((prev) => prev.map((n) => ({ ...n, is_read: true })));
      setUnread(0);
    } catch (e) { setError(true); }
  }, []);

  return { unread, items, loading, error, refresh, markRead, markAllRead };
}
