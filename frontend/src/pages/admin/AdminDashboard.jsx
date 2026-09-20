// File Name: AdminDashboard.jsx
// Description: Master Admin Dashboard with system operations metrics, server status, LMS traffic chart, approval queue, and audit logs.
// Created At: 2026-09-19
// Created By: Tam Khang
// Updated At: 2026-09-20
// Updated By: Tam Khang

import React, { useState } from 'react';
import { 
  GraduationCap, 
  Users, 
  Building2, 
  Cloud, 
  Download, 
  UserPlus, 
  TrendingUp, 
  Shield, 
  AlertTriangle, 
  CheckCircle2, 
  Clock, 
  ChevronRight, 
  ArrowUpRight, 
  FileText, 
  Sparkles,
  X
} from 'lucide-react';
import './AdminDashboard.css';

export default function AdminDashboard() {
  const [timeframe, setTimeframe] = useState('week'); // 'week' | 'month'
  const [hoveredIndex, setHoveredIndex] = useState(null);
  const [showCreateUserModal, setShowCreateUserModal] = useState(false);
  const [showExportModal, setShowExportModal] = useState(false);
  const [showAuditModal, setShowAuditModal] = useState(false);
  const [toastMessage, setToastMessage] = useState(null);

  // Approval requests state
  const [requests, setRequests] = useState([
    {
      id: 1,
      requesterName: 'ThS. Lê Nguyên',
      requesterSub: 'lenguyen@edu.vn',
      avatarText: 'LN',
      avatarBg: '#5B35A8',
      type: 'Cấp tài khoản Giảng viên mới',
      time: '15 phút trước',
      status: 'pending', // pending | approved | rejected
    },
    {
      id: 2,
      requesterName: 'Trần Minh Phong',
      requesterSub: 'Toán - Tin học',
      avatarText: 'TP',
      avatarBg: '#8B2C9A',
      type: 'Mở thêm lớp Chuyên Toán 10-T1',
      time: '1 giờ trước',
      status: 'pending',
    },
    {
      id: 3,
      requesterName: 'Hệ thống Bảo mật',
      requesterSub: 'SSL / DNS Automation',
      isSystem: true,
      type: 'Gia hạn chứng chỉ SSL / Domain',
      time: 'Hôm qua',
      status: 'processed',
    }
  ]);

  // Form state for Create User modal
  const [newUser, setNewUser] = useState({
    fullName: '',
    email: '',
    phone: '',
    role: 'Teacher',
    department: 'Toán học'
  });

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => {
      setToastMessage(null);
    }, 3500);
  };

  const handleApprove = (id) => {
    setRequests(prev => prev.map(req => {
      if (req.id === id) {
        return { ...req, status: 'approved' };
      }
      return req;
    }));
    showToast('Đã phê duyệt yêu cầu thành công!');
  };

  const handleReject = (id) => {
    setRequests(prev => prev.map(req => {
      if (req.id === id) {
        return { ...req, status: 'rejected' };
      }
      return req;
    }));
    showToast('Đã từ chối yêu cầu.');
  };

  const handleCreateUserSubmit = (e) => {
    e.preventDefault();
    if (!newUser.fullName || !newUser.email) {
      alert('Vui lòng nhập đầy đủ họ tên và email.');
      return;
    }
    setShowCreateUserModal(false);
    showToast(`Đã tạo tài khoản cho ${newUser.fullName} thành công!`);
    setNewUser({
      fullName: '',
      email: '',
      phone: '',
      role: 'Teacher',
      department: 'Toán học'
    });
  };

  // Weekly data points for area chart
  const weeklyData = [
    { day: 'T2', visits: 850, x: 50, y: 190 },
    { day: 'T3', visits: 1450, x: 140, y: 155 },
    { day: 'T4', visits: 2250, x: 230, y: 105 },
    { day: 'T5', visits: 2350, x: 320, y: 100 },
    { day: 'T6 (Đỉnh)', visits: 2840, x: 410, y: 70, isPeak: true },
    { day: 'T7', visits: 2200, x: 500, y: 110 },
    { day: 'CN', visits: 1250, x: 590, y: 165 },
  ];

  const monthlyData = [
    { day: 'Tuần 1', visits: 12400, x: 70, y: 170 },
    { day: 'Tuần 2', visits: 15800, x: 210, y: 125 },
    { day: 'Tuần 3 (Đỉnh)', visits: 19400, x: 380, y: 65, isPeak: true },
    { day: 'Tuần 4', visits: 14600, x: 550, y: 140 },
  ];

  const currentChartData = timeframe === 'week' ? weeklyData : monthlyData;

  // Path generator for SVG smooth spline curve
  const generateSvgPath = (points) => {
    if (!points || points.length === 0) return '';
    let d = `M ${points[0].x} ${points[0].y}`;
    for (let i = 0; i < points.length - 1; i++) {
      const p0 = points[i];
      const p1 = points[i + 1];
      const cp1x = p0.x + (p1.x - p0.x) / 2;
      const cp1y = p0.y;
      const cp2x = p0.x + (p1.x - p0.x) / 2;
      const cp2y = p1.y;
      d += ` C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${p1.x} ${p1.y}`;
    }
    return d;
  };

  const linePath = generateSvgPath(currentChartData);
  const areaPath = `${linePath} L ${currentChartData[currentChartData.length - 1].x} 230 L ${currentChartData[0].x} 230 Z`;

  return (
    <div className="admin-dashboard-container">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="admin-toast">
          <CheckCircle2 size={18} />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* 1. Header Welcome Row */}
      <section className="admin-welcome-section">
        <div className="admin-welcome-left">
          <div className="admin-semester-badge">
            <span className="admin-semester-tag">BẢNG ĐIỀU KHIỂN QUẢN TRỊ</span>
            <span className="admin-semester-dot">•</span>
            <span className="admin-semester-term">HỌC KỲ II - 2024</span>
          </div>
          <h1 className="admin-welcome-title">
            Xin chào, Quản trị viên! <span className="greeting-wave">👋</span>
          </h1>
          <p className="admin-welcome-subtitle">
            Dưới đây là thông số vận hành, trạng thái máy chủ và tổng quan người dùng toàn trường hôm nay.
          </p>
        </div>

        <div className="admin-welcome-actions">
          <div className="header-ai-status-card">
            <div className="header-ai-icon-box">
              <Sparkles size={18} />
            </div>
            <div className="header-ai-info">
              <h4 className="header-ai-name">API AI Tạo bài tập</h4>
              <p className="header-ai-desc">Độ trễ phản hồi: 120ms</p>
            </div>
            <span className="header-ai-badge">Ổn định</span>
          </div>
        </div>
      </section>

      {/* 3. Middle Section: Traffic Chart & Infrastructure */}
      <section className="admin-dashboard-row middle-row">
        {/* Left: LMS Traffic & Engagement */}
        <div className="admin-panel traffic-panel">
          <div className="admin-panel-header">
            <div>
              <h2 className="admin-panel-title">Lưu lượng truy cập & Tương tác LMS</h2>
              <p className="admin-panel-subtitle">
                Tần suất người dùng hoạt động (Học sinh, Giảng viên) trong tuần qua
              </p>
            </div>
            {/* Week / Month Toggle */}
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

          {/* Interactive Area Chart */}
          <div className="admin-chart-wrapper">
            <svg viewBox="0 0 660 250" className="admin-svg-chart">
              <defs>
                <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#6339A8" stopOpacity="0.25" />
                  <stop offset="100%" stopColor="#6339A8" stopOpacity="0.0" />
                </linearGradient>
              </defs>

              {/* Grid Lines & Labels */}
              <g className="chart-grid">
                <line x1="40" y1="50" x2="620" y2="50" stroke="#F1EDF8" strokeDasharray="3 3" />
                <text x="25" y="54" className="chart-axis-label">3k</text>

                <line x1="40" y1="110" x2="620" y2="110" stroke="#F1EDF8" strokeDasharray="3 3" />
                <text x="25" y="114" className="chart-axis-label">2k</text>

                <line x1="40" y1="170" x2="620" y2="170" stroke="#F1EDF8" strokeDasharray="3 3" />
                <text x="25" y="174" className="chart-axis-label">1k</text>

                <line x1="40" y1="230" x2="620" y2="230" stroke="#ECE7F4" />
                <text x="25" y="234" className="chart-axis-label">0</text>
              </g>

              {/* Area fill */}
              <path d={areaPath} fill="url(#chartGradient)" />

              {/* Spline curve stroke */}
              <path d={linePath} fill="none" stroke="#4D308D" strokeWidth="2.8" strokeLinecap="round" />

              {/* Peak Tooltip Highlight on Friday */}
              {timeframe === 'week' && (
                <g className="chart-peak-tooltip">
                  <rect x="360" y="32" width="102" height="26" rx="6" fill="#1D1928" />
                  <text x="411" y="49" fill="#FFFFFF" fontSize="11.5" fontWeight="600" textAnchor="middle">
                    2,840 truy cập
                  </text>
                  <polygon points="411,58 406,64 416,64" fill="#1D1928" />
                  <line x1="410" y1="64" x2="410" y2="70" stroke="#4D308D" strokeWidth="1.5" />
                </g>
              )}

              {/* Interactive Data Points */}
              {currentChartData.map((pt, idx) => (
                <g key={pt.day} onMouseEnter={() => setHoveredIndex(idx)} onMouseLeave={() => setHoveredIndex(null)}>
                  {/* Outer circle halo on peak or hover */}
                  {(pt.isPeak || hoveredIndex === idx) && (
                    <circle cx={pt.x} cy={pt.y} r="8" fill="#E8DAFF" opacity="0.8" />
                  )}
                  <circle 
                    cx={pt.x} 
                    cy={pt.y} 
                    r="4.5" 
                    fill={pt.isPeak ? '#4D308D' : '#FFFFFF'} 
                    stroke="#4D308D" 
                    strokeWidth="2.2" 
                    className="chart-data-point"
                  />
                  {/* X Axis Day Label */}
                  <text 
                    x={pt.x} 
                    y="246" 
                    className={`chart-x-label ${pt.isPeak ? 'peak-label' : ''}`}
                    textAnchor="middle"
                  >
                    {pt.day}
                  </text>
                </g>
              ))}
            </svg>
          </div>

          {/* Chart Footer Legend */}
          <div className="admin-chart-footer">
            <div className="chart-legend-items">
              <div className="legend-item">
                <span className="legend-dot purple"></span>
                <span>Lượt xem bài giảng: <strong>14,200</strong></span>
              </div>
              <div className="legend-item">
                <span className="legend-dot blue"></span>
                <span>Bài tập đã nộp: <strong>3,489</strong></span>
              </div>
            </div>
            <div className="chart-update-time">
              Cập nhật lúc: 10 phút trước
            </div>
          </div>
        </div>
      </section>

      {/* 4. Bottom Section: Approval Requests & Audit Logs */}
      <section className="admin-dashboard-row bottom-row">
        {/* Left: Yêu cầu phê duyệt & Hoạt động gần đây */}
        <div className="admin-panel approvals-panel">
          <div className="admin-panel-header">
            <div>
              <h2 className="admin-panel-title">Yêu cầu phê duyệt & Hoạt động gần đây</h2>
              <p className="admin-panel-subtitle">
                Có 3 yêu cầu khẩn cấp cần quản trị viên xử lý
              </p>
            </div>
            <button 
              type="button" 
              className="admin-link-btn"
              onClick={() => showToast('Đang mở toàn bộ danh sách yêu cầu phê duyệt...')}
            >
              <span>Xem tất cả</span>
              <ChevronRight size={16} />
            </button>
          </div>

          <div className="admin-table-container">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>NGƯỜI YÊU CẦU</th>
                  <th>LOẠI YÊU CẦU</th>
                  <th>THỜI GIAN</th>
                  <th>TRẠNG THÁI</th>
                  <th className="text-right">THAO TÁC</th>
                </tr>
              </thead>
              <tbody>
                {requests.map(req => (
                  <tr key={req.id}>
                    {/* Requester Column */}
                    <td>
                      <div className="table-user-cell">
                        {req.isSystem ? (
                          <div className="table-system-avatar">
                            <Shield size={16} />
                          </div>
                        ) : (
                          <div className="table-user-avatar" style={{ backgroundColor: req.avatarBg }}>
                            {req.avatarText}
                          </div>
                        )}
                        <div className="table-user-meta">
                          <span className="table-user-name">{req.requesterName}</span>
                          <span className="table-user-sub">{req.requesterSub}</span>
                        </div>
                      </div>
                    </td>

                    {/* Request Type */}
                    <td className="table-type-cell">
                      <span>{req.type}</span>
                    </td>

                    {/* Time */}
                    <td className="table-time-cell">
                      <span>{req.time}</span>
                    </td>

                    {/* Status Pill */}
                    <td>
                      {req.status === 'pending' && (
                        <span className="status-pill pending">
                          <span className="pill-dot amber"></span>
                          Chờ duyệt
                        </span>
                      )}
                      {req.status === 'approved' && (
                        <span className="status-pill approved">
                          <span className="pill-dot green"></span>
                          Đã duyệt
                        </span>
                      )}
                      {req.status === 'rejected' && (
                        <span className="status-pill rejected">
                          <span className="pill-dot red"></span>
                          Từ chối
                        </span>
                      )}
                      {req.status === 'processed' && (
                        <span className="status-pill processed">
                          <span className="pill-dot green"></span>
                          Đã xử lý
                        </span>
                      )}
                    </td>

                    {/* Action Buttons */}
                    <td className="text-right">
                      {req.status === 'pending' ? (
                        <div className="table-actions-cell">
                          <button 
                            type="button" 
                            className="btn-action-approve"
                            onClick={() => handleApprove(req.id)}
                          >
                            Duyệt
                          </button>
                          <button 
                            type="button" 
                            className="btn-action-reject"
                            onClick={() => handleReject(req.id)}
                          >
                            Từ chối
                          </button>
                        </div>
                      ) : (
                        <span className="table-auto-text">
                          {req.status === 'approved' ? 'Thành công' : req.status === 'rejected' ? 'Đã hủy' : 'Tự động hoàn tất'}
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right: Nhật ký kiểm toán */}
        <div className="admin-panel audit-panel">
          <div className="admin-panel-header">
            <h2 className="admin-panel-title">Nhật ký kiểm toán</h2>
            <Shield size={19} className="audit-shield-icon" />
          </div>

          <div className="audit-timeline-list">
            {/* Audit Item 1 */}
            <div className="audit-item">
              <div className="audit-icon-circle red">
                <AlertTriangle size={16} />
              </div>
              <div className="audit-details">
                <h4 className="audit-item-title">5 lần đăng nhập thất bại liên tiếp</h4>
                <p className="audit-item-desc">
                  IP: 118.70.12.91 đã bị tạm khóa bảo mật 30 phút
                </p>
                <span className="audit-item-time red">10 phút trước</span>
              </div>
            </div>

            {/* Audit Item 2 */}
            <div className="audit-item">
              <div className="audit-icon-circle purple">
                <Users size={16} />
              </div>
              <div className="audit-details">
                <h4 className="audit-item-title">Cập nhật phân quyền Ban Giám Hiệu</h4>
                <p className="audit-item-desc">
                  Thực hiện bởi: Thầy Hiệu Trưởng (UID: #AD01)
                </p>
                <span className="audit-item-time">45 phút trước</span>
              </div>
            </div>

            {/* Audit Item 3 */}
            <div className="audit-item">
              <div className="audit-icon-circle green">
                <Cloud size={16} />
              </div>
              <div className="audit-details">
                <h4 className="audit-item-title">Backup dữ liệu tự động hoàn tất</h4>
                <p className="audit-item-desc">
                  Bản snapshot lưu trữ dung lượng 8.2 GB
                </p>
                <span className="audit-item-time">02:00 Sáng hôm nay</span>
              </div>
            </div>
          </div>

          <button 
            type="button" 
            className="audit-view-all-btn"
            onClick={() => setShowAuditModal(true)}
          >
            <span>Xem toàn bộ nhật ký kiểm toán</span>
            <ChevronRight size={17} />
          </button>
        </div>
      </section>

      {/* MODAL: + Tạo tài khoản mới */}
      {showCreateUserModal && (
        <div className="admin-modal-backdrop" onClick={() => setShowCreateUserModal(false)}>
          <div className="admin-modal-card" onClick={e => e.stopPropagation()}>
            <div className="admin-modal-header">
              <h3 className="admin-modal-title">Tạo tài khoản người dùng mới</h3>
              <button 
                type="button" 
                className="admin-modal-close" 
                onClick={() => setShowCreateUserModal(false)}
              >
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleCreateUserSubmit} className="admin-modal-body">
              <div className="admin-form-group">
                <label className="admin-form-label">Họ và tên *</label>
                <input 
                  type="text" 
                  className="admin-form-input" 
                  placeholder="Ví dụ: ThS. Lê Văn Bình" 
                  value={newUser.fullName}
                  onChange={e => setNewUser(p => ({ ...p, fullName: e.target.value }))}
                  required 
                />
              </div>

              <div className="admin-form-group">
                <label className="admin-form-label">Email trường *</label>
                <input 
                  type="email" 
                  className="admin-form-input" 
                  placeholder="binhle@school.com" 
                  value={newUser.email}
                  onChange={e => setNewUser(p => ({ ...p, email: e.target.value }))}
                  required 
                />
              </div>

              <div className="admin-form-group">
                <label className="admin-form-label">Số điện thoại</label>
                <input 
                  type="text" 
                  className="admin-form-input" 
                  placeholder="0912345678" 
                  value={newUser.phone}
                  onChange={e => setNewUser(p => ({ ...p, phone: e.target.value }))}
                />
              </div>

              <div className="admin-form-row">
                <div className="admin-form-group flex-1">
                  <label className="admin-form-label">Vai trò</label>
                  <select 
                    className="admin-form-select"
                    value={newUser.role}
                    onChange={e => setNewUser(p => ({ ...p, role: e.target.value }))}
                  >
                    <option value="Teacher">Giáo viên (Teacher)</option>
                    <option value="HomeroomTeacher">Giáo viên chủ nhiệm (GVCN)</option>
                    <option value="Student">Học sinh (Student)</option>
                    <option value="Admin">Quản trị viên (Admin)</option>
                  </select>
                </div>

                <div className="admin-form-group flex-1">
                  <label className="admin-form-label">Bộ môn / Khối</label>
                  <select 
                    className="admin-form-select"
                    value={newUser.department}
                    onChange={e => setNewUser(p => ({ ...p, department: e.target.value }))}
                  >
                    <option value="Toán học">Tổ Toán học</option>
                    <option value="Vật lý">Tổ Vật lý</option>
                    <option value="Hóa học">Tổ Hóa học</option>
                    <option value="Ngữ văn">Tổ Ngữ văn</option>
                    <option value="Tin học">Tổ Tin học</option>
                    <option value="Tiếng Anh">Tổ Tiếng Anh</option>
                  </select>
                </div>
              </div>

              <div className="admin-modal-footer">
                <button 
                  type="button" 
                  className="admin-btn-cancel" 
                  onClick={() => setShowCreateUserModal(false)}
                >
                  Hủy bỏ
                </button>
                <button type="submit" className="admin-btn-primary">
                  Tạo tài khoản
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: Xuất báo cáo tổng hợp */}
      {showExportModal && (
        <div className="admin-modal-backdrop" onClick={() => setShowExportModal(false)}>
          <div className="admin-modal-card" onClick={e => e.stopPropagation()}>
            <div className="admin-modal-header">
              <h3 className="admin-modal-title">Xuất báo cáo tổng hợp hệ thống</h3>
              <button 
                type="button" 
                className="admin-modal-close" 
                onClick={() => setShowExportModal(false)}
              >
                <X size={20} />
              </button>
            </div>
            <div className="admin-modal-body">
              <p className="admin-modal-desc">
                Chọn định dạng và kỳ báo cáo để tải xuống tập tin thống kê toàn diện hoạt động của LMS.
              </p>

              <div className="admin-form-group">
                <label className="admin-form-label">Định dạng tập tin</label>
                <div className="export-options-row">
                  <label className="export-option-box">
                    <input type="radio" name="exportFormat" defaultChecked />
                    <span>PDF Document (.pdf)</span>
                  </label>
                  <label className="export-option-box">
                    <input type="radio" name="exportFormat" />
                    <span>Bảng tính Excel (.xlsx)</span>
                  </label>
                </div>
              </div>

              <div className="admin-form-group">
                <label className="admin-form-label">Kỳ thống kê</label>
                <select className="admin-form-select">
                  <option>Học kỳ II (Năm học 2024 - 2025)</option>
                  <option>Tháng hiện tại (Tháng 09/2026)</option>
                  <option>Tuần này</option>
                </select>
              </div>

              <div className="admin-modal-footer">
                <button 
                  type="button" 
                  className="admin-btn-cancel" 
                  onClick={() => setShowExportModal(false)}
                >
                  Đóng
                </button>
                <button 
                  type="button" 
                  className="admin-btn-primary"
                  onClick={() => {
                    setShowExportModal(false);
                    showToast('Đang tạo và tải xuống tập tin báo cáo tổng hợp...');
                  }}
                >
                  <Download size={16} />
                  <span>Tải xuống báo cáo</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* MODAL: Xem toàn bộ nhật ký kiểm toán */}
      {showAuditModal && (
        <div className="admin-modal-backdrop" onClick={() => setShowAuditModal(false)}>
          <div className="admin-modal-card modal-lg" onClick={e => e.stopPropagation()}>
            <div className="admin-modal-header">
              <h3 className="admin-modal-title">Toàn bộ nhật ký kiểm toán hệ thống</h3>
              <button 
                type="button" 
                className="admin-modal-close" 
                onClick={() => setShowAuditModal(false)}
              >
                <X size={20} />
              </button>
            </div>
            <div className="admin-modal-body">
              <div className="audit-full-list">
                <div className="audit-item">
                  <div className="audit-icon-circle red">
                    <AlertTriangle size={16} />
                  </div>
                  <div className="audit-details">
                    <h4 className="audit-item-title">5 lần đăng nhập thất bại liên tiếp</h4>
                    <p className="audit-item-desc">IP: 118.70.12.91 đã bị tạm khóa bảo mật 30 phút do vượt quá số lần xác thực</p>
                    <span className="audit-item-time red">10 phút trước • Module: Auth & Security</span>
                  </div>
                </div>

                <div className="audit-item">
                  <div className="audit-icon-circle purple">
                    <Users size={16} />
                  </div>
                  <div className="audit-details">
                    <h4 className="audit-item-title">Cập nhật phân quyền Ban Giám Hiệu</h4>
                    <p className="audit-item-desc">Thực hiện bởi: Thầy Hiệu Trưởng (UID: #AD01) • Cấp quyền duyệt giáo án toàn trường</p>
                    <span className="audit-item-time">45 phút trước • Module: RBAC</span>
                  </div>
                </div>

                <div className="audit-item">
                  <div className="audit-icon-circle green">
                    <Cloud size={16} />
                  </div>
                  <div className="audit-details">
                    <h4 className="audit-item-title">Backup dữ liệu tự động hoàn tất</h4>
                    <p className="audit-item-desc">Bản snapshot lưu trữ dung lượng 8.2 GB đã được đồng bộ lên AWS S3 Cold Storage</p>
                    <span className="audit-item-time">02:00 Sáng hôm nay • Module: Automated Backup</span>
                  </div>
                </div>

                <div className="audit-item">
                  <div className="audit-icon-circle purple">
                    <Shield size={16} />
                  </div>
                  <div className="audit-details">
                    <h4 className="audit-item-title">Gia hạn thành công chứng chỉ SSL Wildcard</h4>
                    <p className="audit-item-desc">Tự động gia hạn bởi Let's Encrypt bot cho domain *.school.edu.vn (thời hạn 90 ngày)</p>
                    <span className="audit-item-time">Hôm qua • Module: Infrastructure</span>
                  </div>
                </div>
              </div>

              <div className="admin-modal-footer">
                <button 
                  type="button" 
                  className="admin-btn-cancel" 
                  onClick={() => setShowAuditModal(false)}
                >
                  Đóng
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
