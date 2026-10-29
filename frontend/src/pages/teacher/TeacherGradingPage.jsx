// File Name: TeacherGradingPage.jsx
// Description: Teacher Grading & Feedback management page with submission metrics, multi-criteria filtering, submission roster table, and interactive grading modal.
// Created At: 2026-09-01
// Created By: Tam Khang
// Updated At: 2026-10-29
// Updated By: Tam Khang

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { 
  ChevronRight, 
  Search, 
  Download, 
  Inbox, 
  FileText, 
  CheckCircle2, 
  Clock, 
  AlertTriangle, 
  Edit3, 
  ChevronLeft, 
  ChevronDown, 
  Sparkles,
  FileSpreadsheet,
  Check,
  Loader2
} from 'lucide-react';
import { useSearchParams } from 'react-router-dom';
import GradingFeedbackModal from '../../components/teacher/GradingFeedbackModal';
import { attemptsApi, classesApi, subjectsApi } from '../../services/api';
import './TeacherGradingPage.css';

export default function TeacherGradingPage() {
  const [searchParams] = useSearchParams();
  const [showSidebar, setShowSidebar] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [gradeFilter, setGradeFilter] = useState('all');
  const [subjectFilter, setSubjectFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState(searchParams.get('status') || 'all');
  const [typeFilter, setTypeFilter] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 8;

  // Selected submission for grading modal
  const [gradingSubmission, setGradingSubmission] = useState(null);
  const [toastMessage, setToastMessage] = useState(null);
  const [loading, setLoading] = useState(true);
  const [classesList, setClassesList] = useState([]);
  const [subjectsList, setSubjectsList] = useState([]);
  const [dashboardStats, setDashboardStats] = useState(null);

  // Submissions dataset populated from real backend API
  const [submissions, setSubmissions] = useState([]);

  useEffect(() => {
    const s = searchParams.get('status');
    if (s) {
      setStatusFilter(s);
    }
  }, [searchParams]);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [attemptsRes, classesRes, subjectsRes, dashboardRes] = await Promise.allSettled([
        attemptsApi.getAttempts(),
        classesApi.getClasses(),
        subjectsApi.getSubjects(),
        attemptsApi.getGradingDashboard(),
      ]);

      if (dashboardRes.status === 'fulfilled' && dashboardRes.value) {
        setDashboardStats(dashboardRes.value);
      }

      if (classesRes.status === 'fulfilled') {
        setClassesList(Array.isArray(classesRes.value) ? classesRes.value : classesRes.value.items || []);
      }

      if (subjectsRes.status === 'fulfilled') {
        setSubjectsList(Array.isArray(subjectsRes.value) ? subjectsRes.value : subjectsRes.value.items || []);
      }

      if (attemptsRes.status === 'fulfilled') {
        const rawItems = Array.isArray(attemptsRes.value) ? attemptsRes.value : (attemptsRes.value?.items || []);
        const mapped = rawItems.map((att, idx) => {
          const rawScore = att.score;
          const hasScore = rawScore !== null && rawScore !== undefined;
          const gradeMatch = att.class_name ? att.class_name.match(/(10|11|12)/) : null;
          const grade = gradeMatch ? gradeMatch[1] : '12';

          let subjKey = 'math';
          if (att.subject_name) {
            const sn = att.subject_name.toLowerCase();
            if (sn.includes('vật') || sn.includes('lý')) subjKey = 'physics';
            else if (sn.includes('hóa')) subjKey = 'chemistry';
            else if (sn.includes('anh')) subjKey = 'english';
          }

          const colors = ['#8B5CF6', '#6366F1', '#EC4899', '#3B82F6', '#10B981', '#F59E0B'];
          const avatarColor = colors[idx % colors.length];
          const nameParts = (att.student_name || 'Học sinh').trim().split(' ');
          const avatarInitial = nameParts.length >= 2 ? (nameParts[0][0] + nameParts[nameParts.length - 1][0]).toUpperCase() : nameParts[0].slice(0, 2).toUpperCase();

          const submittedFormatted = att.end_time
            ? new Date(att.end_time).toLocaleDateString('vi-VN', { hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit' })
            : (att.start_time ? new Date(att.start_time).toLocaleDateString('vi-VN', { hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit' }) : 'Vừa xong');

          const itemStatus = (att.status === 'pending_grading' || att.status === 'pending_review' || att.status === 'approved')
            ? att.status
            : (hasScore ? 'approved' : 'pending_grading');
          const itemStatusLabel = itemStatus === 'pending_grading'
            ? 'Chờ chấm'
            : (itemStatus === 'pending_review' ? 'Chờ duyệt' : 'Đã duyệt');

          return {
            id: att.attempt_id,
            attempt_id: att.attempt_id,
            assignment_id: att.assignment_id,
            exercise_id: att.exercise_id,
            student_id: att.student_id,
            studentName: att.student_name || 'Học sinh',
            avatarInitial,
            avatarColor,
            className: att.class_name || '12A1',
            class_id: att.class_id,
            grade,
            subject: subjKey,
            subjectName: att.subject_name || 'Toán học',
            exerciseTitle: att.exercise_title || att.assignment_title || 'Bài tập trực tuyến',
            exerciseType: 'Bài tập trực tuyến',
            exerciseTypeCode: 'classroom',
            submittedTime: submittedFormatted,
            timeType: 'normal',
            status: itemStatus,
            statusLabel: itemStatusLabel,
            score: hasScore ? Number(rawScore) : null,
            feedback: '',
            raw: att
          };
        });
        setSubmissions(mapped);
      }
    } catch (err) {
      console.error('Failed to load grading data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Handle grade/approval saved from modal (transitions to 'approved' and supports cascade batch regrade)
  const handleSaveGrade = async (updatedSubmission) => {
    try {
      if (updatedSubmission.attempt_id) {
        await attemptsApi.updateGrade(updatedSubmission.attempt_id, {
          score: updatedSubmission.score !== null ? updatedSubmission.score : 0,
          feedback: updatedSubmission.feedback || '',
        });
      }

      setSubmissions((prev) =>
        prev.map((item) => {
          if (item.id === updatedSubmission.id || (item.attempt_id && item.attempt_id === updatedSubmission.attempt_id)) {
            return {
              ...item,
              ...updatedSubmission,
              status: 'approved',
              statusLabel: 'Đã duyệt'
            };
          }
          if (updatedSubmission.cascadeRegrade && item.exerciseTitle === updatedSubmission.exerciseTitle) {
            return {
              ...item,
              score: updatedSubmission.score !== null ? updatedSubmission.score : item.score,
              status: 'approved',
              statusLabel: 'Đã duyệt'
            };
          }
          return item;
        })
      );

      if (updatedSubmission.cascadeRegrade) {
        setToastMessage(`Đã lưu đáp án mới và tự động cập nhật điểm số cho tất cả bài làm của đề "${updatedSubmission.exerciseTitle}".`);
      } else {
        setToastMessage(`Đã hoàn tất chấm điểm bài nộp của học sinh ${updatedSubmission.studentName} (${updatedSubmission.score} điểm).`);
      }
    } catch (err) {
      setToastMessage('Không thể lưu điểm trên máy chủ. Đã lưu tạm bộ nhớ.');
    }
    setTimeout(() => setToastMessage(null), 4000);
  };

  // Handle save and automatically jump to the next pending submission
  const handleSaveAndNext = async (updatedSubmission) => {
    try {
      if (updatedSubmission.attempt_id) {
        await attemptsApi.updateGrade(updatedSubmission.attempt_id, {
          score: updatedSubmission.score !== null ? updatedSubmission.score : 0,
          feedback: updatedSubmission.feedback || '',
        });
      }
    } catch (err) {
      console.error(err);
    }

    setSubmissions((prev) => {
      const nextSubmissions = prev.map((item) => {
        if (item.id === updatedSubmission.id || (item.attempt_id && item.attempt_id === updatedSubmission.attempt_id)) {
          return {
            ...item,
            ...updatedSubmission,
            status: 'approved',
            statusLabel: 'Đã duyệt'
          };
        }
        if (updatedSubmission.cascadeRegrade && item.exerciseTitle === updatedSubmission.exerciseTitle) {
          return {
            ...item,
            score: updatedSubmission.score !== null ? updatedSubmission.score : item.score,
            status: 'approved',
            statusLabel: 'Đã duyệt'
          };
        }
        return item;
      });

      const remainingPending = nextSubmissions.filter(
        (s) => (s.status === 'pending_grading' || s.status === 'pending_review') && s.id !== updatedSubmission.id && s.attempt_id !== updatedSubmission.attempt_id
      );
      if (remainingPending.length > 0) {
        setGradingSubmission(remainingPending[0]);
        setToastMessage(`Đã duyệt bài của ${updatedSubmission.studentName}. Chuyển sang bài tiếp theo của ${remainingPending[0].studentName}...`);
      } else {
        setGradingSubmission(null);
        setToastMessage(`Đã hoàn tất duyệt & chấm toàn bộ danh sách bài nộp!`);
      }
      return nextSubmissions;
    });
    setTimeout(() => setToastMessage(null), 3500);
  };

  // Quick grade/review trigger from cards
  const handleQuickGrade = (targetStatus = 'pending_grading') => {
    setStatusFilter(targetStatus);
    const candidates = submissions.filter((s) => s.status === targetStatus);
    if (candidates.length > 0) {
      setGradingSubmission(candidates[0]);
    } else {
      setToastMessage(targetStatus === 'pending_grading' ? 'Không còn bài chờ chấm!' : 'Không còn bài chờ duyệt!');
      setTimeout(() => setToastMessage(null), 3000);
    }
  };

  // Dynamic counts: exact real-time counts from submissions
  const pendingGradingCount = useMemo(() => {
    if (submissions && submissions.length > 0) {
      return submissions.filter((s) => s.status === 'pending_grading').length;
    }
    return dashboardStats?.pending_grading_count ?? 0;
  }, [dashboardStats, submissions]);

  const pendingReviewCount = useMemo(() => {
    if (submissions && submissions.length > 0) {
      return submissions.filter((s) => s.status === 'pending_review').length;
    }
    return dashboardStats?.pending_review_count ?? 0;
  }, [dashboardStats, submissions]);

  // Filter logic
  const filteredSubmissions = useMemo(() => {
    return submissions.filter((item) => {
      // Search query filter
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase();
        const matchName = item.studentName.toLowerCase().includes(query);
        const matchClass = item.className.toLowerCase().includes(query);
        const matchExercise = item.exerciseTitle.toLowerCase().includes(query);
        if (!matchName && !matchClass && !matchExercise) return false;
      }

      // Grade filter
      if (gradeFilter !== 'all' && item.grade !== gradeFilter) {
        return false;
      }

      // Subject filter
      if (subjectFilter !== 'all' && item.subject !== subjectFilter) {
        return false;
      }

      // Status filter
      if (statusFilter !== 'all') {
        if (statusFilter === 'pending_grading' && item.status !== 'pending_grading') return false;
        if (statusFilter === 'pending_review' && item.status !== 'pending_review') return false;
        if (statusFilter === 'approved' && item.status !== 'approved') return false;
      }

      // Type filter
      if (typeFilter !== 'all') {
        if (typeFilter === 'classroom' && item.exerciseTypeCode !== 'classroom') return false;
        if (typeFilter === 'ai' && item.exerciseTypeCode !== 'ai') return false;
      }

      return true;
    });
  }, [submissions, searchQuery, gradeFilter, subjectFilter, statusFilter, typeFilter]);

  // Paginated records
  const totalPages = Math.max(1, Math.ceil(filteredSubmissions.length / itemsPerPage));
  const currentRecords = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    return filteredSubmissions.slice(startIndex, startIndex + itemsPerPage);
  }, [filteredSubmissions, currentPage, itemsPerPage]);

  const handleExportReport = () => {
    try {
      const headers = ['Mã bài làm', 'Họ và tên học sinh', 'Lớp', 'Môn học', 'Đề bài', 'Điểm số', 'Trạng thái', 'Nhận xét', 'Thời gian nộp'];
      const rows = filteredSubmissions.map((s) => [
        `"${s.id || s.attempt_id || ''}"`,
        `"${(s.studentName || '').replace(/"/g, '""')}"`,
        `"${(s.className || '').replace(/"/g, '""')}"`,
        `"${(s.subjectName || s.subject || '').replace(/"/g, '""')}"`,
        `"${(s.exerciseTitle || '').replace(/"/g, '""')}"`,
        `"${s.score !== null && s.score !== undefined ? s.score : ''}"`,
        `"${(s.statusLabel || s.status || '').replace(/"/g, '""')}"`,
        `"${(s.feedback || '').replace(/"/g, '""')}"`,
        `"${(s.submittedTime || '').replace(/"/g, '""')}"`
      ]);

      const csvContent = '\uFEFF' + [headers.join(','), ...rows.map(r => r.join(','))].join('\r\n');
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.setAttribute('href', url);
      link.setAttribute('download', `Bang_Diem_Hoc_Sinh_${new Date().toISOString().slice(0, 10)}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      setToastMessage('Đã xuất file bảng điểm (Excel/CSV) thành công!');
    } catch (err) {
      console.error('Export error:', err);
      setToastMessage('Lỗi khi xuất bảng điểm.');
    }
    setTimeout(() => setToastMessage(null), 3500);
  };

  return (
    <div className="grading-content-area">
          {/* Toast Notification */}
          {toastMessage && (
            <div className="grading-toast">
              <CheckCircle2 size={18} />
              <span>{toastMessage}</span>
            </div>
          )}

          {/* Breadcrumb Row */}
          <div className="grading-breadcrumb-row">
            <span className="breadcrumb-link">Trang chủ</span>
            <ChevronRight size={14} className="breadcrumb-arrow" />
            <span className="breadcrumb-current">Chấm điểm & Phản hồi</span>
          </div>

          {/* Page Title & Actions */}
          <div className="grading-header-row">
            <h1 className="grading-page-title">Quản lý Chấm điểm</h1>
            <button 
              type="button" 
              className="btn-export-report"
              onClick={handleExportReport}
            >
              <Download size={16} />
              <span>Xuất báo cáo</span>
            </button>
          </div>

          {/* 3 Redefined Metric Summary Cards as requested */}
          <div className="grading-metrics-grid">
            {/* Khung 1: Chú thích trạng thái */}
            <div className="metric-guide-card">
              <div className="guide-card-header">
                <Inbox size={16} className="text-purple" />
                <span>CHÚ THÍCH TRẠNG THÁI</span>
              </div>

              <div className="guide-items-list">
                <div className="guide-status-item">
                  <span className="status-dot-badge cho-cham">Chờ chấm</span>
                  <span className="guide-desc-text">
                    Câu hỏi chưa có đáp án, khi GV chấm xong sẽ chuyển thành <strong>Đã duyệt</strong>.
                  </span>
                </div>

                <div className="guide-status-item">
                  <span className="status-dot-badge cho-duyet">Chờ duyệt</span>
                  <span className="guide-desc-text">
                    Đã chấm bởi hệ thống, chờ giáo viên duyệt để chuyển sang <strong>Đã duyệt</strong>.
                  </span>
                </div>

                <div className="guide-status-item">
                  <span className="status-dot-badge da-duyet">Đã duyệt</span>
                  <span className="guide-desc-text">
                    Giáo viên đã thông qua và hoàn tất kết quả.
                  </span>
                </div>
              </div>
            </div>

            {/* Khung 2: Khung Chờ chấm */}
            <div 
              className="metric-stat-card border-amber-accent interactive-urgent-card"
              onClick={() => handleQuickGrade('pending_grading')}
              title="Bấm vào đây để lọc và chấm các bài chờ chấm"
            >
              <div className="metric-icon-box amber-box">
                <Clock size={22} color="#D97706" />
              </div>
              <div className="metric-text-content">
                <div className="metric-header-badge-row">
                  <span className="metric-stat-label">CHỜ CHẤM</span>
                  <span className="urgent-badge-action">Chấm ngay ➔</span>
                </div>
                <div className="metric-urgent-row">
                  <span className="metric-stat-number">{pendingGradingCount}</span>
                  <div className="metric-breakdown-subcounts">
                    <span className="subcount-row">
                      Câu hỏi chưa có đáp án
                    </span>
                    <span className="subcount-row text-amber-dark">
                      Cần giáo viên chấm thủ công
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Khung 3: Khung Chờ duyệt */}
            <div 
              className="metric-stat-card border-blue-accent interactive-urgent-card"
              onClick={() => handleQuickGrade('pending_review')}
              title="Bấm vào đây để lọc và duyệt các bài hệ thống đã chấm"
            >
              <div className="metric-icon-box blue-box">
                <Sparkles size={22} color="#2563EB" />
              </div>
              <div className="metric-text-content">
                <div className="metric-header-badge-row">
                  <span className="metric-stat-label">CHỜ DUYỆT</span>
                  <span className="review-badge-action">Duyệt ngay ➔</span>
                </div>
                <div className="metric-urgent-row">
                  <span className="metric-stat-number">{pendingReviewCount}</span>
                  <div className="metric-breakdown-subcounts">
                    <span className="subcount-row">
                      Đã chấm bởi hệ thống
                    </span>
                    <span className="subcount-row text-blue-dark">
                      Chờ giáo viên duyệt kết quả
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Filter Toolbar */}
          <div className="grading-filter-toolbar">
            {/* Grade Filter */}
            <div className="select-container">
              <select 
                className="filter-select"
                value={gradeFilter}
                onChange={(e) => {
                  setGradeFilter(e.target.value);
                  setCurrentPage(1);
                }}
              >
                <option value="all">Khối lớp</option>
                <option value="10">Khối 10</option>
                <option value="11">Khối 11</option>
                <option value="12">Khối 12</option>
              </select>
              <ChevronDown size={14} className="select-arrow" />
            </div>

            {/* Subject Filter */}
            <div className="select-container">
              <select 
                className="filter-select"
                value={subjectFilter}
                onChange={(e) => {
                  setSubjectFilter(e.target.value);
                  setCurrentPage(1);
                }}
              >
                <option value="all">Môn học</option>
                <option value="math">Toán học</option>
                <option value="physics">Vật lý</option>
                <option value="chemistry">Hóa học</option>
                <option value="literature">Ngữ văn</option>
                <option value="english">Tiếng Anh</option>
              </select>
              <ChevronDown size={14} className="select-arrow" />
            </div>

            {/* Status Filter */}
            <div className="select-container">
              <select 
                className="filter-select"
                value={statusFilter}
                onChange={(e) => {
                  setStatusFilter(e.target.value);
                  setCurrentPage(1);
                }}
              >
                <option value="all">Tất cả trạng thái</option>
                <option value="pending_grading">Chờ chấm ({pendingGradingCount})</option>
                <option value="pending_review">Chờ duyệt ({pendingReviewCount})</option>
                <option value="approved">Đã duyệt (128)</option>
              </select>
              <ChevronDown size={14} className="select-arrow" />
            </div>

            {/* Assignment Type Filter */}
            <div className="select-container">
              <select 
                className="filter-select"
                value={typeFilter}
                onChange={(e) => {
                  setTypeFilter(e.target.value);
                  setCurrentPage(1);
                }}
              >
                <option value="all">Tất cả bài tập</option>
                <option value="classroom">Bài tập trên lớp</option>
                <option value="ai">Tạo sinh</option>
              </select>
              <ChevronDown size={14} className="select-arrow" />
            </div>

            {/* Search Input */}
            <div className="search-input-wrapper">
              <Search size={15} className="search-icon" />
              <input 
                type="text" 
                className="search-input-field"
                placeholder="Tìm tên học sinh..."
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setCurrentPage(1);
                }}
              />
            </div>
          </div>

          {/* Submissions Table Card */}
          <div className="submissions-table-card">
            <div className="table-responsive-container">
              <table className="grading-data-table">
                <thead>
                  <tr>
                    <th>HỌC SINH</th>
                    <th>LỚP</th>
                    <th>BÀI TẬP</th>
                    <th>LOẠI BÀI TẬP</th>
                    <th>THỜI GIAN NỘP</th>
                    <th>TRẠNG THÁI</th>
                    <th className="text-center">THAO TÁC</th>
                  </tr>
                </thead>
                <tbody>
                  {currentRecords.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="no-data-cell">
                        Không tìm thấy bài nộp nào phù hợp với bộ lọc.
                      </td>
                    </tr>
                  ) : (
                    currentRecords.map((item) => (
                      <tr key={item.id}>
                        {/* Student Name & Avatar */}
                        <td>
                          <div className="student-row-cell">
                            <div 
                              className="student-avatar-circle"
                              style={{ backgroundColor: item.avatarColor || '#8B5CF6' }}
                            >
                              {item.avatarInitial}
                            </div>
                            <span className="student-name-text">{item.studentName}</span>
                          </div>
                        </td>

                        {/* Class */}
                        <td>
                          <span className="class-name-text">{item.className}</span>
                        </td>

                        {/* Exercise Title */}
                        <td>
                          <span className="exercise-title-text" title={item.exerciseTitle}>
                            {item.exerciseTitle}
                          </span>
                        </td>

                        {/* Exercise Type */}
                        <td>
                          {item.exerciseTypeCode === 'ai' ? (
                            <span className="type-tag-ai">
                              Tạo sinh
                            </span>
                          ) : (
                            <span className="type-tag-classroom">
                              Bài tập trên lớp
                            </span>
                          )}
                        </td>

                        {/* Submitted Time */}
                        <td>
                          {item.timeType === 'late' ? (
                            <span className="time-text late">
                              <AlertTriangle size={14} /> {item.submittedTime}
                            </span>
                          ) : item.timeType === 'graded' || item.status === 'approved' ? (
                            <span className="time-text graded">
                              <Check size={14} /> {item.submittedTime}
                            </span>
                          ) : (
                            <span className="time-text normal">
                              <Clock size={14} /> {item.submittedTime}
                            </span>
                          )}
                        </td>

                        {/* Status Badge */}
                        <td>
                          {item.status === 'pending_grading' && (
                            <span className="status-badge amber">
                              Chờ chấm
                            </span>
                          )}
                          {item.status === 'pending_review' && (
                            <span className="status-badge blue">
                              Chờ duyệt
                            </span>
                          )}
                          {item.status === 'approved' && (
                            <span className="status-badge green">
                              Đã duyệt
                            </span>
                          )}
                        </td>

                        {/* Actions */}
                        <td className="text-center">
                          {item.status === 'approved' ? (
                            <div className="graded-action-box">
                              <span className="score-badge-pill">{item.score}</span>
                              <button 
                                type="button" 
                                className="btn-icon-edit"
                                onClick={() => setGradingSubmission(item)}
                                title="Chỉnh sửa kết quả & điểm số"
                              >
                                <Edit3 size={15} />
                              </button>
                            </div>
                          ) : item.status === 'pending_review' ? (
                            <button 
                              type="button" 
                              className="btn-grade-outline blue"
                              onClick={() => setGradingSubmission(item)}
                              title="Kiểm tra và duyệt kết quả do hệ thống chấm"
                            >
                              <Sparkles size={13} />
                              <span>Duyệt bài</span>
                            </button>
                          ) : (
                            <button 
                              type="button" 
                              className="btn-grade-outline"
                              onClick={() => setGradingSubmission(item)}
                              title="Mở chấm điểm bài tập chưa có đáp án"
                            >
                              Chấm bài
                            </button>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination Footer */}
            <div className="table-pagination-footer">
              <span className="pagination-info-text">
                Hiển thị 1-{Math.min(filteredSubmissions.length, itemsPerPage)} trong số {filteredSubmissions.length} bài nộp
              </span>

              <div className="pagination-controls">
                <button 
                  type="button" 
                  className="page-btn nav-btn"
                  disabled={currentPage === 1}
                  onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                  aria-label="Previous page"
                >
                  <ChevronLeft size={16} />
                </button>

                {Array.from({ length: totalPages }, (_, i) => i + 1).map((pageNum) => (
                  <button
                    key={pageNum}
                    type="button"
                    className={`page-btn ${currentPage === pageNum ? 'active' : ''}`}
                    onClick={() => setCurrentPage(pageNum)}
                  >
                    {pageNum}
                  </button>
                ))}

                <button 
                  type="button" 
                  className="page-btn nav-btn"
                  disabled={currentPage === totalPages}
                  onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                  aria-label="Next page"
                >
                  <ChevronRight size={16} />
                </button>
              </div>
            </div>
          </div>

      {/* Interactive Grading and Feedback Modal */}
      <GradingFeedbackModal
        isOpen={Boolean(gradingSubmission)}
        onClose={() => setGradingSubmission(null)}
        submission={gradingSubmission}
        onSaveGrade={handleSaveGrade}
        hasNextPending={submissions.some(
          (s) => (s.status === 'pending' || s.status === 'late') && s.id !== gradingSubmission?.id
        )}
        onSaveAndNext={handleSaveAndNext}
      />
    </div>
  );
}
