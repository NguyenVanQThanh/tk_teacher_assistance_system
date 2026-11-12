// File Name: useDataSync.js
// Description: React hook that subscribes to the dataSync singleton. Returns the current backend
// data version and a checkNow() trigger; calls onChange(version) whenever the version changes
// (new data in DB detected via polling / X-Data-Version header / other tabs).
// Created At: 2026-11-12
// Created By: Tam Khang

import { useState, useEffect, useRef, useCallback } from 'react';
import dataSync from '../services/dataSync';

export default function useDataSync(onChange) {
  const [version, setVersion] = useState(() => dataSync.getVersion());

  // Keep latest onChange in a ref so the subscription never needs to re-bind
  // when the parent passes a new callback identity.
  const onChangeRef = useRef(onChange);
  useEffect(() => {
    onChangeRef.current = onChange;
  }, [onChange]);

  useEffect(() => {
    const unsubscribe = dataSync.subscribe((v) => {
      setVersion(v);
      try {
        onChangeRef.current?.(v);
      } catch (e) {
        console.error('[useDataSync] onChange error:', e);
      }
    });
    return unsubscribe;
  }, []);

  const checkNow = useCallback(() => {
    dataSync.forceCheck();
  }, []);

  return { version, checkNow };
}
