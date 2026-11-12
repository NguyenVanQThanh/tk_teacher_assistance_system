// File Name: useExamLockdown.js
// Description: Screen lockdown hook for real (backend) exam taking. While enabled it
// (1) auto-requests fullscreen and re-locks fullscreen when the user exits it,
// (2) detects multi-monitor / extended-display setups via window.screen.isExtended
// (with a geometric fallback) and exposes an overlay state that only clears when a
// single screen is detected again, and (3) releases everything (exitFullscreen,
// listeners) when disabled (after submit or when entering review mode).
// Created At: 2026-11-12
// Created By: AI Agent

import { useState, useEffect, useCallback, useRef } from 'react';

/**
 * Detect an extended / multi-monitor desktop.
 * Primary: window.screen.isExtended (Chromium). Fallback heuristics when undefined:
 * availLeft < 0, availWidth larger than the primary screen width, or window.screenLeft < 0.
 */
export function detectExtendedScreen() {
  try {
    const s = window.screen;
    if (s && typeof s.isExtended === 'boolean') return s.isExtended;
    if (s && (Number(s.availLeft) < 0 || Number(s.availWidth) > Number(s.width) + 1)) return true;
    if (typeof window.screenLeft === 'number' && window.screenLeft < 0) return true;
    return false;
  } catch {
    return false;
  }
}

/**
 * @param {Object} opts
 * @param {boolean} opts.enabled True while a real backend exam is in progress
 *   (isBackendTarget && !submitted && !review). When it flips to false the hook
 *   exits fullscreen and removes every listener.
 * @param {Function} [opts.onFullscreenLost] Called when fullscreen is lost/exit
 *   during lockdown (e.g. wire it to the anti-cheat warning modal).
 * @returns {{isFullscreen: boolean, extendedDetected: boolean,
 *   showMonitorOverlay: boolean, recheckMonitors: Function, requestFullscreen: Function}}
 */
export default function useExamLockdown({ enabled, onFullscreenLost } = {}) {
  const [isFullscreen, setIsFullscreen] = useState(() => Boolean(document.fullscreenElement));
  const [extendedDetected, setExtendedDetected] = useState(() => detectExtendedScreen());

  const enabledRef = useRef(Boolean(enabled));
  enabledRef.current = Boolean(enabled);
  const onLostRef = useRef(onFullscreenLost);
  onLostRef.current = onFullscreenLost;
  // whether WE requested fullscreen (so we only exit fullscreen we entered)
  const requestedRef = useRef(false);
  // becomes true once lockdown was active — used to always release fullscreen on exit
  const wasEnabledRef = useRef(false);

  const requestFullscreen = useCallback(() => {
    if (document.fullscreenElement) {
      setIsFullscreen(true);
      return Promise.resolve();
    }
    const el = document.documentElement;
    if (!el || typeof el.requestFullscreen !== 'function') {
      return Promise.reject(new Error('Fullscreen API not supported'));
    }
    requestedRef.current = true;
    return el.requestFullscreen()
      .then(() => setIsFullscreen(true))
      .catch((err) => {
        requestedRef.current = false;
        throw err;
      });
  }, []);

  /** Manually re-run multi-monitor detection; returns the detected value. */
  const recheckMonitors = useCallback(() => {
    const ext = detectExtendedScreen();
    setExtendedDetected(ext);
    return ext;
  }, []);

  useEffect(() => {
    if (!enabled) {
      // Release: back to a normal screen once lockdown ends (submit / review / unmount)
      if (wasEnabledRef.current && document.fullscreenElement) {
        requestedRef.current = false;
        document.exitFullscreen().catch(() => {});
      }
      wasEnabledRef.current = false;
      setIsFullscreen(Boolean(document.fullscreenElement));
      return undefined;
    }

    wasEnabledRef.current = true;

    // Entering lockdown: auto request fullscreen (full-zoom = fullscreen whole screen)
    requestFullscreen().catch(() => {
      // Likely missing user activation; surface the warning so the user can
      // re-enter fullscreen from the modal button (a real click gesture).
      if (enabledRef.current && !document.fullscreenElement) {
        onLostRef.current?.();
      }
    });

    const onFullscreenChange = () => {
      const fs = Boolean(document.fullscreenElement);
      setIsFullscreen(fs);
      if (!fs && enabledRef.current) {
        // Locked: warn and immediately try to re-enter fullscreen (no way out)
        onLostRef.current?.();
        setTimeout(() => {
          if (!enabledRef.current || document.fullscreenElement) return;
          requestFullscreen().catch(() => {});
        }, 60);
      }
    };

    const onScreenChange = () => {
      if (enabledRef.current) recheckMonitors();
    };

    document.addEventListener('fullscreenchange', onFullscreenChange);
    const scr = window.screen;
    if (scr && typeof scr.addEventListener === 'function') {
      scr.addEventListener('change', onScreenChange);
    }
    // Fallback poll for browsers without the screen 'change' event
    const poll = setInterval(() => {
      if (enabledRef.current) recheckMonitors();
    }, 3000);

    return () => {
      document.removeEventListener('fullscreenchange', onFullscreenChange);
      if (scr && typeof scr.removeEventListener === 'function') {
        scr.removeEventListener('change', onScreenChange);
      }
      clearInterval(poll);
      // Release on disable/unmount: back to normal screen only now (after submit/review)
      if (wasEnabledRef.current && document.fullscreenElement) {
        requestedRef.current = false;
        document.exitFullscreen().catch(() => {});
      }
    };
  }, [enabled, requestFullscreen, recheckMonitors]);

  return {
    isFullscreen,
    extendedDetected,
    // Overlay blocks the whole screen until a single monitor is detected again
    showMonitorOverlay: Boolean(enabled) && extendedDetected,
    recheckMonitors,
    requestFullscreen,
  };
}
