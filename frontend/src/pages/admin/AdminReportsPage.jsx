// File Name: AdminReportsPage.jsx
// Description: Comprehensive Reports & Analytics screen for Admin portal with GPA distributions, dual spline trend charts, Bloom taxonomy donut, and early intervention alerts.
// Created At: 2026-09-19
// Created By: Tam Khang
// Updated At: 2026-11-14
// Updated By: Tam Khang

import React, { useState, useEffect, useCallback } from 'react';
import { 
  BarChart3, 
  Download, 
  Plus, 
  TrendingUp, 
  Star, 
  ClipboardCheck, 
  ChevronDown, 
  ArrowRight, 
  CheckCircle2, 
  Calendar, 
  Cpu,
  X,
  Sparkles
} from 'lucide-react';
import { adminReportsApi } from '../../services/api';
import './AdminReportsPage.css';

const FALLBACK_KPIS = {
  total_exercises: 517,
  ai_exercises: 318,
  regular_exercises: 199,
  total_questions: 4820,
  ai_questions: 2940,
  total_attempts: 3489,
  avg_score: 7.85,
  total_students: 2450,
  total_classes: 64,
  total_subjects: 12,
  ai_adoption_rate: 61.5,
  completion_rate: 88.4,
};

const FALLBACK_GRADE_DISTRIBUTIONS = [
  {
    grade: 'Khối 12',
    grade_code: 'k12',
    studentsCount: 840,
    totalExercises: 210,
    segments: [
      { label: 'Xuất sắc', count: 235, percent: 28.0, color: '#10b981' },
      { label: 'Khá / Giỏi', count: 353, percent: 42.0, color: '#3b82f6' },
      { label: 'Trung bình', count: 185, percent: 22.0, color: '#f59e0b' },
      { label: 'Cần hỗ trợ', count: 67, percent: 8.0, color: '#ef4444' },
    ],
  },
  {
    grade: 'Khối 11',
    grade_code: 'k11',
    studentsCount: 790,
    totalExercises: 162,
    segments: [
      { label: 'Xuất sắc', count: 221, percent: 28.0, color: '#10b981' },
      { label: 'Khá / Giỏi', count: 332, percent: 42.0, color: '#3b82f6' },
      { label: 'Trung bình', count: 174, percent: 22.0, color: '#f59e0b' },
      { label: 'Cần hỗ trợ', count: 63, percent: 8.0, color: '#ef4444' },
    ],
  },
  {
    grade: 'Khối 10',
    grade_code: 'k10',
    studentsCount: 820,
    totalExercises: 145,
    segments: [
      { label: 'Xuất sắc', count: 230, percent: 28.0, color: '#10b981' },
      { label: 'Khá / Giỏi', count: 344, percent: 42.0, color: '#3b82f6' },
      { label: 'Trung bình', count: 180, percent: 22.0, color: '#f59e0b' },
      { label: 'Cần hỗ trợ', count: 66, percent: 8.0, color: '#ef4444' },
    ],
  },
];

const FALLBACK_WEEKLY_DATA = [
  { day: 'Thứ 2', ai: 18, regular: 12, x: 50, yAi: 150, yReg: 170 },
  { day: 'Thứ 3', ai: 26, regular: 16, x: 140, yAi: 125, yReg: 158 },
  { day: 'Thứ 4', ai: 34, regular: 19, x: 230, yAi: 102, yReg: 148 },
  { day: 'Thứ 5', ai: 31, regular: 21, x: 320, yAi: 110, yReg: 142 },
  { day: 'Thứ 6', ai: 44, regular: 24, x: 410, yAi: 74, yReg: 132 },
  { day: 'Thứ 7', ai: 29, regular: 15, x: 500, yAi: 116, yReg: 162 },
  { day: 'Chủ nhật', ai: 14, regular: 9, x: 590, yAi: 164, yReg: 180 },
];

const SEGMENT_LABEL_VI = {
  Excellent: 'Xuất sắc',
  Good: 'Khá / Giỏi',
  Average: 'Trung bình',
  'Needs Support': 'Cần hỗ trợ',
};

const DAY_LABEL_VI = {
  Mon: 'Thứ 2',
  Tue: 'Thứ 3',
  Wed: 'Thứ 4',
  Thu: 'Thứ 5',
  Fri: 'Thứ 6',
  Sat: 'Thứ 7',
  Sun: 'Chủ nhật',
  'Week 1': 'Tuần 1',
  'Week 2': 'Tuần 2',
  'Week 3': 'Tuần 3',
  'Week 4': 'Tuần 4',
};

const FREQUENCY_LABEL_VI = {
  daily: 'Mỗi ngày (18:00)',
  weekly: 'Hàng tuần (Thứ Hai 07:00)',
  monthly: 'Hàng tháng (Ngày 28)',
};

const localizeGradeLabel = (rawGrade, gradeCode) => {
  if (gradeCode === 'k10') return 'Khối 10';
  if (gradeCode === 'k11') return 'Khối 11';
  if (gradeCode === 'k12') return 'Khối 12';
  return String(rawGrade || '').replace(/^Grade\s+/i, 'Khối ');
};

