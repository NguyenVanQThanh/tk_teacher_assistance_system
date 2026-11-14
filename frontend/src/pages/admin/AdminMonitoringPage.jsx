// File Name: AdminMonitoringPage.jsx
// Description: Admin realtime system monitoring dashboard: KPI cards, alerts, SVG latency/throughput
//              chart, status distribution, top routes, slowest requests and a filterable recent-request
//              table. Summary data arrives through the authenticated SSE stream (fetch + ReadableStream)
//              with exponential-backoff reconnects and a 5s polling fallback.
// Created At: 2026-11-13
// Created By: AI Agent
// Updated At: 2026-11-13
// Updated By: AI Agent

import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Activity,
  AlertTriangle,
  BarChart3,
  Clock,
  Filter,
  Gauge,
  Inbox,
  Loader2,
  RefreshCw,
  Search,
  ShieldAlert,
  Timer,
  Users,
  X,
} from 'lucide-react';
import { monitoringApi } from '../../services/api';
import './AdminMonitoringPage.css';

const WINDOW_OPTIONS = [
  { value: 60, label: '1 phút' },
  { value: 300, label: '5 phút' },
  { value: 900, label: '15 phút' },
  { value: 3600, label: '1 giờ' },
];

const STATUS_ROWS = [
  { key: '2xx', label: 'Thành công', className: 'is-2xx' },
  { key: '3xx', label: 'Chuyển hướng', className: 'is-3xx' },
  { key: '4xx', label: 'Lỗi phía client', className: 'is-4xx' },
  { key: '5xx', label: 'Lỗi phía server', className: 'is-5xx' },
];

const EMPTY_ARRAY = [];
const API_BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/+$/, '');
const STREAM_PATH = '/api/v1/admin/monitoring/stream';
const POLL_INTERVAL_MS = 5000;
const RECONNECT_DELAYS = [1000, 2000, 5000, 10000];
const RECENT_LIMIT = 50;

function formatNumber(value, maximumFractionDigits = 0) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return '0';
  return numeric.toLocaleString('vi-VN', {
    maximumFractionDigits,
    minimumFractionDigits: 0,
  });
}

function formatCompact(value) {
  const numeric = Number(value) || 0;
  const absolute = Math.abs(numeric);
  if (absolute >= 1000000) {
    return `${(numeric / 1000000).toFixed(1).replace('.', ',')}M`;
  }
  if (absolute >= 1000) {
    const digits = absolute >= 10000 ? 0 : 1;
    return `${(numeric / 1000).toFixed(digits).replace('.', ',')}k`;
  }
  if (absolute === 0) return '0';
  if (absolute >= 10) return String(Math.round(numeric));
  return numeric.toFixed(1).replace('.', ',');
}

function formatMs(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return '—';
  return `${formatNumber(numeric, numeric < 10 ? 1 : 0)} ms`;
}

function formatPercent(rate, digits = 2) {
  const numeric = Number(rate);
  if (!Number.isFinite(numeric)) return '0%';
  return numeric.toLocaleString('vi-VN', {
    style: 'percent',
    maximumFractionDigits: digits,
    minimumFractionDigits: 0,
  });
}

function formatTime(value) {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '—';
  return date.toLocaleTimeString('vi-VN');
}

function formatChartTime(value, withSeconds = false) {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  return date.toLocaleTimeString(
    'vi-VN',
    withSeconds
      ? { hour: '2-digit', minute: '2-digit', second: '2-digit' }
      : { hour: '2-digit', minute: '2-digit' }
  );
}

function shortId(value) {
  if (!value) return '—';
  const text = String(value);
  return text.length > 10 ? `${text.slice(0, 8)}…` : text;
}

function shortUserRef(value) {
  if (!value) return '—';
  const text = String(value);
  return text.length > 18 ? `${text.slice(0, 16)}…` : text;
}

function statusClass(code) {
  const numeric = Number(code);
  if (numeric >= 500) return 'is-5xx';
  if (numeric >= 400) return 'is-4xx';
  if (numeric >= 300) return 'is-3xx';
  if (numeric >= 200) return 'is-2xx';
  if (numeric >= 100) return 'is-1xx';
  return 'is-other';
}

function alertText(alert) {
  if (!alert) return '';
  if (alert.type === 'latency_p95') {
    return `Độ trễ P95 ${formatMs(alert.value)} vượt ngưỡng ${formatMs(alert.threshold)}.`;
  }
  if (alert.type === 'error_rate') {
    return `Tỷ lệ lỗi ${formatPercent(alert.value)} vượt ngưỡng ${formatPercent(alert.threshold)}.`;
  }
  return alert.message || 'Cảnh báo hệ thống';
}

function StatusBadge({ code }) {
  const numeric = Number(code);
  const hasCode = Number.isFinite(numeric) && numeric > 0;
  return (
    <span className={`mon-status-badge ${hasCode ? statusClass(numeric) : 'is-other'}`}>
      {hasCode ? numeric : '—'}
    </span>
  );
}

function KpiCard({ icon: Icon, label, value, hint, tone = 'default', loading = false }) {
  return (
    <article className={`mon-kpi-card ${tone === 'warning' ? 'is-warning' : ''}`}>
      <div className="mon-kpi-top">
        <div className="mon-kpi-icon">
          <Icon size={17} strokeWidth={2.1} />
        </div>
        <span className="mon-kpi-label">{label}</span>
      </div>
      <div className="mon-kpi-value">{loading ? '—' : value}</div>
      {hint && <div className="mon-kpi-hint">{hint}</div>}
    </article>
  );
}

