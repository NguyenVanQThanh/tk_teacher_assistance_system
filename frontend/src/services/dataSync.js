// File Name: dataSync.js
// Description: Singleton data-version synchronization service. Polls GET /api/v1/sync/version,
// shares the latest version across tabs via localStorage key 'tk_data_version' + BroadcastChannel('tk_data_sync')
// + 'storage' event, and notifies in-tab subscribers so cached pages can refetch when the DB has new data.
// Created At: 2026-11-12
// Created By: Tam Khang

import { syncApi } from './api';

const VERSION_STORAGE_KEY = 'tk_data_version';
const CHANNEL_NAME = 'tk_data_sync';
const DEFAULT_INTERVAL_MS = 5000;   // poll every 5s while tab is visible
const HIDDEN_INTERVAL_MS = 15000;   // poll every 15s while tab is hidden (lighter)
const ERROR_INTERVAL_MS = 30000;    // backoff when /sync/version is not available yet (e.g. 404)
const MIN_INTERVAL_MS = 1000;

const hasWindow = typeof window !== 'undefined';
const hasDocument = typeof document !== 'undefined';
const hasLocalStorage = typeof localStorage !== 'undefined';

const readStoredVersion = () => {
  try {
    return hasLocalStorage ? localStorage.getItem(VERSION_STORAGE_KEY) : null;
  } catch (e) {
    return null;
  }
};

const writeStoredVersion = (v) => {
  try {
    if (hasLocalStorage && localStorage.getItem(VERSION_STORAGE_KEY) !== v) {
      localStorage.setItem(VERSION_STORAGE_KEY, v);
    }
  } catch (e) {}
};

// In-memory current version; seeded from localStorage so an F5 with an unchanged
// server version does NOT count as a "change" (cache stays valid).
let currentVersion = readStoredVersion();
let pollIntervalMs = DEFAULT_INTERVAL_MS;
let started = false;
let timerId = null;
let inFlight = false;
let consecutiveErrors = 0;
let hasLoggedError = false;
let changeDetected = false; // true once a real version change was observed this session

const subscribers = new Set();
let channel = null;

const notify = (version) => {
  subscribers.forEach((cb) => {
    try {
      cb(version);
    } catch (e) {
      console.error('[dataSync] subscriber error:', e);
    }
  });
};

// Version coming from our own tab: poll result or X-Data-Version response header.
const handleServerVersion = (v) => {
  if (!v || typeof v !== 'string') return;
  const stored = readStoredVersion();
  if (v === stored && v === currentVersion) return; // unchanged

  const hadKnown = stored != null;
  if (v !== stored) {
    writeStoredVersion(v);
    // Broadcast to other tabs of this browser so every session refetches too
    try {
      channel?.postMessage({ version: v });
    } catch (e) {}
  }
  const changed = currentVersion !== v;
  currentVersion = v;
  if (changed && hadKnown) {
    changeDetected = true;
    notify(v);
  }
};

// Version coming from ANOTHER tab (BroadcastChannel message or storage event).
const handleRemoteVersion = (v) => {
  if (!v || typeof v !== 'string') return;
  writeStoredVersion(v); // keep localStorage consistent (no-op if identical)
  if (v === currentVersion) return; // already known (dedupes BC + storage double fire)
  currentVersion = v;
  changeDetected = true;
  notify(v);
};

const doCheck = async () => {
  if (inFlight) return;
  inFlight = true;
  try {
    const data = await syncApi.getVersion();
    const v = data?.version;
    if (v) {
      consecutiveErrors = 0;
      handleServerVersion(v);
    }
  } catch (err) {
    // BE may not expose /sync/version yet (404) -> stay quiet, keep retrying slowly,
    // manual "Làm mới" button remains the fallback.
    consecutiveErrors += 1;
    if (!hasLoggedError) {
      hasLoggedError = true;
      console.warn('[dataSync] GET /api/v1/sync/version unavailable (will retry quietly). Falling back to manual refresh only.', err?.message || err);
    }
  } finally {
    inFlight = false;
  }
};

const computeDelay = () => {
  if (hasDocument && document.hidden) return HIDDEN_INTERVAL_MS;
  if (consecutiveErrors >= 3) return ERROR_INTERVAL_MS;
  return pollIntervalMs;
};

const loop = async () => {
  if (!started) return;
  await doCheck();
  if (!started) return;
  timerId = setTimeout(loop, computeDelay());
};

const setupChannel = () => {
  if (!hasWindow || typeof BroadcastChannel === 'undefined') return;
  try {
    channel = new BroadcastChannel(CHANNEL_NAME);
    channel.onmessage = (ev) => {
      const v = ev?.data?.version;
      if (v) handleRemoteVersion(v);
    };
  } catch (e) {
    channel = null;
  }
};

const onStorage = (e) => {
  // Fallback for browsers without BroadcastChannel: fires only in OTHER tabs
  if (e && e.key === VERSION_STORAGE_KEY && e.newValue) {
    handleRemoteVersion(e.newValue);
  }
};

const onVisibilityChange = () => {
  if (hasDocument && !document.hidden) {
    // Tab became visible again -> check immediately instead of waiting for the next tick
    doCheck();
  }
};

const start = () => {
  if (started || !hasWindow) return;
  started = true;
  setupChannel();
  window.addEventListener('storage', onStorage);
  if (hasDocument) document.addEventListener('visibilitychange', onVisibilityChange);
  loop();
};

const stop = () => {
  started = false;
  if (timerId) {
    clearTimeout(timerId);
    timerId = null;
  }
  if (hasWindow) window.removeEventListener('storage', onStorage);
  if (hasDocument) document.removeEventListener('visibilitychange', onVisibilityChange);
  try { channel?.close(); } catch (e) {}
  channel = null;
};

const subscribe = (cb) => {
  if (typeof cb !== 'function') return () => {};
  subscribers.add(cb);
  // If a version change was already detected earlier in this session, deliver it once
  // to late subscribers (e.g. a page that mounted after the change was noticed).
  if (changeDetected && currentVersion) {
    const v = currentVersion;
    setTimeout(() => {
      try { cb(v); } catch (e) { console.error('[dataSync] subscriber error:', e); }
    }, 0);
  }
  return () => { subscribers.delete(cb); };
};

const forceCheck = () => doCheck();

const setPollInterval = (ms) => {
  const n = Number(ms);
  pollIntervalMs = Number.isFinite(n) && n >= MIN_INTERVAL_MS ? n : DEFAULT_INTERVAL_MS;
};

// Called by the axios response interceptor in api.js for every X-Data-Version header.
const notifyHeaderVersion = (v) => {
  if (v) handleServerVersion(v);
};

const dataSync = {
  getVersion: () => currentVersion || readStoredVersion(),
  subscribe,
  forceCheck,
  setPollInterval,
  start,
  stop,
  notifyHeaderVersion,
};

export { VERSION_STORAGE_KEY, CHANNEL_NAME, notifyHeaderVersion };
export default dataSync;

// Auto-start once when this module is imported (guarded, never duplicate-polls).
start();