const normalizeTimeSeries = (rawSeries) => {
  if (!Array.isArray(rawSeries) || rawSeries.length === 0) return [];
  const count = rawSeries.length;
  const maxVal = Math.max(
    1,
    ...rawSeries.map((pt) => Math.max(Number(pt.ai || 0), Number(pt.regular || 0)))
  );
  return rawSeries.map((pt, idx) => {
    const ai = Number(pt.ai ?? 0);
    const regular = Number(pt.regular ?? 0);
    const computedX = count === 1 ? 350 : Math.round(60 + (idx * 560) / (count - 1));
    const x = typeof pt.x === 'number' ? pt.x : computedX;
    const yAi = typeof pt.yAi === 'number' ? pt.yAi : Math.round(195 - (ai / maxVal) * 130);
    const yReg = typeof pt.yReg === 'number' ? pt.yReg : Math.round(195 - (regular / maxVal) * 130);
    return {
      day: DAY_LABEL_VI[pt.day] || pt.day,
      ai,
      regular,
      x,
      yAi,
      yReg,
    };
  });
};

const triggerBlobDownload = (blobData, filename, mimeType) => {
  const blob = blobData instanceof Blob ? blobData : new Blob([blobData], { type: mimeType });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
};

export default function AdminReportsPage() {
  // State for filters
  const [timeframe, setTimeframe] = useState('week'); // 'week' | 'month'
  const [academicYear, setAcademicYear] = useState('2024 - 2025');
  const [semester, setSemester] = useState('Học kỳ II');
  const [gradeFilter, setGradeFilter] = useState('all');
  const [deptFilter, setDeptFilter] = useState('all');
  const [hoveredWeeklyPoint, setHoveredWeeklyPoint] = useState(null);

  // Analytics & schedule state
  const [kpis, setKpis] = useState(FALLBACK_KPIS);
  const [gradeExerciseDistributions, setGradeExerciseDistributions] = useState(FALLBACK_GRADE_DISTRIBUTIONS);
  const [weeklyData, setWeeklyData] = useState(FALLBACK_WEEKLY_DATA);
  const [schedules, setSchedules] = useState([]);
  const [isLoadingAnalytics, setIsLoadingAnalytics] = useState(false);
  const [lastUpdatedText, setLastUpdatedText] = useState('Vừa cập nhật');

  // Modals state
  const [isExportModalOpen, setIsExportModalOpen] = useState(false);
  const [isCustomReportModalOpen, setIsCustomReportModalOpen] = useState(false);
  const [isScheduleModalOpen, setIsScheduleModalOpen] = useState(false);
  const [toastMessage, setToastMessage] = useState(null);

  // Export & creation action states
  const [exportFormat, setExportFormat] = useState('pdf');
  const [isExporting, setIsExporting] = useState(false);
  const [isCreatingCustom, setIsCreatingCustom] = useState(false);
  const [isCreatingSchedule, setIsCreatingSchedule] = useState(false);

  // Custom report form state
  const [customReport, setCustomReport] = useState({
    title: '',
    metricType: 'academic',
    format: 'pdf',
    frequency: 'weekly',
  });

  // Schedule report form state
  const [scheduleForm, setScheduleForm] = useState({
    title: '',
    frequency: 'weekly',
    format: 'csv',
    recipientsText: '',
  });

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => {
      setToastMessage(null);
    }, 3500);
  };

  const fetchAnalytics = useCallback(async () => {
    setIsLoadingAnalytics(true);
    try {
      const res = await adminReportsApi.getAnalytics({
        academic_year: academicYear,
        semester,
        grade: gradeFilter,
        department: deptFilter,
        timeframe,
      });

      if (res?.kpis) {
        setKpis((prev) => ({ ...prev, ...res.kpis }));
      }
      if (Array.isArray(res?.grade_distributions)) {
        setGradeExerciseDistributions(
          res.grade_distributions.map((item) => ({
            ...item,
            grade: localizeGradeLabel(item.grade, item.grade_code),
            segments: Array.isArray(item.segments)
              ? item.segments.map((seg) => ({
                  ...seg,
                  label: SEGMENT_LABEL_VI[seg.label] || seg.label,
                }))
              : [],
          }))
        );
      }
      if (Array.isArray(res?.time_series)) {
        setWeeklyData(normalizeTimeSeries(res.time_series));
      }
      setLastUpdatedText(new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }));
    } catch (err) {
      console.error('Failed to fetch analytics report:', err);
      showToast('Không thể tải dữ liệu phân tích mới nhất từ máy chủ.');
    } finally {
      setIsLoadingAnalytics(false);
    }
  }, [academicYear, semester, gradeFilter, deptFilter, timeframe]);

  const fetchSchedules = useCallback(async () => {
    try {
      const res = await adminReportsApi.getSchedules();
      if (Array.isArray(res?.items)) {
        setSchedules(res.items);
      }
    } catch (err) {
      console.error('Failed to fetch report schedules:', err);
    }
  }, []);

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  useEffect(() => {
    fetchSchedules();
  }, [fetchSchedules]);

  const handleExportReport = async () => {
    if (isExporting) return;
    setIsExporting(true);
    try {
      const blob = await adminReportsApi.exportReport({
        format: exportFormat,
        academic_year: academicYear,
        semester,
        grade: gradeFilter,
        department: deptFilter,
      });
      const safeYear = academicYear.replace(/[^a-zA-Z0-9_-]/g, '') || 'report';
      const ext = exportFormat === 'pdf' ? 'html' : exportFormat;
      const mimeMap = {
        html: 'text/html;charset=utf-8;',
        csv: 'text/csv;charset=utf-8;',
        json: 'application/json;charset=utf-8;',
      };
      triggerBlobDownload(blob, `admin_report_${safeYear}.${ext}`, mimeMap[ext] || 'application/octet-stream');
      setIsExportModalOpen(false);
      showToast('Đã tạo và tải xuống tài liệu báo cáo thành công!');
    } catch (err) {
      console.error('Failed to export report:', err);
      const errMsg = err.response?.data?.detail?.message || err.message || 'Lỗi khi xuất báo cáo.';
      showToast(`Lỗi: ${errMsg}`);
    } finally {
      setIsExporting(false);
    }
  };

  const handleCreateCustomReport = async (e) => {
    e.preventDefault();
    if (!customReport.title.trim() || isCreatingCustom) return;
    setIsCreatingCustom(true);
    try {
      const res = await adminReportsApi.createCustomReport({
        title: customReport.title.trim(),
        metricType: customReport.metricType,
        format: customReport.format,
        frequency: customReport.frequency,
        academic_year: academicYear,
        semester,
        grade: gradeFilter,
        department: deptFilter,
      });
      const createdTitle = res?.title || res?.item?.title || customReport.title.trim();
      setIsCustomReportModalOpen(false);
      setCustomReport({ title: '', metricType: 'academic', format: 'pdf', frequency: 'weekly' });
      showToast(`Đã tạo mẫu báo cáo tùy chỉnh "${createdTitle}"!`);
    } catch (err) {
      console.error('Failed to create custom report:', err);
      const errMsg = err.response?.data?.detail?.message || err.message || 'Không thể tạo báo cáo tùy chỉnh.';
      showToast(`Lỗi: ${errMsg}`);
    } finally {
      setIsCreatingCustom(false);
    }
  };

  const handleCreateSchedule = async (e) => {
    e.preventDefault();
    if (!scheduleForm.title.trim() || isCreatingSchedule) return;
    const recipients = scheduleForm.recipientsText
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean);
    if (recipients.length === 0) {
      showToast('Vui lòng nhập ít nhất một email người nhận hợp lệ.');
      return;
    }

    setIsCreatingSchedule(true);
    try {
      const res = await adminReportsApi.createSchedule({
        title: scheduleForm.title.trim(),
        frequency: scheduleForm.frequency,
        format: scheduleForm.format,
        recipients,
        grade: gradeFilter,
        department: deptFilter,
      });
      const createdItem = res?.item || res;
      if (createdItem) {
        setSchedules((prev) => [createdItem, ...prev]);
      }
      setIsScheduleModalOpen(false);
      setScheduleForm({ title: '', frequency: 'weekly', format: 'csv', recipientsText: '' });
      showToast('Đã thiết lập lịch gửi email báo cáo tự động thành công!');
    } catch (err) {
      console.error('Failed to create report schedule:', err);
      const errMsg = err.response?.data?.detail?.message || err.message || 'Không thể lưu lịch gửi báo cáo.';
      showToast(`Lỗi: ${errMsg}`);
    } finally {
      setIsCreatingSchedule(false);
    }
  };

  const generateSvgPath = (points, yKey) => {
    if (!points || points.length === 0) return '';
    let d = `M ${points[0].x} ${points[0][yKey]}`;
    for (let i = 0; i < points.length - 1; i++) {
      const p0 = points[i];
      const p1 = points[i + 1];
      const cp1x = p0.x + (p1.x - p0.x) / 2;
      const cp1y = p0[yKey];
      const cp2x = p0.x + (p1.x - p0.x) / 2;
      const cp2y = p1[yKey];
      d += ` C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${p1.x} ${p1[yKey]}`;
    }
    return d;
  };

  const linePathAi = generateSvgPath(weeklyData, 'yAi');
  const linePathReg = generateSvgPath(weeklyData, 'yReg');
  const areaPathAi = weeklyData.length > 0
    ? `${linePathAi} L ${weeklyData[weeklyData.length - 1].x} 230 L ${weeklyData[0].x} 230 Z`
    : '';
  const areaPathReg = weeklyData.length > 0
    ? `${linePathReg} L ${weeklyData[weeklyData.length - 1].x} 230 L ${weeklyData[0].x} 230 Z`
    : '';
  const legendSegments = gradeExerciseDistributions[0]?.segments || [];

  return (
    <div className="admin-reports-page-container">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="admin-toast">
          <CheckCircle2 size={18} />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* 1. Header Section */}
      <section className="reports-page-header">
        <div className="reports-header-title-block">
          <div className="reports-analytics-tag">
            <span className="status-dot purple"></span>
            <span>TRUNG TÂM PHÂN TÍCH DỮ LIỆU TOÀN TRƯỜNG</span>
            <span className="dot">•</span>
            <span className="tag-accent">NĂM HỌC {academicYear}</span>
          </div>

          <div className="reports-title-with-actions-row">
            <div className="reports-header-title-row">
              <h1 className="reports-page-title">Báo cáo & Thống kê</h1>
              <BarChart3 size={24} className="reports-title-icon" />
            </div>

            <div className="reports-header-actions">
              <button 
                type="button" 
                className="btn-reports-export"
                onClick={() => setIsScheduleModalOpen(true)}
              >
                <Calendar size={16} strokeWidth={2} />
                <span>Lên lịch gửi</span>
              </button>

              <button 
                type="button" 
                className="btn-reports-export"
                onClick={() => setIsExportModalOpen(true)}
              >
                <Download size={16} strokeWidth={2} />
                <span>Xuất dữ liệu PDF/Excel</span>
              </button>

              <button 
                type="button" 
                className="btn-reports-custom"
                onClick={() => setIsCustomReportModalOpen(true)}
              >
                <Plus size={17} strokeWidth={2.4} />
                <span>+ Tạo báo cáo tùy chỉnh</span>
              </button>
            </div>
          </div>

          <p className="reports-page-subtitle">
            Tổng hợp các chỉ số hiệu suất học tập, mức độ tham gia trực tuyến, tỷ lệ hoàn thành bài tập và tình trạng vận hành hệ thống LMS.
          </p>
        </div>
      </section>

      {/* 2. Top KPI Summary Cards */}
      <section className="reports-stats-grid">
        <div className="reports-stat-card">
          <div className="reports-stat-top">
            <span className="reports-stat-label">TỔNG SỐ BÀI TẬP</span>
            <div className="reports-stat-icon-box purple">
              <ClipboardCheck size={18} />
            </div>
          </div>
          <div className="reports-stat-value">
            {Number(kpis.total_exercises || 0).toLocaleString('vi-VN')} <span className="stat-unit">bài</span>
          </div>
          <div className="reports-stat-footer">
            <span className="reports-trend-badge green">
              <TrendingUp size={13} /> {Number(kpis.total_questions || 0).toLocaleString('vi-VN')} câu hỏi
            </span>
            <span>• {kpis.total_classes || 0} lớp học</span>
          </div>
          <div className="reports-stat-progress-bar purple"></div>
        </div>

        <div className="reports-stat-card">
          <div className="reports-stat-top">
            <span className="reports-stat-label">TỶ LỆ ỨNG DỤNG AI</span>
            <div className="reports-stat-icon-box lavender">
              <Cpu size={18} />
            </div>
          </div>
          <div className="reports-stat-value">
            {kpis.ai_adoption_rate ?? 0}<span className="stat-unit">%</span>
          </div>
          <div className="reports-stat-footer">
            <span>{Number(kpis.ai_exercises || 0).toLocaleString('vi-VN')} bài AI / {Number(kpis.regular_exercises || 0).toLocaleString('vi-VN')} bài lớp</span>
          </div>
          <div className="reports-stat-progress-bar lavender"></div>
        </div>

        <div className="reports-stat-card">
          <div className="reports-stat-top">
            <span className="reports-stat-label">ĐIỂM TRUNG BÌNH (GPA)</span>
            <div className="reports-stat-icon-box blue">
              <Star size={18} />
            </div>
          </div>
          <div className="reports-stat-value">
            {kpis.avg_score ?? 0} <span className="stat-unit">/10</span>
          </div>
          <div className="reports-stat-footer">
            <span className="reports-stat-metric-pill blue">
              {Number(kpis.total_attempts || 0).toLocaleString('vi-VN')} lượt nộp
            </span>
            <span>Toàn trường</span>
          </div>
          <div className="reports-stat-progress-bar blue"></div>
        </div>

        <div className="reports-stat-card">
          <div className="reports-stat-top">
            <span className="reports-stat-label">TỶ LỆ HOÀN THÀNH</span>
            <div className="reports-stat-icon-box pink">
              <Sparkles size={18} />
            </div>
          </div>
          <div className="reports-stat-value">
            {kpis.completion_rate ?? 0}<span className="stat-unit">%</span>
          </div>
          <div className="reports-stat-footer">
            <span>{Number(kpis.total_students || 0).toLocaleString('vi-VN')} học sinh • {kpis.total_subjects || 0} môn</span>
          </div>
          <div className="reports-stat-progress-bar pink"></div>
        </div>
      </section>

      {/* 3. Subheader Filter Row */}
      <section className="reports-subheader-filters">
        <div className="reports-dropdowns-group">
          <div className="report-select-wrapper">
            <select value={academicYear} onChange={e => setAcademicYear(e.target.value)} className="report-select">
              <option value="2024 - 2025">Năm học 2024 - 2025</option>
              <option value="2023 - 2024">Năm học 2023 - 2024</option>
            </select>
            <ChevronDown size={13} className="select-icon" />
          </div>

          <div className="report-select-wrapper">
            <select value={semester} onChange={e => setSemester(e.target.value)} className="report-select">
              <option value="Học kỳ II">Học kỳ II</option>
              <option value="Học kỳ I">Học kỳ I</option>
              <option value="Cả năm">Cả năm</option>
            </select>
            <ChevronDown size={13} className="select-icon" />
          </div>

          <div className="report-select-wrapper">
            <select value={gradeFilter} onChange={e => setGradeFilter(e.target.value)} className="report-select">
              <option value="all">Tất cả các khối</option>
              <option value="k10">Khối 10</option>
              <option value="k11">Khối 11</option>
              <option value="k12">Khối 12</option>
            </select>
            <ChevronDown size={13} className="select-icon" />
          </div>

          <div className="report-select-wrapper">
            <select value={deptFilter} onChange={e => setDeptFilter(e.target.value)} className="report-select">
              <option value="all">Tất cả bộ môn</option>
              <option value="math">Toán học</option>
              <option value="physics">Vật lý</option>
              <option value="chemistry">Hóa học</option>
              <option value="biology">Sinh học</option>
              <option value="literature">Ngữ văn</option>
              <option value="history">Lịch sử</option>
              <option value="english">Tiếng Anh</option>
            </select>
            <ChevronDown size={13} className="select-icon" />
          </div>
        </div>
      </section>

      {/* 4. Main Layout */}
      <section className="reports-main-grid">
        <div className="reports-left-column">
          {/* Card 1: Phân bổ kết quả học tập & bài tập theo khối */}
          <div className="report-panel">
            <div className="report-panel-header">
              <div className="panel-title-block">
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
                  <h3 className="panel-title">Phân bổ kết quả học tập & bài tập theo khối</h3>
                  <span className="total-exercises-badge">
                    Tổng số bài tập: <strong>{Number(kpis.total_exercises || 0).toLocaleString('vi-VN')}</strong> bài
                  </span>
                </div>
                <p className="panel-subtitle">Tỷ trọng xếp loại kết quả học tập và khối lượng bài tập theo từng khối toàn trường</p>
              </div>

              {/* Legend */}
              <div className="score-legend-list">
                {legendSegments.map((seg) => (
                  <div key={seg.label} className="score-legend-item">
                    <span className="legend-indicator" style={{ backgroundColor: seg.color }}></span>
                    <span>{seg.label}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Stacked Bars for Grades */}
            <div className="grade-stacked-bars-list">
              {gradeExerciseDistributions.map(item => (
                <div key={item.grade} className="grade-stacked-row">
                  <div className="grade-row-meta">
                    <span className="grade-name">{item.grade} <span className="grade-count">({Number(item.studentsCount || 0).toLocaleString('vi-VN')} học sinh)</span></span>
                    <span className="grade-avg-score">Tổng bài tập: <strong>{Number(item.totalExercises || 0).toLocaleString('vi-VN')} bài</strong></span>
                  </div>

                  <div className="stacked-progress-bar">
                    {(item.segments || []).map(seg => (
                      <div 
                        key={seg.label}
                        className="stacked-bar-segment"
                        style={{ width: `${seg.percent}%`, backgroundColor: seg.color }}
                        title={`${seg.label}: ${Number(seg.count || 0).toLocaleString('vi-VN')} (${seg.percent}%)`}
                      >
                        <span className="segment-text">
                          {seg.percent >= 14 ? `${seg.label}: ${seg.percent}%` : seg.percent >= 7 ? `${seg.percent}%` : ''}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            <div className="report-panel-footer">
              <span className="footer-quality-text">
                Tỷ lệ bài tập tạo sinh ứng dụng AI đạt {kpis.ai_adoption_rate ?? 0}% toàn trường • GPA trung bình {kpis.avg_score ?? 0}/10
              </span>
              <button 
                type="button" 
                className="footer-link-btn"
                onClick={() => setIsExportModalOpen(true)}
              >
                <span>Xuất báo cáo chi tiết</span>
                <ArrowRight size={14} />
              </button>
            </div>
          </div>

          {/* Card 2: Xu hướng hoàn thành bài tập */}
          <div className="report-panel">
            <div className="report-panel-header">
              <div className="panel-title-block">
                <h3 className="panel-title">
                  {timeframe === 'month' ? 'Xu hướng hoàn thành bài tập theo tháng' : 'Xu hướng hoàn thành bài tập theo tuần'}
                </h3>
                <p className="panel-subtitle">Tần suất bài tập truyền thống kết hợp trợ lý AI tạo sinh</p>
              </div>

              <div className="admin-toggle-pill-group">
                <button 
                  type="button" 
                  className={`admin-toggle-pill ${timeframe === 'week' ? 'active' : ''}`}
                  onClick={() => setTimeframe('week')}
                >
                  Theo tuần
                </button>
                <button 
                  type="button" 
                  className={`admin-toggle-pill ${timeframe === 'month' ? 'active' : ''}`}
                  onClick={() => setTimeframe('month')}
                >
                  Theo tháng
                </button>
              </div>
            </div>

            <div className="chart-legend-row">
              <div className="chart-legend-items">
                <div className="chart-legend-item">
                  <span className="legend-dot purple"></span>
                  <span>Bài tập AI tạo sinh: <strong>{Number(kpis.ai_exercises || 0).toLocaleString('vi-VN')}</strong></span>
                </div>
                <div className="chart-legend-item">
                  <span className="legend-dot blue"></span>
                  <span>Bài tập định kỳ: <strong>{Number(kpis.regular_exercises || 0).toLocaleString('vi-VN')}</strong></span>
                </div>
              </div>
              <span className="chart-update-time">
                {isLoadingAnalytics ? 'Đang cập nhật dữ liệu...' : `Cập nhật lúc: ${lastUpdatedText}`}
              </span>
            </div>

            {/* Dual Spline Chart */}
            <div className="reports-chart-wrapper">
              <svg viewBox="0 0 700 250" className="reports-svg-chart">
                <defs>
                  <linearGradient id="aiGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#4D308D" stopOpacity="0.25" />
                    <stop offset="100%" stopColor="#4D308D" stopOpacity="0.0" />
                  </linearGradient>
                  <linearGradient id="regGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#3B82F6" stopOpacity="0.18" />
                    <stop offset="100%" stopColor="#3B82F6" stopOpacity="0.0" />
                  </linearGradient>
                </defs>

                {/* Grid lines */}
                <g className="chart-grid">
                  <line x1="30" y1="50" x2="670" y2="50" stroke="#F1EDF8" strokeDasharray="3 3" />
                  <line x1="30" y1="110" x2="670" y2="110" stroke="#F1EDF8" strokeDasharray="3 3" />
                  <line x1="30" y1="170" x2="670" y2="170" stroke="#F1EDF8" strokeDasharray="3 3" />
                  <line x1="30" y1="230" x2="670" y2="230" stroke="#ECE7F4" />
                </g>

                {/* Fills */}
                {areaPathAi && <path d={areaPathAi} fill="url(#aiGradient)" />}
                {areaPathReg && <path d={areaPathReg} fill="url(#regGradient)" />}

                {/* Curves */}
                {linePathReg && <path d={linePathReg} fill="none" stroke="#3B82F6" strokeWidth="2.4" />}
                {linePathAi && <path d={linePathAi} fill="none" stroke="#4D308D" strokeWidth="2.8" />}

                {/* Data points & X labels with hover interaction */}
                {weeklyData.map(pt => {
                  const isHovered = hoveredWeeklyPoint?.day === pt.day;
                  const hitWidth = weeklyData.length <= 4 ? 120 : 80;
                  return (
                    <g 
                      key={pt.day} 
                      className="chart-data-node"
                      onMouseEnter={() => setHoveredWeeklyPoint(pt)}
                      onMouseLeave={() => setHoveredWeeklyPoint(null)}
                      style={{ cursor: 'pointer' }}
                    >
                      {/* Transparent column hit-area for easy hover */}
                      <rect 
                        x={pt.x - hitWidth / 2} 
                        y={20} 
                        width={hitWidth} 
                        height={215} 
                        fill="transparent" 
                      />

                      {/* Hover dashed vertical guideline */}
                      {isHovered && (
                        <line 
                          x1={pt.x} 
                          y1={25} 
                          x2={pt.x} 
                          y2={230} 
                          stroke="#7C3AED" 
                          strokeWidth="1.2" 
                          strokeDasharray="3 3" 
                          opacity="0.4" 
                        />
                      )}

                      {/* Outer halo rings when hovered */}
                      {isHovered && (
                        <>
                          <circle cx={pt.x} cy={pt.yAi} r="9" fill="#E9D5FF" opacity="0.8" />
                          <circle cx={pt.x} cy={pt.yReg} r="8" fill="#BFDBFE" opacity="0.8" />
                        </>
                      )}

                      {/* AI circle */}
                      <circle 
                        cx={pt.x} 
                        cy={pt.yAi} 
                        r={isHovered ? 5.5 : 4} 
                        fill={isHovered ? '#4D308D' : '#FFFFFF'} 
                        stroke="#4D308D" 
                        strokeWidth={isHovered ? 2.5 : 2} 
                      />

                      {/* Regular circle */}
                      <circle 
                        cx={pt.x} 
                        cy={pt.yReg} 
                        r={isHovered ? 5 : 3.5} 
                        fill={isHovered ? '#2563EB' : '#FFFFFF'} 
                        stroke="#2563EB" 
                        strokeWidth={isHovered ? 2.5 : 2} 
                      />

                      {/* Day label */}
                      <text 
                        x={pt.x} 
                        y="246" 
                        className={`chart-x-axis-text ${isHovered ? 'hovered' : ''}`} 
                        textAnchor="middle"
                      >
                        {pt.day}
                      </text>
                    </g>
                  );
                })}

                {/* Floating Tooltip showing detail exercise counts of hovered node */}
                {hoveredWeeklyPoint && (() => {
                  const boxWidth = 175;
                  const boxHeight = 76;
                  const boxX = Math.max(25, Math.min(675 - boxWidth, hoveredWeeklyPoint.x - boxWidth / 2));
                  const topPointY = Math.min(hoveredWeeklyPoint.yAi, hoveredWeeklyPoint.yReg);
                  const boxY = Math.max(6, topPointY - boxHeight - 12);
                  const pointerPoints = `${hoveredWeeklyPoint.x - 5},${boxY + boxHeight} ${hoveredWeeklyPoint.x},${boxY + boxHeight + 6} ${hoveredWeeklyPoint.x + 5},${boxY + boxHeight}`;

                  return (
                    <g className="chart-dynamic-tooltip" style={{ pointerEvents: 'none' }}>
                      {/* Tooltip background card */}
                      <rect 
                        x={boxX} 
                        y={boxY} 
                        width={boxWidth} 
                        height={boxHeight} 
                        rx="8" 
                        fill="#1E1B2E" 
                        stroke="#38324E"
                        strokeWidth="1"
                        style={{ filter: 'drop-shadow(0 6px 16px rgba(0, 0, 0, 0.28))' }}
                      />
                      {/* Downward pointer triangle */}
                      <polygon 
                        points={pointerPoints} 
                        fill="#1E1B2E" 
                      />

                      {/* Day & Total badge */}
                      <text x={boxX + 12} y={boxY + 18} fill="#FFFFFF" fontSize="11.5" fontWeight="700">
                        {hoveredWeeklyPoint.day}
                      </text>
                      <text x={boxX + boxWidth - 12} y={boxY + 18} fill="#C4B5FD" fontSize="10.5" fontWeight="600" textAnchor="end">
                        {(hoveredWeeklyPoint.ai + hoveredWeeklyPoint.regular).toLocaleString('vi-VN')} bài
                      </text>

                      {/* Divider */}
                      <line 
                        x1={boxX + 10} 
                        y1={boxY + 25} 
                        x2={boxX + boxWidth - 10} 
                        y2={boxY + 25} 
                        stroke="#38324E" 
                        strokeWidth="0.8" 
                      />

                      {/* AI exercise count row */}
                      <circle cx={boxX + 17} cy={boxY + 41} r="3.5" fill="#A78BFA" />
                      <text x={boxX + 27} y={boxY + 44} fill="#94A3B8" fontSize="10" fontWeight="500">
                        AI tạo sinh:
                      </text>
                      <text x={boxX + boxWidth - 12} y={boxY + 44} fill="#FFFFFF" fontSize="10.5" fontWeight="700" textAnchor="end">
                        {hoveredWeeklyPoint.ai.toLocaleString('vi-VN')} bài
                      </text>

                      {/* Regular exercise count row */}
                      <circle cx={boxX + 17} cy={boxY + 59} r="3.5" fill="#60A5FA" />
                      <text x={boxX + 27} y={boxY + 62} fill="#94A3B8" fontSize="10" fontWeight="500">
                        Bài tập trên lớp:
                      </text>
                      <text x={boxX + boxWidth - 12} y={boxY + 62} fill="#FFFFFF" fontSize="10.5" fontWeight="700" textAnchor="end">
                        {hoveredWeeklyPoint.regular.toLocaleString('vi-VN')} bài
                      </text>
                    </g>
                  );
                })()}
              </svg>
            </div>
          </div>

          {/* Card 3: Lịch gửi báo cáo tự động */}
          <div className="report-panel">
            <div className="report-panel-header">
              <div className="panel-title-block">
                <h3 className="panel-title">Lịch gửi báo cáo tự động</h3>
                <p className="panel-subtitle">Danh sách lịch trình tổng hợp và gửi báo cáo định kỳ tới Ban Giám Hiệu</p>
              </div>
              <button
                type="button"
                className="btn-schedule-link"
                onClick={() => setIsScheduleModalOpen(true)}
              >
                + Thêm lịch gửi mới
              </button>
            </div>

            {schedules.length === 0 ? (
              <p className="panel-subtitle">Chưa có lịch gửi báo cáo tự động nào được cấu hình.</p>
            ) : (
              <div className="scheduled-reports-list">
                {schedules.map((sched) => (
                  <div key={sched.id} className="scheduled-report-item">
                    <div className="scheduled-icon-box purple">
                      <Calendar size={16} />
                    </div>
                    <div className="scheduled-meta">
                      <h4 className="scheduled-title">{sched.title}</h4>
                      <p className="scheduled-time">
                        {FREQUENCY_LABEL_VI[sched.frequency] || sched.frequency} • Định dạng {String(sched.format || 'csv').toUpperCase()} • {(sched.recipients || []).join(', ')}
                      </p>
                    </div>
                    <span className="scheduled-status-pill green">Đang hoạt động</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </section>

      {/* MODAL: Xuất dữ liệu PDF/Excel */}
      {isExportModalOpen && (
        <div className="admin-modal-backdrop" onClick={() => setIsExportModalOpen(false)}>
          <div className="admin-modal-card" onClick={e => e.stopPropagation()}>
            <div className="admin-modal-header">
              <h3 className="admin-modal-title">Xuất báo cáo dữ liệu toàn trường</h3>
              <button type="button" className="admin-modal-close" onClick={() => setIsExportModalOpen(false)}>
                <X size={20} />
              </button>
            </div>
            <div className="admin-modal-body">
              <p className="admin-modal-desc">
                Tải xuống bản báo cáo tổng hợp toàn diện các chỉ số học lực, chuyên cần và hiệu suất {semester} ({academicYear}).
              </p>
              <div className="admin-form-group">
                <label className="admin-form-label">Định dạng tập tin</label>
                <div className="export-options-row">
                  <label className="export-option-box">
                    <input
                      type="radio"
                      name="reportExportFormat"
                      value="pdf"
                      checked={exportFormat === 'pdf'}
                      onChange={() => setExportFormat('pdf')}
                    />
                    <span>Tài liệu In Ấn / PDF (.html)</span>
                  </label>
                  <label className="export-option-box">
                    <input
                      type="radio"
                      name="reportExportFormat"
                      value="csv"
                      checked={exportFormat === 'csv'}
                      onChange={() => setExportFormat('csv')}
                    />
                    <span>Bảng tính Excel / CSV (.csv)</span>
                  </label>
                  <label className="export-option-box">
                    <input
                      type="radio"
                      name="reportExportFormat"
                      value="json"
                      checked={exportFormat === 'json'}
                      onChange={() => setExportFormat('json')}
                    />
                    <span>Dữ liệu JSON (.json)</span>
                  </label>
                </div>
              </div>

              <div className="admin-modal-footer">
                <button type="button" className="admin-btn-cancel" onClick={() => setIsExportModalOpen(false)}>
                  Đóng
                </button>
                <button 
                  type="button" 
                  className="admin-btn-primary"
                  onClick={handleExportReport}
                  disabled={isExporting}
                >
                  <Download size={16} />
                  <span>{isExporting ? 'Đang tạo tệp...' : 'Tải xuống'}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* MODAL: Tạo báo cáo tùy chỉnh */}
      {isCustomReportModalOpen && (
        <div className="admin-modal-backdrop" onClick={() => setIsCustomReportModalOpen(false)}>
          <div className="admin-modal-card" onClick={e => e.stopPropagation()}>
            <div className="admin-modal-header">
              <h3 className="admin-modal-title">Tạo mẫu báo cáo tùy chỉnh</h3>
              <button type="button" className="admin-modal-close" onClick={() => setIsCustomReportModalOpen(false)}>
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleCreateCustomReport} className="admin-modal-body">
              <div className="admin-form-group">
                <label className="admin-form-label">Tên báo cáo *</label>
                <input 
                  type="text" 
                  className="admin-form-input" 
                  placeholder="Ví dụ: Báo cáo tỷ lệ nộp bài tập AI khối 12" 
                  value={customReport.title}
                  onChange={e => setCustomReport(p => ({ ...p, title: e.target.value }))}
                  required 
                />
              </div>

              <div className="admin-form-group">
                <label className="admin-form-label">Nhóm chỉ số phân tích</label>
                <select 
                  className="admin-form-select"
                  value={customReport.metricType}
                  onChange={e => setCustomReport(p => ({ ...p, metricType: e.target.value }))}
                >
                  <option value="academic">Học lực & Điểm kiểm tra</option>
                  <option value="attendance">Chuyên cần & Tương tác LMS</option>
                  <option value="exercises">Tiến độ bài tập & Đề thi AI</option>
                  <option value="system">Tài nguyên máy chủ & Tải mạng</option>
                </select>
              </div>

              <div className="admin-form-group">
                <label className="admin-form-label">Định dạng xuất báo cáo</label>
                <select
                  className="admin-form-select"
                  value={customReport.format}
                  onChange={e => setCustomReport(p => ({ ...p, format: e.target.value }))}
                >
                  <option value="pdf">Tài liệu In Ấn / PDF</option>
                  <option value="csv">Bảng tính Excel / CSV</option>
                  <option value="json">Dữ liệu JSON</option>
                </select>
              </div>

              <div className="admin-modal-footer">
                <button type="button" className="admin-btn-cancel" onClick={() => setIsCustomReportModalOpen(false)}>
                  Hủy
                </button>
                <button type="submit" className="admin-btn-primary" disabled={isCreatingCustom}>
                  {isCreatingCustom ? 'Đang tạo...' : 'Tạo báo cáo'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: Lên lịch gửi báo cáo tự động */}
      {isScheduleModalOpen && (
        <div className="admin-modal-backdrop" onClick={() => setIsScheduleModalOpen(false)}>
          <div className="admin-modal-card" onClick={e => e.stopPropagation()}>
            <div className="admin-modal-header">
              <h3 className="admin-modal-title">Lên lịch gửi báo cáo tự động</h3>
              <button type="button" className="admin-modal-close" onClick={() => setIsScheduleModalOpen(false)}>
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleCreateSchedule} className="admin-modal-body">
              <div className="admin-form-group">
                <label className="admin-form-label">Tiêu đề lịch gửi</label>
                <input
                  type="text"
                  className="admin-form-input"
                  placeholder="Ví dụ: Báo cáo điểm danh định kỳ thứ Sáu"
                  value={scheduleForm.title}
                  onChange={e => setScheduleForm(p => ({ ...p, title: e.target.value }))}
                  required
                />
              </div>

              <div className="admin-form-group">
                <label className="admin-form-label">Tần suất gửi</label>
                <select
                  className="admin-form-select"
                  value={scheduleForm.frequency}
                  onChange={e => setScheduleForm(p => ({ ...p, frequency: e.target.value }))}
                >
                  <option value="weekly">Hàng tuần (Thứ Hai 07:00 AM)</option>
                  <option value="monthly">Hàng tháng (Ngày 28 hàng tháng)</option>
                  <option value="daily">Mỗi ngày (Cuối ngày 18:00 PM)</option>
                </select>
              </div>

              <div className="admin-form-group">
                <label className="admin-form-label">Định dạng tệp đính kèm</label>
                <select
                  className="admin-form-select"
                  value={scheduleForm.format}
                  onChange={e => setScheduleForm(p => ({ ...p, format: e.target.value }))}
                >
                  <option value="csv">Bảng tính Excel / CSV</option>
                  <option value="pdf">Tài liệu In Ấn / PDF</option>
                  <option value="json">Dữ liệu JSON</option>
                </select>
              </div>

              <div className="admin-form-group">
                <label className="admin-form-label">Email người nhận (cách nhau dấu phẩy)</label>
                <input
                  type="text"
                  className="admin-form-input"
                  placeholder="hieutruong@school.edu.vn, bgh@school.edu.vn"
                  value={scheduleForm.recipientsText}
                  onChange={e => setScheduleForm(p => ({ ...p, recipientsText: e.target.value }))}
                  required
                />
              </div>

              <div className="admin-modal-footer">
                <button type="button" className="admin-btn-cancel" onClick={() => setIsScheduleModalOpen(false)}>
                  Hủy
                </button>
                <button type="submit" className="admin-btn-primary" disabled={isCreatingSchedule}>
                  {isCreatingSchedule ? 'Đang lưu...' : 'Lưu lịch gửi'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