function EmptyState({ icon: Icon = Inbox, title = 'Chưa có dữ liệu', description }) {
  return (
    <div className="mon-empty">
      <div className="mon-empty-icon">
        <Icon size={22} strokeWidth={1.9} />
      </div>
      <p className="mon-empty-title">{title}</p>
      {description && <p className="mon-empty-desc">{description}</p>}
    </div>
  );
}

function LoadingState({ label = 'Đang tải dữ liệu…' }) {
  return (
    <div className="mon-table-loading">
      <Loader2 size={18} className="mon-spin" />
      <span>{label}</span>
    </div>
  );
}

function Panel({ title, subtitle, actions, children, className = '' }) {
  return (
    <section className={`mon-panel ${className}`}>
      <div className="mon-panel-header">
        <div className="mon-panel-heading">
          <h2 className="mon-panel-title">{title}</h2>
          {subtitle && <p className="mon-panel-subtitle">{subtitle}</p>}
        </div>
        {actions && <div className="mon-panel-actions">{actions}</div>}
      </div>
      <div className="mon-panel-body">{children}</div>
    </section>
  );
}

export default function AdminMonitoringPage() {
  const navigate = useNavigate();

  const [windowSeconds, setWindowSeconds] = useState(300);
  const [summary, setSummary] = useState(null);
  const [summaryLoading, setSummaryLoading] = useState(true);
  const [summaryError, setSummaryError] = useState('');
  const [lastUpdated, setLastUpdated] = useState(null);
  const [connectionState, setConnectionState] = useState('connecting');
  const [streamError, setStreamError] = useState('');
  const [pollingFallback, setPollingFallback] = useState(false);
  const [streamWindow, setStreamWindow] = useState(null);
  const [authExpired, setAuthExpired] = useState(false);

  const [requests, setRequests] = useState([]);
  const [requestsLoading, setRequestsLoading] = useState(true);
  const [requestsError, setRequestsError] = useState('');
  const [routeInput, setRouteInput] = useState('');
  const [routeFilter, setRouteFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  const [hoveredIndex, setHoveredIndex] = useState(null);
  const [chartWidth, setChartWidth] = useState(760);

  const mountedRef = useRef(true);
  const requestsSeqRef = useRef(0);
  const chartRef = useRef(null);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const windowLabel = useMemo(
    () => WINDOW_OPTIONS.find((option) => option.value === windowSeconds)?.label || `${windowSeconds}s`,
    [windowSeconds]
  );

  const fetchSummary = useCallback(async () => {
    setSummaryLoading(true);
    try {
      const data = await monitoringApi.getSummary(windowSeconds);
      if (!mountedRef.current) return;
      setSummary(data);
      setSummaryError('');
      setLastUpdated(new Date());
    } catch (error) {
      if (!mountedRef.current) return;
      const status = error?.response?.status;
      if (status === 401) {
        setAuthExpired(true);
        setConnectionState('offline');
        setSummaryError('Phiên đăng nhập đã hết hạn.');
      } else {
        setSummaryError('Không thể tải số liệu giám sát.');
      }
    } finally {
      if (mountedRef.current) setSummaryLoading(false);
    }
  }, [windowSeconds]);

  const fetchRequests = useCallback(async () => {
    const sequence = requestsSeqRef.current + 1;
    requestsSeqRef.current = sequence;
    setRequestsLoading(true);
    setRequestsError('');
    try {
      // The backend status filter is an exact HTTP code, while the UI filters by class
      // (2xx/4xx/5xx). Fetch a wider page for class filters, then narrow it client-side.
      const params = { limit: statusFilter === 'all' ? RECENT_LIMIT : 200 };
      const route = routeFilter.trim();
      if (route) params.route = route;
      const data = await monitoringApi.getRequests(params);
      if (!mountedRef.current || sequence !== requestsSeqRef.current) return;
      let list = Array.isArray(data?.requests) ? data.requests : [];
      if (statusFilter !== 'all') {
        const prefix = statusFilter.charAt(0);
        list = list.filter((item) => String(item?.status_code ?? '').startsWith(prefix));
      }
      setRequests(list.slice(0, RECENT_LIMIT));
    } catch (error) {
      if (!mountedRef.current || sequence !== requestsSeqRef.current) return;
      const status = error?.response?.status;
      if (status === 401) {
        setAuthExpired(true);
        setConnectionState('offline');
        setRequestsError('Phiên đăng nhập đã hết hạn.');
      } else {
        setRequestsError('Không thể tải danh sách request.');
      }
      setRequests([]);
    } finally {
      if (mountedRef.current && sequence === requestsSeqRef.current) setRequestsLoading(false);
    }
  }, [routeFilter, statusFilter]);

  const handleRefresh = useCallback(() => {
    fetchSummary();
    fetchRequests();
  }, [fetchSummary, fetchRequests]);

  useEffect(() => {
    fetchSummary();
  }, [fetchSummary]);

  useEffect(() => {
    fetchRequests();
  }, [fetchRequests]);

  // Debounce the route input so typing does not fire one request per keystroke.
  useEffect(() => {
    const timer = setTimeout(() => setRouteFilter(routeInput.trim()), 400);
    return () => clearTimeout(timer);
  }, [routeInput]);

  // Authenticated SSE stream. EventSource cannot set Authorization, so we read the
  // response body with fetch() + ReadableStream and keep a buffer for split events.
  useEffect(() => {
    if (authExpired) {
      setConnectionState('offline');
      return undefined;
    }

    let cancelled = false;
    let controller = null;
    let reconnectTimer = null;
    let reader = null;
    let failures = 0;

    const scheduleReconnect = () => {
      const delay = RECONNECT_DELAYS[Math.min(failures - 1, RECONNECT_DELAYS.length - 1)];
      reconnectTimer = setTimeout(connect, delay);
    };

    const connect = async () => {
      if (cancelled) return;

      const token = localStorage.getItem('access_token');
      if (!token) {
        setConnectionState('offline');
        setAuthExpired(true);
        return;
      }

      controller = new AbortController();
      try {
        setConnectionState(failures === 0 ? 'connecting' : failures >= 3 ? 'offline' : 'reconnecting');
        const url = `${API_BASE}${STREAM_PATH}?window_seconds=${encodeURIComponent(windowSeconds)}`;
        const response = await fetch(url, {
          method: 'GET',
          headers: {
            Authorization: `Bearer ${token}`,
            Accept: 'text/event-stream',
          },
          cache: 'no-store',
          signal: controller.signal,
        });

        if (response.status === 401 || response.status === 403) {
          if (!cancelled) {
            // Stop the stream and surface Offline. A genuinely expired session is
            // detected by the REST calls, which own the auth-expired banner.
            setConnectionState('offline');
            setStreamError(
              response.status === 401
                ? 'Không thể xác thực luồng realtime (401).'
                : 'Tài khoản không có quyền truy cập dữ liệu giám sát (403).'
            );
          }
          return;
        }

        if (!response.ok || !response.body) {
          throw new Error(`SSE HTTP ${response.status}`);
        }

        if (cancelled) return;
        failures = 0;
        setConnectionState('live');
        setPollingFallback(false);
        setStreamError('');

        reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let buffer = '';

        while (!cancelled) {
          const { value, done } = await reader.read();
          if (done) break;

          buffer = (buffer + decoder.decode(value, { stream: true })).replace(/\r\n?/g, '\n');

          let separatorIndex = buffer.indexOf('\n\n');
          while (separatorIndex !== -1) {
            const rawEvent = buffer.slice(0, separatorIndex);
            buffer = buffer.slice(separatorIndex + 2);

            const dataLines = rawEvent
              .split('\n')
              .filter((line) => line.startsWith('data:'))
              .map((line) => line.slice(5).replace(/^ /, ''));

            if (dataLines.length > 0) {
              const payload = dataLines.join('\n').trim();
              if (payload && payload !== '[DONE]') {
                try {
                  const data = JSON.parse(payload);
                  if (!cancelled) {
                    const payloadWindow = Number(data?.window_seconds) || null;
                    setStreamWindow(payloadWindow);
                    if (payloadWindow === null || payloadWindow === windowSeconds) {
                      setSummary(data);
                      setSummaryError('');
                      setSummaryLoading(false);
                      setLastUpdated(new Date());
                    }
                  }
                } catch (parseError) {
                  // Ignore malformed events and keep the stream alive.
                }
              }
            }

            separatorIndex = buffer.indexOf('\n\n');
          }
        }

        if (!cancelled) throw new Error('SSE stream closed');
      } catch (error) {
        if (cancelled || error?.name === 'AbortError') return;

        failures += 1;
        if (failures >= 3) {
          setConnectionState('offline');
          setPollingFallback(true);
          setStreamError('Kết nối realtime bị gián đoạn — đang tự động làm mới mỗi 5 giây.');
        } else {
          setConnectionState('reconnecting');
        }
        scheduleReconnect();
      } finally {
        try {
          if (reader) reader.releaseLock();
        } catch (releaseError) {
          // Reader may already be released after an abort.
        }
        reader = null;
      }
    };

    connect();

    return () => {
      cancelled = true;
      clearTimeout(reconnectTimer);
      try {
        controller?.abort();
      } catch (abortError) {
        // Ignore abort races.
      }
    };
  }, [windowSeconds, authExpired]);

  // Polling fallback: used after 3 stream failures and for custom windows when the
  // stream still reports its default 300s window. Never runs while a matching stream
  // is delivering data.
  useEffect(() => {
    if (authExpired) return undefined;
    const needsWindowPolling = windowSeconds !== 300 && streamWindow !== windowSeconds;
    if (!pollingFallback && !needsWindowPolling) return undefined;

    let cancelled = false;
    const tick = async () => {
      if (cancelled) return;
      try {
        const data = await monitoringApi.getSummary(windowSeconds);
        if (cancelled || !mountedRef.current) return;
        setSummary(data);
        setSummaryError('');
        setSummaryLoading(false);
        setLastUpdated(new Date());
      } catch (error) {
        if (cancelled || !mountedRef.current) return;
        if (error?.response?.status === 401) {
          setAuthExpired(true);
          setConnectionState('offline');
        }
      }
    };

    const timer = setInterval(tick, POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [authExpired, pollingFallback, windowSeconds, streamWindow]);

  useEffect(() => {
    setHoveredIndex(null);
  }, [windowSeconds]);

  // Measure the chart container so the SVG stays readable at every breakpoint.
  useEffect(() => {
    const element = chartRef.current;
    if (!element) return undefined;

    const updateWidth = () => {
      const next = Math.max(300, Math.floor(element.clientWidth || 0));
      setChartWidth((previous) => (Math.abs(previous - next) > 1 ? next : previous));
    };

    updateWidth();
    if (typeof ResizeObserver === 'undefined') {
      window.addEventListener('resize', updateWidth);
      return () => window.removeEventListener('resize', updateWidth);
    }
    const observer = new ResizeObserver(updateWidth);
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  const totals = summary?.totals || {};
  const latency = summary?.latency_ms || {};
  const statusCounts = summary?.status_counts || {};
  const alerts = Array.isArray(summary?.alerts) ? summary.alerts : EMPTY_ARRAY;
  const topRoutes = Array.isArray(summary?.top_routes) ? summary.top_routes : EMPTY_ARRAY;
  const slowest = Array.isArray(summary?.slowest) ? summary.slowest : EMPTY_ARRAY;
  const series = Array.isArray(summary?.series) ? summary.series : EMPTY_ARRAY;

  const hasSummary = Boolean(summary);
  const totalRequests = Number(totals.requests) || 0;
  const totalErrors = Number(totals.errors) || 0;
  const errorRate = Number(summary?.error_rate ?? totals.error_rate) || 0;
  const rpm = Number(summary?.req_per_minute ?? totals.requests_per_minute) || 0;
  const rps = Number(summary?.rps ?? totals.requests_per_sec) || 0;
  const activeUsers = Number(summary?.active_users) || 0;
  const p50 = Number(latency.p50) || 0;
  const p95 = Number(latency.p95) || 0;
  const p99 = Number(latency.p99) || 0;
  const maxLatency = Number(latency.max) || 0;

  const hasCriticalAlert = alerts.some((alert) => alert?.severity === 'critical');
  const statusTotal = STATUS_ROWS.reduce(
    (sum, row) => sum + (Number(statusCounts[row.key]) || 0),
    0
  );
  const hasChartData =
    series.length > 0 &&
    (totalRequests > 0 ||
      series.some(
        (item) => (Number(item?.requests) || 0) > 0 || (Number(item?.p95_ms) || 0) > 0
      ));

  const chart = useMemo(() => {
    const width = Math.max(300, chartWidth || 760);
    const height = width < 520 ? 240 : 280;
    const margin = {
      top: 24,
      right: width < 520 ? 42 : 54,
      bottom: 34,
      left: width < 520 ? 40 : 52,
    };
    const innerW = Math.max(10, width - margin.left - margin.right);
    const innerH = Math.max(10, height - margin.top - margin.bottom);
    const bottom = margin.top + innerH;

    const points = series.map((item, index) => {
      const requestsValue = Math.max(0, Number(item?.requests) || 0);
      const errorsValue = Math.max(0, Number(item?.errors) || 0);
      const p95Value = Math.max(0, Number(item?.p95_ms) || 0);
      const x =
        series.length <= 1
          ? margin.left + innerW / 2
          : margin.left + (index / (series.length - 1)) * innerW;
      return {
        ...item,
        requests: requestsValue,
        errors: errorsValue,
        p95: p95Value,
        x,
      };
    });

    const maxRequests = Math.max(1, ...points.map((point) => Math.max(point.requests, point.errors))) * 1.12;
    const maxLatencyValue = Math.max(1, ...points.map((point) => point.p95)) * 1.12;

    const yRequests = (value) =>
      bottom - (Math.max(0, Number(value) || 0) / maxRequests) * innerH;
    const yLatency = (value) =>
      bottom - (Math.max(0, Number(value) || 0) / maxLatencyValue) * innerH;

    const withY = points.map((point) => ({
      ...point,
      yRequests: yRequests(point.requests),
      yErrors: yRequests(point.errors),
      yP95: yLatency(point.p95),
    }));

    const buildLine = (key) =>
      withY
        .map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x.toFixed(2)} ${point[key].toFixed(2)}`)
        .join(' ');

    const requestsPath = buildLine('yRequests');
    const errorsPath = buildLine('yErrors');
    const p95Path = buildLine('yP95');
    const areaPath =
      withY.length > 1
        ? `M ${withY[0].x.toFixed(2)} ${bottom.toFixed(2)} L ${withY
            .map((point) => `${point.x.toFixed(2)} ${point.yRequests.toFixed(2)}`)
            .join(' L ')} L ${withY[withY.length - 1].x.toFixed(2)} ${bottom.toFixed(2)} Z`
        : '';

    const bucketSeconds = Number(series[0]?.bucket_seconds) || 0;
    const showSeconds = bucketSeconds > 0 && bucketSeconds < 60;
    const labelCount = width < 480 ? 3 : width < 720 ? 4 : 6;
    const tickIndexes = new Set();
    if (withY.length > 0) {
      for (let index = 0; index < labelCount; index += 1) {
        tickIndexes.add(
          Math.round((index * (withY.length - 1)) / Math.max(1, labelCount - 1))
        );
      }
    }
    const xTicks = [...tickIndexes]
      .sort((a, b) => a - b)
      .map((index) => ({
        x: withY[index].x,
        label: formatChartTime(withY[index].timestamp, showSeconds),
      }));

    const yTicks = [0, 0.25, 0.5, 0.75, 1].map((ratio) => ({
      y: bottom - ratio * innerH,
      requests: maxRequests * ratio,
      latency: maxLatencyValue * ratio,
    }));

    return {
      width,
      height,
      margin,
      innerW,
      innerH,
      bottom,
      points: withY,
      requestsPath,
      errorsPath,
      p95Path,
      areaPath,
      xTicks,
      yTicks,
    };
  }, [series, chartWidth]);

  const hoveredPoint = hoveredIndex != null ? chart.points[hoveredIndex] : null;
  const tooltipLeftPercent = hoveredPoint
    ? Math.max(
        (90 / chart.width) * 100,
        Math.min(100 - (90 / chart.width) * 100, (hoveredPoint.x / chart.width) * 100)
      )
    : 50;

  const handleChartMouseMove = useCallback(
    (event) => {
      if (!chart.points.length) return;
      const svg = event.currentTarget.ownerSVGElement;
      if (!svg) return;
      const rect = svg.getBoundingClientRect();
      if (!rect.width) return;
      const relativeX = ((event.clientX - rect.left) / rect.width) * chart.width;
      const ratio = (relativeX - chart.margin.left) / chart.innerW;
      const index = Math.round(ratio * (chart.points.length - 1));
      setHoveredIndex(Math.max(0, Math.min(chart.points.length - 1, index)));
    },
    [chart]
  );

  const handleChartMouseLeave = useCallback(() => setHoveredIndex(null), []);

  const connectionMeta = useMemo(() => {
    if (connectionState === 'live') {
      return { label: 'Live', className: 'is-live' };
    }
    if (connectionState === 'reconnecting') {
      return { label: 'Reconnecting', className: 'is-reconnecting' };
    }
    if (connectionState === 'offline') {
      return { label: 'Offline', className: 'is-offline' };
    }
    return { label: 'Đang kết nối', className: 'is-connecting' };
  }, [connectionState]);

  const streamNote = pollingFallback
    ? 'Mất kết nối realtime — dashboard đang tự động làm mới mỗi 5 giây.'
    : windowSeconds !== 300 && streamWindow !== windowSeconds
      ? 'Cửa sổ thời gian tùy chỉnh được làm mới mỗi 5 giây; luồng realtime mặc định dùng cửa sổ 5 phút.'
      : streamError;

  const initialLoading = summaryLoading && !hasSummary;
  const kpiLoading = initialLoading;
  const refreshing = summaryLoading || requestsLoading;

  return (
    <div className="admin-monitoring-page">
      <header className="mon-page-header">
        <div className="mon-header-main">
          <div className="mon-title-block">
            <div className="mon-title-icon">
              <Activity size={22} strokeWidth={2.2} />
            </div>
            <div>
              <h1 className="mon-page-title">Giám sát hệ thống</h1>
              <p className="mon-page-subtitle">
                Theo dõi lưu lượng API, độ trễ và lỗi hệ thống theo thời gian thực.
              </p>
            </div>
          </div>

          <div className="mon-header-actions">
            <div className="mon-window-selector" role="group" aria-label="Khoảng thời gian giám sát">
              {WINDOW_OPTIONS.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  className={`mon-window-btn ${windowSeconds === option.value ? 'active' : ''}`}
                  onClick={() => setWindowSeconds(option.value)}
                  aria-pressed={windowSeconds === option.value}
                >
                  {option.label}
                </button>
              ))}
            </div>

            <div
              className={`mon-connection-pill ${connectionMeta.className}`}
              role="status"
              aria-live="polite"
              title={streamError || 'Trạng thái kết nối realtime'}
            >
              <span className="mon-connection-dot" />
              <span>{connectionMeta.label}</span>
            </div>

            <button
              type="button"
              className="mon-refresh-btn"
              onClick={handleRefresh}
              disabled={refreshing}
            >
              <RefreshCw size={15} className={refreshing ? 'mon-spin' : ''} />
              <span>Làm mới</span>
            </button>
          </div>
        </div>

        <div className="mon-header-meta">
          <span>
            Cập nhật: <strong>{lastUpdated ? lastUpdated.toLocaleTimeString('vi-VN') : '—'}</strong>
          </span>
          <span className="mon-meta-sep">•</span>
          <span>
            Cửa sổ: <strong>{windowLabel}</strong>
          </span>
          {hasSummary && summary?.buffer_size != null && (
            <>
              <span className="mon-meta-sep">•</span>
              <span>Buffer: {formatNumber(summary.buffer_size)}</span>
            </>
          )}
          {hasSummary && summary?.persist_enabled != null && (
            <>
              <span className="mon-meta-sep">•</span>
              <span>Lưu DB: {summary.persist_enabled ? 'Bật' : 'Tắt'}</span>
            </>
          )}
        </div>
      </header>

      {authExpired && (
        <div className="mon-banner is-error" role="alert">
          <div className="mon-banner-icon">
            <ShieldAlert size={20} />
          </div>
          <div className="mon-banner-body">
            <p className="mon-banner-title">Phiên đăng nhập đã hết hạn</p>
            <p className="mon-banner-text">
              Vui lòng đăng nhập lại để tiếp tục nhận dữ liệu giám sát realtime.
            </p>
          </div>
          <button type="button" className="mon-banner-btn" onClick={() => navigate('/login')}>
            Đăng nhập lại
          </button>
        </div>
      )}

      {summaryError && !authExpired && (
        <div className="mon-banner is-warning" role="alert">
          <div className="mon-banner-icon">
            <AlertTriangle size={20} />
          </div>
          <div className="mon-banner-body">
            <p className="mon-banner-title">Không thể tải số liệu giám sát</p>
            <p className="mon-banner-text">{summaryError}</p>
          </div>
          <button type="button" className="mon-banner-btn" onClick={fetchSummary}>
            Thử lại
          </button>
        </div>
      )}

      {streamNote && !authExpired && (
        <div className="mon-stream-note" role="status">
          <AlertTriangle size={15} />
          <span>{streamNote}</span>
        </div>
      )}

      {alerts.length > 0 && (
        <div
          className={`mon-alerts-banner ${hasCriticalAlert ? 'is-critical' : 'is-warning'}`}
          role="alert"
        >
          <div className="mon-alerts-icon">
            <ShieldAlert size={20} />
          </div>
          <div className="mon-alerts-body">
            <div className="mon-alerts-title">
              {hasCriticalAlert ? 'Cảnh báo nghiêm trọng' : 'Cảnh báo hệ thống'}
              <span>{alerts.length}</span>
            </div>
            <ul className="mon-alerts-list">
              {alerts.map((alert, index) => (
                <li key={`${alert?.type || 'alert'}-${index}`}>
                  <span
                    className={`mon-alert-tag ${
                      alert?.severity === 'critical' ? 'is-critical' : 'is-warning'
                    }`}
                  >
                    {alert?.severity === 'critical' ? 'Critical' : 'Warning'}
                  </span>
                  <span title={alert?.message || ''}>{alertText(alert)}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      <section className="mon-kpi-grid" aria-label="Chỉ số chính">
        <KpiCard
          icon={Activity}
          label="Tổng request"
          value={hasSummary ? formatNumber(totalRequests) : '—'}
          hint={hasSummary ? `${windowLabel} gần nhất` : 'Đang chờ dữ liệu'}
          loading={kpiLoading}
        />
        <KpiCard
          icon={Gauge}
          label="Request/phút"
          value={hasSummary ? formatNumber(rpm, rpm < 10 ? 1 : 0) : '—'}
          hint={hasSummary ? `${formatNumber(rps, 2)} req/s` : 'Đang chờ dữ liệu'}
          loading={kpiLoading}
        />
        <KpiCard
          icon={AlertTriangle}
          label="Error rate"
          value={hasSummary ? formatPercent(errorRate) : '—'}
          hint={hasSummary ? `${formatNumber(totalErrors)} lỗi` : 'Đang chờ dữ liệu'}
          tone={errorRate > 0.05 ? 'warning' : 'default'}
          loading={kpiLoading}
        />
        <KpiCard
          icon={Users}
          label="Active users"
          value={hasSummary ? formatNumber(activeUsers) : '—'}
          hint={hasSummary ? 'Người dùng duy nhất' : 'Đang chờ dữ liệu'}
          loading={kpiLoading}
        />
        <KpiCard
          icon={Timer}
          label="P95 latency"
          value={hasSummary ? formatMs(p95) : '—'}
          hint={hasSummary ? `p50: ${formatMs(p50)}` : 'Đang chờ dữ liệu'}
          tone={p95 > 1000 ? 'warning' : 'default'}
          loading={kpiLoading}
        />
        <KpiCard
          icon={Clock}
          label="P99 latency"
          value={hasSummary ? formatMs(p99) : '—'}
          hint={hasSummary ? `max: ${formatMs(maxLatency)}` : 'Đang chờ dữ liệu'}
          loading={kpiLoading}
        />
      </section>

      <Panel
        title="Lưu lượng & độ trễ"
        subtitle={`Requests, lỗi và P95 theo từng bucket trong ${windowLabel.toLowerCase()} gần nhất`}
        className="mon-chart-panel"
        actions={
          <div className="mon-chart-legend">
            <span>
              <i className="mon-legend-dot is-requests" />
              Requests
            </span>
            <span>
              <i className="mon-legend-dot is-errors" />
              Lỗi
            </span>
            <span>
              <i className="mon-legend-dot is-p95" />
              P95
            </span>
          </div>
        }
      >
        <div className="mon-chart-body" ref={chartRef}>
          {initialLoading ? (
            <LoadingState label="Đang tải số liệu biểu đồ…" />
          ) : !hasChartData ? (
            <EmptyState
              icon={BarChart3}
              title="Chưa có dữ liệu biểu đồ"
              description="Chưa ghi nhận request nào trong cửa sổ thời gian này."
            />
          ) : (
            <>
              <svg
                viewBox={`0 0 ${chart.width} ${chart.height}`}
                className="mon-chart-svg"
                role="img"
                aria-label="Biểu đồ lưu lượng request, lỗi và độ trễ P95"
              >
                <defs>
                  <linearGradient id="monRequestsGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#4D308D" stopOpacity="0.18" />
                    <stop offset="100%" stopColor="#4D308D" stopOpacity="0" />
                  </linearGradient>
                </defs>

                {chart.yTicks.map((tick, index) => (
                  <g key={`mon-grid-${index}`}>
                    <line
                      x1={chart.margin.left}
                      y1={tick.y}
                      x2={chart.width - chart.margin.right}
                      y2={tick.y}
                      className={index === 0 ? 'mon-chart-baseline' : 'mon-chart-grid-line'}
                    />
                    <text
                      x={chart.margin.left - 8}
                      y={tick.y + 3}
                      textAnchor="end"
                      className="mon-chart-axis-label"
                    >
                      {formatCompact(tick.requests)}
                    </text>
                    <text
                      x={chart.width - chart.margin.right + 8}
                      y={tick.y + 3}
                      textAnchor="start"
                      className="mon-chart-axis-label"
                    >
                      {formatCompact(tick.latency)}
                    </text>
                  </g>
                ))}

                <text x={chart.margin.left} y={12} className="mon-chart-axis-title">
                  requests
                </text>
                <text
                  x={chart.width - chart.margin.right}
                  y={12}
                  textAnchor="end"
                  className="mon-chart-axis-title"
                >
                  ms
                </text>

                {chart.areaPath && <path d={chart.areaPath} fill="url(#monRequestsGradient)" />}
                <path
                  d={chart.requestsPath}
                  fill="none"
                  stroke="#4D308D"
                  strokeWidth="2.2"
                  strokeLinejoin="round"
                  strokeLinecap="round"
                />
                <path
                  d={chart.errorsPath}
                  fill="none"
                  stroke="#EF4444"
                  strokeWidth="1.8"
                  strokeLinejoin="round"
                  strokeLinecap="round"
                />
                <path
                  d={chart.p95Path}
                  fill="none"
                  stroke="#F59E0B"
                  strokeWidth="2"
                  strokeDasharray="5 4"
                  strokeLinejoin="round"
                  strokeLinecap="round"
                />

                {chart.xTicks.map((tick, index) => (
                  <text
                    key={`mon-xtick-${index}`}
                    x={tick.x}
                    y={chart.height - 10}
                    textAnchor="middle"
                    className="mon-chart-axis-label"
                  >
                    {tick.label}
                  </text>
                ))}

                {hoveredPoint && (
                  <line
                    x1={hoveredPoint.x}
                    y1={chart.margin.top}
                    x2={hoveredPoint.x}
                    y2={chart.bottom}
                    stroke="#C4B5FD"
                    strokeWidth="1"
                    strokeDasharray="4 4"
                  />
                )}

                {hoveredPoint && (
                  <>
                    <circle
                      cx={hoveredPoint.x}
                      cy={hoveredPoint.yRequests}
                      r="4.5"
                      fill="#4D308D"
                      stroke="#FFFFFF"
                      strokeWidth="2"
                    />
                    <circle
                      cx={hoveredPoint.x}
                      cy={hoveredPoint.yErrors}
                      r="4"
                      fill="#EF4444"
                      stroke="#FFFFFF"
                      strokeWidth="2"
                    />
                    <circle
                      cx={hoveredPoint.x}
                      cy={hoveredPoint.yP95}
                      r="4"
                      fill="#F59E0B"
                      stroke="#FFFFFF"
                      strokeWidth="2"
                    />
                  </>
                )}

                <rect
                  x={chart.margin.left}
                  y={chart.margin.top}
                  width={chart.innerW}
                  height={chart.innerH}
                  fill="transparent"
                  style={{ cursor: 'crosshair' }}
                  onMouseMove={handleChartMouseMove}
                  onMouseLeave={handleChartMouseLeave}
                />
              </svg>

              {hoveredPoint && (
                <div
                  className="mon-chart-tooltip"
                  style={{ left: `${tooltipLeftPercent}%` }}
                >
                  <div className="mon-tooltip-time">{formatTime(hoveredPoint.timestamp)}</div>
                  <div className="mon-tooltip-row">
                    <span className="mon-legend-dot is-requests" />
                    Requests
                    <strong>{formatNumber(hoveredPoint.requests)}</strong>
                  </div>
                  <div className="mon-tooltip-row">
                    <span className="mon-legend-dot is-errors" />
                    Lỗi
                    <strong>{formatNumber(hoveredPoint.errors)}</strong>
                  </div>
                  <div className="mon-tooltip-row">
                    <span className="mon-legend-dot is-p95" />
                    P95
                    <strong>{formatMs(hoveredPoint.p95)}</strong>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </Panel>

      <div className="mon-two-col">
        <Panel
          title="Phân bố trạng thái"
          subtitle="Tỷ lệ mã HTTP trong cửa sổ thời gian đã chọn"
          actions={<span className="mon-panel-count">{formatNumber(statusTotal)} request</span>}
        >
          {initialLoading ? (
            <LoadingState />
          ) : statusTotal === 0 ? (
            <EmptyState
              icon={BarChart3}
              title="Chưa có dữ liệu trạng thái"
              description="Chưa có request nào được ghi nhận trong cửa sổ này."
            />
          ) : (
            <div className="mon-status-list">
              {STATUS_ROWS.map((row) => {
                const count = Number(statusCounts[row.key]) || 0;
                const percent = statusTotal > 0 ? (count / statusTotal) * 100 : 0;
                return (
                  <div className="mon-status-row" key={row.key}>
                    <div className="mon-status-label-wrap">
                      <span className={`mon-status-dot ${row.className}`} />
                      <span className="mon-status-code">{row.key}</span>
                      <span className="mon-status-desc">{row.label}</span>
                    </div>
                    <div className="mon-status-bar">
                      <span
                        className={row.className}
                        style={{ width: `${Math.max(0, Math.min(100, percent))}%` }}
                      />
                    </div>
                    <div className="mon-status-numbers">
                      <strong>{formatNumber(count)}</strong>
                      <span>{formatPercent(count / statusTotal, 1)}</span>
                    </div>
                  </div>
                );
              })}
              {(Number(statusCounts['1xx']) > 0 || Number(statusCounts.other) > 0) && (
                <p className="mon-status-footnote">
                  1xx: {formatNumber(statusCounts['1xx'])} · Khác: {formatNumber(statusCounts.other)}
                </p>
              )}
            </div>
          )}
        </Panel>

        <Panel
          title="Top routes"
          subtitle="Các route có lưu lượng cao nhất trong cửa sổ thời gian"
          actions={<span className="mon-panel-count">{topRoutes.length} route</span>}
        >
          {initialLoading ? (
            <LoadingState />
          ) : topRoutes.length === 0 ? (
            <EmptyState
              icon={Inbox}
              title="Chưa có dữ liệu route"
              description="Chưa có request nào được ghi nhận trong cửa sổ này."
            />
          ) : (
            <div className="mon-table-wrap">
              <table className="mon-table">
                <thead>
                  <tr>
                    <th>Route</th>
                    <th className="is-right">Requests</th>
                    <th className="is-right">Avg</th>
                    <th className="is-right">P95</th>
                    <th className="is-right">Error rate</th>
                  </tr>
                </thead>
                <tbody>
                  {topRoutes.map((route, index) => {
                    const routeP95 = Number(route?.p95_ms) || 0;
                    const routeErrorRate = Number(route?.error_rate) || 0;
                    return (
                      <tr
                        key={`${route?.route || 'route'}-${index}`}
                        className={routeP95 > 1000 ? 'is-slow' : ''}
                      >
                        <td>
                          <span className="mon-route-cell" title={route?.route || ''}>
                            {route?.route || '—'}
                          </span>
                        </td>
                        <td className="is-right">{formatNumber(route?.count)}</td>
                        <td className="is-right">{formatMs(route?.avg_ms)}</td>
                        <td className={`is-right ${routeP95 > 1000 ? 'mon-cell-warn' : ''}`}>
                          {formatMs(routeP95)}
                        </td>
                        <td
                          className={`is-right ${
                            routeErrorRate > 0.05 ? 'mon-cell-warn' : ''
                          }`}
                        >
                          {formatPercent(routeErrorRate)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </Panel>
      </div>

      <Panel
        title="Request chậm nhất"
        subtitle="10 request có thời gian xử lý cao nhất trong cửa sổ thời gian"
        actions={<span className="mon-panel-count">{slowest.length} request</span>}
        className="mon-table-panel"
      >
        {initialLoading ? (
          <LoadingState />
        ) : slowest.length === 0 ? (
          <EmptyState
            icon={Clock}
            title="Chưa có dữ liệu request"
            description="Chưa có request nào được ghi nhận trong cửa sổ này."
          />
        ) : (
          <div className="mon-table-wrap">
            <table className="mon-table">
              <thead>
                <tr>
                  <th>Method</th>
                  <th>Route</th>
                  <th>Status</th>
                  <th className="is-right">Duration</th>
                  <th className="is-right">Thời gian</th>
                </tr>
              </thead>
              <tbody>
                {slowest.map((item, index) => {
                  const duration = Number(item?.duration_ms) || 0;
                  return (
                    <tr key={`${item?.request_id || 'slow'}-${index}`}>
                      <td>
                        <span className={`mon-method method-${String(item?.method || '').toLowerCase()}`}>
                          {item?.method || '—'}
                        </span>
                      </td>
                      <td>
                        <span
                          className="mon-route-cell"
                          title={item?.path || item?.route || ''}
                        >
                          {item?.route || item?.path || '—'}
                        </span>
                      </td>
                      <td>
                        <StatusBadge code={item?.status_code} />
                      </td>
                      <td className={`is-right ${duration > 1000 ? 'mon-cell-warn' : ''}`}>
                        {formatMs(duration)}
                      </td>
                      <td className="is-right">
                        {formatTime(item?.finished_at || item?.started_at)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Panel>

      <Panel
        title="Request gần đây"
        subtitle="50 request mới nhất theo bộ lọc route và trạng thái"
        actions={<span className="mon-panel-count">{requests.length} / {RECENT_LIMIT}</span>}
        className="mon-table-panel"
      >
        <div className="mon-table-toolbar">
          <div className="mon-search-box">
            <Search size={15} />
            <input
              type="text"
              value={routeInput}
              onChange={(event) => setRouteInput(event.target.value)}
              placeholder="Lọc theo route hoặc path..."
              aria-label="Lọc theo route"
            />
            {routeInput && (
              <button
                type="button"
                className="mon-search-clear"
                onClick={() => setRouteInput('')}
                aria-label="Xóa bộ lọc route"
              >
                <X size={13} />
              </button>
            )}
          </div>

          <div className="mon-select-box">
            <Filter size={14} />
            <select
              value={statusFilter}
              onChange={(event) => setStatusFilter(event.target.value)}
              aria-label="Lọc theo trạng thái"
            >
              <option value="all">Tất cả trạng thái</option>
              <option value="2xx">2xx · Thành công</option>
              <option value="4xx">4xx · Lỗi client</option>
              <option value="5xx">5xx · Lỗi server</option>
            </select>
          </div>

          {(routeInput || statusFilter !== 'all') && (
            <button
              type="button"
              className="mon-clear-filters"
              onClick={() => {
                setRouteInput('');
                setStatusFilter('all');
              }}
            >
              <X size={13} />
              Xóa lọc
            </button>
          )}

          <button
            type="button"
            className="mon-icon-btn"
            onClick={fetchRequests}
            disabled={requestsLoading}
            title="Làm mới danh sách request"
            aria-label="Làm mới danh sách request"
          >
            <RefreshCw size={16} className={requestsLoading ? 'mon-spin' : ''} />
          </button>

          <span className="mon-table-count">{requests.length} request</span>
        </div>

        {requestsError && (
          <div className="mon-inline-error">
            <AlertTriangle size={14} />
            <span>{requestsError}</span>
          </div>
        )}

        {requestsLoading ? (
          <div className="mon-table-loading">
            <Loader2 size={18} className="mon-spin" />
            <span>Đang tải danh sách request…</span>
          </div>
        ) : requests.length === 0 ? (
          <EmptyState
            icon={Inbox}
            title="Không có request phù hợp"
            description="Thử thay đổi bộ lọc route hoặc trạng thái, hoặc bấm làm mới."
          />
        ) : (
          <div className="mon-table-wrap">
            <table className="mon-table is-wide">
              <thead>
                <tr>
                  <th>Request ID</th>
                  <th>Method</th>
                  <th>Route</th>
                  <th>Status</th>
                  <th className="is-right">Duration</th>
                  <th>User</th>
                  <th className="is-right">Thời gian</th>
                </tr>
              </thead>
              <tbody>
                {requests.map((item, index) => {
                  const duration = Number(item?.duration_ms) || 0;
                  return (
                    <tr key={`${item?.request_id || 'request'}-${index}`}>
                      <td>
                        <code className="mon-req-id" title={item?.request_id || ''}>
                          {shortId(item?.request_id)}
                        </code>
                      </td>
                      <td>
                        <span className={`mon-method method-${String(item?.method || '').toLowerCase()}`}>
                          {item?.method || '—'}
                        </span>
                      </td>
                      <td>
                        <span
                          className="mon-route-cell is-muted"
                          title={item?.path || item?.route || ''}
                        >
                          {item?.route || item?.path || '—'}
                        </span>
                      </td>
                      <td>
                        <StatusBadge code={item?.status_code} />
                      </td>
                      <td className={`is-right ${duration > 1000 ? 'mon-cell-warn' : ''}`}>
                        {formatMs(duration)}
                      </td>
                      <td>
                        <span className="mon-user-ref" title={item?.user_ref || ''}>
                          {shortUserRef(item?.user_ref)}
                        </span>
                      </td>
                      <td className="is-right">
                        {formatTime(item?.finished_at || item?.created_at || item?.started_at)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Panel>
    </div>
  );
}
