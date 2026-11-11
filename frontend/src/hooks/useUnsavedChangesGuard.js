/*
File Name: useUnsavedChangesGuard.js
Description: Hook that asks for confirmation before closing an edit modal that has unsaved changes.
Created At: 2026-11-11
Created By: AI Agent
Updated At: 2026-11-11
Updated By: AI Agent
*/
import { useCallback, useEffect, useRef } from 'react';

const CONFIRM_MESSAGE = 'Bạn có thay đổi chưa lưu. Thoát và bỏ các thay đổi này?';

/**
 * @param {*} state JSON-serializable snapshot of everything the user can edit.
 * @param {Function} onClose Raw close handler.
 * @param {boolean} ready True once initial data is loaded; the baseline is captured then.
 * @returns {Function} guardedClose: use for backdrop/X/cancel. Use raw onClose after a successful save.
 */
export default function useUnsavedChangesGuard(state, onClose, ready = true) {
  const current = JSON.stringify(state);
  const currentRef = useRef(current);
  currentRef.current = current;
  const baseline = useRef(null);

  // ponytail: short delay lets async-loaded state settle before the baseline is taken
  useEffect(() => {
    if (!ready) return undefined;
    const t = setTimeout(() => { baseline.current = currentRef.current; }, 400);
    return () => clearTimeout(t);
  }, [ready]);

  return useCallback(() => {
    const dirty = baseline.current !== null && baseline.current !== currentRef.current;
    if (dirty && !window.confirm(CONFIRM_MESSAGE)) return;
    onClose();
  }, [onClose]);
}
