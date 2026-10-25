// File Name: AdminReportsPage.jsx
// Description: Comprehensive Reports & Analytics screen for Admin portal with GPA distributions, dual spline trend charts, Bloom taxonomy donut, and early intervention alerts.
// Created At: 2026-09-19
// Created By: Tam Khang
// Updated At: 2026-09-20
// Updated By: Tam Khang

import React, { useState } from 'react';
import { 
  BarChart3, 
  Download, 
  Plus, 
  TrendingUp, 
  Star, 
  ClipboardCheck, 
  Clock, 
  ChevronDown, 
  ChevronRight, 
  ArrowRight, 
  AlertTriangle, 
  Mail, 
  Send, 
  CheckCircle2, 
  Calendar, 
  Cpu, 
  FileText, 
  PieChart, 
  Sliders, 
  X, 
  Sparkles,
  HelpCircle
} from 'lucide-react';
import './AdminReportsPage.css';

export default function AdminReportsPage() {
  // State for filters
  const [timeframe, setTimeframe] = useState('week'); // 'week' | 'month'
  const [academicYear, setAcademicYear] = useState('2024 - 2025');
  const [semester, setSemester] = useState('Học kỳ II');
  const [gradeFilter, setGradeFilter] = useState('all');
  const [deptFilter, setDeptFilter] = useState('all');
  const [hoveredWeeklyPoint, setHoveredWeeklyPoint] = useState(null);

  // Modals state
  const [isExportModalOpen, setIsExportModalOpen] = useState(false);
  const [isCustomReportModalOpen, setIsCustomReportModalOpen] = useState(false);
  const [isScheduleModalOpen, setIsScheduleModalOpen] = useState(false);
  const [toastMessage, setToastMessage] = useState(null);

  // Custom report form state
  const [customReport, setCustomReport] = useState({
    title: '',
    metricType: 'academic',
    format: 'pdf',
    frequency: 'weekly'
  });

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => {
      setToastMessage(null);
    }, 3500);
  };

  // Stacked bar data for grade exercise distributions (bài tập trên lớp và bài tập tạo sinh)
  const gradeExerciseDistributions = [
    {
      grade: 'Khối 12',
      studentsCount: 820,
      totalExercises: 17200,
      segments: [
        { label: 'Bài tập trên lớp', count: 5800, percent: 33.7, color: '#30a1cbff' },
        { label: 'Bài tập tạo sinh', count: 11400, percent: 66.3, color: '#7C3AED' }
      ]
    },
    {
      grade: 'Khối 11',
      studentsCount: 810,
      totalExercises: 15800,
      segments: [
        { label: 'Bài tập trên lớp', count: 5600, percent: 35.4, color: '#30a1cbff' },
        { label: 'Bài tập tạo sinh', count: 10200, percent: 64.6, color: '#7C3AED' }
      ]
    },
    {
      grade: 'Khối 10',
      studentsCount: 820,
      totalExercises: 15250,
      segments: [
        { label: 'Bài tập trên lớp', count: 5400, percent: 35.4, color: '#30a1cbff' },
        { label: 'Bài tập tạo sinh', count: 9850, percent: 64.6, color: '#7C3AED' }
      ]
    }
  ];


  // Dual spline area curves data
  const weeklyData = [
    { day: 'Thứ 2', ai: 3100, regular: 1800, x: 45, yAi: 165, yReg: 195 },
    { day: 'Thứ 3', ai: 4200, regular: 2400, x: 145, yAi: 140, yReg: 180 },
    { day: 'Thứ 4', ai: 5100, regular: 2800, x: 245, yAi: 115, yReg: 165 },
    { day: 'Thứ 5', ai: 5600, regular: 3100, x: 345, yAi: 100, yReg: 155 },
    { day: 'Thứ 6', ai: 6840, regular: 3900, x: 445, yAi: 70, yReg: 135 },
    { day: 'Thứ 7', ai: 4900, regular: 2700, x: 545, yAi: 120, yReg: 170 },
    { day: 'Chủ nhật', ai: 3600, regular: 2100, x: 645, yAi: 150, yReg: 185 },
  ];

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
  const areaPathAi = `${linePathAi} L ${weeklyData[weeklyData.length - 1].x} 230 L ${weeklyData[0].x} 230 Z`;
  const areaPathReg = `${linePathReg} L ${weeklyData[weeklyData.length - 1].x} 230 L ${weeklyData[0].x} 230 Z`;

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
            <span className="tag-accent">NĂM HỌC 2024 - 2025</span>
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

      {/* 2. Subheader Filter Row */}
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
              <option value="literature">Ngữ văn</option>
              <option value="english">Tiếng Anh</option>
              <option value="physics">Vật lý</option>
            </select>
            <ChevronDown size={13} className="select-icon" />
          </div>
        </div>
      </section>

      {/* 4. Main Two Column Layout */}
      <section className="reports-main-grid">
        {/* LEFT COLUMN: 3 Cards */}
        <div className="reports-left-column">
          {/* Card 1: Phân bổ loại bài tập theo khối */}
          <div className="report-panel">
            <div className="report-panel-header">
              <div className="panel-title-block">
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
                  <h3 className="panel-title">Phân bổ loại bài tập theo khối</h3>
                  <span className="total-exercises-badge">
                    Tổng số bài tập: <strong>48,250</strong> bài
                  </span>
                </div>
                <p className="panel-subtitle">Tỷ trọng bài tập trên lớp và bài tập tạo sinh theo từng khối toàn trường</p>
              </div>

              {/* Legend */}
              <div className="score-legend-list">
                <div className="score-legend-item">
                  <span className="legend-indicator" style={{ backgroundColor: '#2563EB' }}></span>
                  <span>Bài tập trên lớp: <strong>16,800 bài</strong></span>
                </div>
                <div className="score-legend-item">
                  <span className="legend-indicator" style={{ backgroundColor: '#7C3AED' }}></span>
                  <span>Bài tập tạo sinh: <strong>31,450 bài</strong></span>
                </div>
              </div>
            </div>

            {/* Stacked Bars for Grades */}
            <div className="grade-stacked-bars-list">
              {gradeExerciseDistributions.map(item => (
                <div key={item.grade} className="grade-stacked-row">
                  <div className="grade-row-meta">
                    <span className="grade-name">{item.grade} <span className="grade-count">({item.studentsCount} học sinh)</span></span>
                    <span className="grade-avg-score">Tổng bài tập: <strong>{item.totalExercises.toLocaleString('vi-VN')} bài</strong></span>
                  </div>

                  <div className="stacked-progress-bar">
                    {item.segments.map(seg => (
                      <div 
                        key={seg.label}
                        className="stacked-bar-segment"
                        style={{ width: `${seg.percent}%`, backgroundColor: seg.color }}
                        title={`${seg.label}: ${seg.count.toLocaleString('vi-VN')} bài (${seg.percent}%)`}
                      >
                        <span className="segment-text">{seg.label}: {seg.count.toLocaleString('vi-VN')} bài</span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            <div className="report-panel-footer">
              <span className="footer-quality-text">Tỷ lệ bài tập tạo sinh ứng dụng AI đạt 65.2% toàn trường</span>
              <button 
                type="button" 
                className="footer-link-btn"
                onClick={() => showToast('Đang tải danh sách phân tích chi tiết bài tập từng môn...')}
              >
                <span>Xem chi tiết bài tập theo môn</span>
                <ArrowRight size={14} />
              </button>
            </div>
          </div>

          {/* Card 2: Xu hướng hoàn thành bài tập theo tuần */}
          <div className="report-panel">
            <div className="report-panel-header">
              <div className="panel-title-block">
                <h3 className="panel-title">Xu hướng hoàn thành bài tập theo tuần</h3>
                <p className="panel-subtitle">Tần suất nộp bài tập hệ thống truyền thống kết hợp trợ lý AI tạo sinh</p>
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
                  <span>Bài tập AI tạo sinh: <strong>31,450</strong></span>
                </div>
                <div className="chart-legend-item">
                  <span className="legend-dot blue"></span>
                  <span>Bài tập định kỳ: <strong>16,800</strong></span>
                </div>
              </div>
              <span className="chart-update-time">Cập nhật: 10 phút trước</span>
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
                <path d={areaPathAi} fill="url(#aiGradient)" />
                <path d={areaPathReg} fill="url(#regGradient)" />

                {/* Curves */}
                <path d={linePathReg} fill="none" stroke="#3B82F6" strokeWidth="2.4" />
                <path d={linePathAi} fill="none" stroke="#4D308D" strokeWidth="2.8" />

                {/* Data points & X labels with hover interaction */}
                {weeklyData.map(pt => {
                  const isHovered = hoveredWeeklyPoint?.day === pt.day;
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
                        x={pt.x - 45} 
                        y={20} 
                        width={90} 
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
                        {(hoveredWeeklyPoint.ai + hoveredWeeklyPoint.regular).toLocaleString('vi-VN')} bài nộp
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
                Tải xuống bản báo cáo tổng hợp toàn diện các chỉ số học lực, chuyên cần và hiệu suất học kỳ II.
              </p>
              <div className="admin-form-group">
                <label className="admin-form-label">Định dạng tập tin</label>
                <div className="export-options-row">
                  <label className="export-option-box">
                    <input type="radio" name="reportExportFormat" defaultChecked />
                    <span>Tài liệu PDF In Ấn (.pdf)</span>
                  </label>
                  <label className="export-option-box">
                    <input type="radio" name="reportExportFormat" />
                    <span>Bảng tính Excel Đầy Đủ (.xlsx)</span>
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
                  onClick={() => {
                    setIsExportModalOpen(false);
                    showToast('Đang tạo và tải xuống tài liệu báo cáo...');
                  }}
                >
                  <Download size={16} />
                  <span>Tải xuống</span>
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
            <form onSubmit={e => {
              e.preventDefault();
              setIsCustomReportModalOpen(false);
              showToast(`Đã tạo mẫu báo cáo tùy chỉnh "${customReport.title || 'Báo cáo mới'}"!`);
            }} className="admin-modal-body">
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

              <div className="admin-modal-footer">
                <button type="button" className="admin-btn-cancel" onClick={() => setIsCustomReportModalOpen(false)}>
                  Hủy
                </button>
                <button type="submit" className="admin-btn-primary">
                  Tạo báo cáo
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
            <form onSubmit={e => {
              e.preventDefault();
              setIsScheduleModalOpen(false);
              showToast('Đã thiết lập lịch gửi email báo cáo tự động thành công!');
            }} className="admin-modal-body">
              <div className="admin-form-group">
                <label className="admin-form-label">Tiêu đề lịch gửi</label>
                <input type="text" className="admin-form-input" placeholder="Ví dụ: Báo cáo điểm danh định kỳ thứ Sáu" required />
              </div>

              <div className="admin-form-group">
                <label className="admin-form-label">Tần suất gửi</label>
                <select className="admin-form-select">
                  <option>Hàng tuần (Thứ Hai 07:00 AM)</option>
                  <option>Hàng tháng (Ngày 28 hàng tháng)</option>
                  <option>Mỗi ngày (Cuối ngày 18:00 PM)</option>
                </select>
              </div>

              <div className="admin-form-group">
                <label className="admin-form-label">Email người nhận (cách nhau dấu phẩy)</label>
                <input type="text" className="admin-form-input" placeholder="hieutruong@school.edu.vn, bgh@school.edu.vn" required />
              </div>

              <div className="admin-modal-footer">
                <button type="button" className="admin-btn-cancel" onClick={() => setIsScheduleModalOpen(false)}>
                  Hủy
                </button>
                <button type="submit" className="admin-btn-primary">
                  Lưu lịch gửi
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
