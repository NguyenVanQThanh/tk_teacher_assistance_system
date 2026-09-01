// File Name: TeacherGradingPage.jsx
// Description: Teacher Grading & Feedback management page with submission metrics, multi-criteria filtering, submission roster table, and interactive grading modal.
// Created At: 2026-09-01
// Created By: Tam Khang
// Updated At: 2026-09-01
// Updated By: Tam Khang

import React, { useState, useMemo } from 'react';
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
  Check
} from 'lucide-react';
import Header from '../../components/common/Header';
import TeacherSidebar from '../../components/teacher/TeacherSidebar';
import GradingFeedbackModal from '../../components/teacher/GradingFeedbackModal';
import './TeacherGradingPage.css';

export default function TeacherGradingPage() {
  const [showSidebar, setShowSidebar] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [gradeFilter, setGradeFilter] = useState('all');
  const [subjectFilter, setSubjectFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 8;

  // Selected submission for grading modal
  const [gradingSubmission, setGradingSubmission] = useState(null);
  const [toastMessage, setToastMessage] = useState(null);

  // Submissions dataset with 3 official statuses: pending_grading (Chờ chấm), pending_review (Chờ duyệt), approved (Đã duyệt)
  const [submissions, setSubmissions] = useState([
    {
      id: 1,
      studentName: 'Trần Thị Lan',
      avatarInitial: 'TL',
      avatarColor: '#8B5CF6',
      className: '10A1',
      grade: '10',
      subject: 'math',
      exerciseTitle: 'Kiểm tra 15p - Đạo hàm',
      exerciseType: 'Bài tập trên lớp',
      exerciseTypeCode: 'classroom',
      submittedTime: 'Hôm nay, 08:30',
      timeType: 'normal',
      status: 'pending_grading',
      statusLabel: 'Chờ chấm',
      score: null,
      feedback: ''
    },
    {
      id: 2,
      studentName: 'Phạm Thu Thảo',
      avatarInitial: 'TT',
      avatarColor: '#6366F1',
      className: '12A1',
      grade: '12',
      subject: 'math',
      exerciseTitle: 'Khảo sát hàm số nâng cao',
      exerciseType: 'Bài tập trên lớp',
      exerciseTypeCode: 'classroom',
      submittedTime: 'Hôm nay, 09:15',
      timeType: 'normal',
      status: 'pending_grading',
      statusLabel: 'Chờ chấm',
      score: null,
      feedback: ''
    },
    {
      id: 3,
      studentName: 'Hoàng Yến Nhi',
      avatarInitial: 'YN',
      avatarColor: '#EC4899',
      className: '11A3',
      grade: '11',
      subject: 'physics',
      exerciseTitle: 'Kiểm tra 45p - Sóng ánh sáng',
      exerciseType: 'Bài tập trên lớp',
      exerciseTypeCode: 'classroom',
      submittedTime: 'Hôm qua, 22:30',
      timeType: 'late',
      status: 'pending_grading',
      statusLabel: 'Chờ chấm',
      score: null,
      feedback: ''
    },
    {
      id: 4,
      studentName: 'Bùi Quốc Anh',
      avatarInitial: 'QA',
      avatarColor: '#3B82F6',
      className: '10A2',
      grade: '10',
      subject: 'physics',
      exerciseTitle: 'Bài tập Thuyết electron & Điện tích',
      exerciseType: 'Bài tập trên lớp',
      exerciseTypeCode: 'classroom',
      submittedTime: 'Hôm nay, 10:05',
      timeType: 'normal',
      status: 'pending_grading',
      statusLabel: 'Chờ chấm',
      score: null,
      feedback: ''
    },
    {
      id: 5,
      studentName: 'Lê Gia Hưng',
      avatarInitial: 'GH',
      avatarColor: '#10B981',
      className: '11B1',
      grade: '11',
      subject: 'chemistry',
      exerciseTitle: 'Bài tập Ancol - Phenol',
      exerciseType: 'Bài tập trên lớp',
      exerciseTypeCode: 'classroom',
      submittedTime: 'Hôm nay, 10:45',
      timeType: 'normal',
      status: 'pending_grading',
      statusLabel: 'Chờ chấm',
      score: null,
      feedback: ''
    },
    {
      id: 6,
      studentName: 'Đỗ Minh Trí',
      avatarInitial: 'MT',
      avatarColor: '#F59E0B',
      className: '12A2',
      grade: '12',
      subject: 'chemistry',
      exerciseTitle: 'Đề kiểm tra Este Lipit nâng cao',
      exerciseType: 'Bài tập trên lớp',
      exerciseTypeCode: 'classroom',
      submittedTime: 'Hôm qua, 21:10',
      timeType: 'normal',
      status: 'pending_grading',
      statusLabel: 'Chờ chấm',
      score: null,
      feedback: ''
    },
    {
      id: 7,
      studentName: 'Võ Thùy Trang',
      avatarInitial: 'TT',
      avatarColor: '#8B5CF6',
      className: '10A3',
      grade: '10',
      subject: 'literature',
      exerciseTitle: 'Phân tích văn bản Tấm Cám',
      exerciseType: 'Bài tập trên lớp',
      exerciseTypeCode: 'classroom',
      submittedTime: 'Hôm qua, 18:20',
      timeType: 'normal',
      status: 'pending_grading',
      statusLabel: 'Chờ chấm',
      score: null,
      feedback: ''
    },
    {
      id: 8,
      studentName: 'Trịnh Hoàng Long',
      avatarInitial: 'HL',
      avatarColor: '#06B6D4',
      className: '11A1',
      grade: '11',
      subject: 'literature',
      exerciseTitle: 'Nghị luận xã hội: Tư duy tự học',
      exerciseType: 'Bài tập trên lớp',
      exerciseTypeCode: 'classroom',
      submittedTime: 'Hôm nay, 07:50',
      timeType: 'normal',
      status: 'pending_grading',
      statusLabel: 'Chờ chấm',
      score: null,
      feedback: ''
    },
    {
      id: 9,
      studentName: 'Dương Thanh Hà',
      avatarInitial: 'TH',
      avatarColor: '#EC4899',
      className: '12A3',
      grade: '12',
      subject: 'english',
      exerciseTitle: 'Ôn tập Unit 4: Urbanisation',
      exerciseType: 'Bài tập trên lớp',
      exerciseTypeCode: 'classroom',
      submittedTime: 'Hôm qua, 23:45',
      timeType: 'late',
      status: 'pending_grading',
      statusLabel: 'Chờ chấm',
      score: null,
      feedback: ''
    },
    {
      id: 10,
      studentName: 'Nguyễn Hải Yến',
      avatarInitial: 'HY',
      avatarColor: '#14B8A6',
      className: '10A1',
      grade: '10',
      subject: 'english',
      exerciseTitle: 'Progress Test: Tenses & Modals',
      exerciseType: 'Bài tập trên lớp',
      exerciseTypeCode: 'classroom',
      submittedTime: 'Hôm nay, 11:00',
      timeType: 'normal',
      status: 'pending_grading',
      statusLabel: 'Chờ chấm',
      score: null,
      feedback: ''
    },
    {
      id: 11,
      studentName: 'Phan Minh Khang',
      avatarInitial: 'MK',
      avatarColor: '#6366F1',
      className: '11B2',
      grade: '11',
      subject: 'physics',
      exerciseTitle: 'Bài tập Định luật Vạn vật Hấp dẫn',
      exerciseType: 'Bài tập trên lớp',
      exerciseTypeCode: 'classroom',
      submittedTime: 'Hôm nay, 11:30',
      timeType: 'normal',
      status: 'pending_grading',
      statusLabel: 'Chờ chấm',
      score: null,
      feedback: ''
    },
    {
      id: 12,
      studentName: 'Trương Bảo Ngọc',
      avatarInitial: 'BN',
      avatarColor: '#A855F7',
      className: '12A1',
      grade: '12',
      subject: 'math',
      exerciseTitle: 'Phương trình Logarit chứa tham số m',
      exerciseType: 'Bài tập trên lớp',
      exerciseTypeCode: 'classroom',
      submittedTime: 'Hôm nay, 11:45',
      timeType: 'normal',
      status: 'pending_grading',
      statusLabel: 'Chờ chấm',
      score: null,
      feedback: ''
    },
    {
      id: 13,
      studentName: 'Nguyễn Minh Hải',
      avatarInitial: 'MH',
      avatarColor: '#A855F7',
      className: '11B2',
      grade: '11',
      subject: 'math',
      exerciseTitle: 'Luyện tập AI - Tích phân',
      exerciseType: 'Tạo sinh',
      exerciseTypeCode: 'ai',
      submittedTime: 'Hôm qua, 23:15',
      timeType: 'normal',
      status: 'pending_review',
      statusLabel: 'Chờ duyệt',
      score: 8.5,
      feedback: ''
    },
    {
      id: 14,
      studentName: 'Đặng Quốc Huy',
      avatarInitial: 'QH',
      avatarColor: '#10B981',
      className: '12A1',
      grade: '12',
      subject: 'chemistry',
      exerciseTitle: 'Luyện tập AI - Este Lipit',
      exerciseType: 'Tạo sinh',
      exerciseTypeCode: 'ai',
      submittedTime: 'Hôm nay, 11:20',
      timeType: 'normal',
      status: 'pending_review',
      statusLabel: 'Chờ duyệt',
      score: 8.0,
      feedback: ''
    },
    {
      id: 15,
      studentName: 'Cao Tuấn Kiệt',
      avatarInitial: 'TK',
      avatarColor: '#3B82F6',
      className: '10A2',
      grade: '10',
      subject: 'physics',
      exerciseTitle: 'Luyện tập AI - Khúc xạ ánh sáng',
      exerciseType: 'Tạo sinh',
      exerciseTypeCode: 'ai',
      submittedTime: 'Hôm nay, 08:15',
      timeType: 'normal',
      status: 'pending_review',
      statusLabel: 'Chờ duyệt',
      score: 9.0,
      feedback: ''
    },
    {
      id: 16,
      studentName: 'Lâm Khánh Linh',
      avatarInitial: 'KL',
      avatarColor: '#EC4899',
      className: '11A1',
      grade: '11',
      subject: 'english',
      exerciseTitle: 'Luyện tập AI - Conditional Sentences',
      exerciseType: 'Tạo sinh',
      exerciseTypeCode: 'ai',
      submittedTime: 'Hôm nay, 09:40',
      timeType: 'normal',
      status: 'pending_review',
      statusLabel: 'Chờ duyệt',
      score: 8.5,
      feedback: ''
    },
    {
      id: 17,
      studentName: 'Hồ Văn Tuấn',
      avatarInitial: 'VT',
      avatarColor: '#F59E0B',
      className: '12A2',
      grade: '12',
      subject: 'math',
      exerciseTitle: 'Luyện tập AI - Tọa độ không gian Oxyz',
      exerciseType: 'Tạo sinh',
      exerciseTypeCode: 'ai',
      submittedTime: 'Hôm nay, 10:10',
      timeType: 'normal',
      status: 'pending_review',
      statusLabel: 'Chờ duyệt',
      score: 7.5,
      feedback: ''
    },
    {
      id: 18,
      studentName: 'Lê Phương Duy',
      avatarInitial: 'PD',
      avatarColor: '#94A3B8',
      className: '10A1',
      grade: '10',
      subject: 'math',
      exerciseTitle: 'Bài tập Hình học Không gian',
      exerciseType: 'Bài tập trên lớp',
      exerciseTypeCode: 'classroom',
      submittedTime: '12/05/2023, 14:20',
      timeType: 'graded',
      status: 'approved',
      statusLabel: 'Đã duyệt',
      score: 8.5,
      feedback: 'Làm bài tốt, hình vẽ rõ ràng và lập luận chuẩn xác.'
    },
    {
      id: 19,
      studentName: 'Vũ Đức Nam',
      avatarInitial: 'DN',
      avatarColor: '#3B82F6',
      className: '10A2',
      grade: '10',
      subject: 'math',
      exerciseTitle: 'Luyện tập AI - Tổ hợp xác suất',
      exerciseType: 'Tạo sinh',
      exerciseTypeCode: 'ai',
      submittedTime: 'Hôm qua, 20:45',
      timeType: 'graded',
      status: 'approved',
      statusLabel: 'Đã duyệt',
      score: 9.0,
      feedback: 'Lời giải ngắn gọn, kết quả chính xác 100%.'
    },
    {
      id: 20,
      studentName: 'Nguyễn Bích Ngọc',
      avatarInitial: 'BN',
      avatarColor: '#F59E0B',
      className: '10A1',
      grade: '10',
      subject: 'literature',
      exerciseTitle: 'Đọc hiểu Văn bản Thơ',
      exerciseType: 'Bài tập trên lớp',
      exerciseTypeCode: 'classroom',
      submittedTime: 'Hôm qua, 16:30',
      timeType: 'graded',
      status: 'approved',
      statusLabel: 'Đã duyệt',
      score: 8.0,
      feedback: 'Cảm thụ tốt, lời văn trau chuốt.'
    }
  ]);

  // Handle grade/approval saved from modal (transitions to 'approved' and supports cascade batch regrade)
  const handleSaveGrade = (updatedSubmission) => {
    setSubmissions((prev) =>
      prev.map((item) => {
        if (item.id === updatedSubmission.id) {
          return {
            ...updatedSubmission,
            status: 'approved',
            statusLabel: 'Đã duyệt'
          };
        }
        // If cascade regrade is requested and another submission belongs to the same exercise
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
    setTimeout(() => setToastMessage(null), 4000);
  };

  // Handle save and automatically jump to the next pending submission
  const handleSaveAndNext = (updatedSubmission) => {
    setSubmissions((prev) => {
      const nextSubmissions = prev.map((item) => {
        if (item.id === updatedSubmission.id) {
          return {
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
        (s) => (s.status === 'pending_grading' || s.status === 'pending_review') && s.id !== updatedSubmission.id
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
    return submissions.filter((s) => s.status === 'pending_grading').length;
  }, [submissions]);

  const pendingReviewCount = useMemo(() => {
    return submissions.filter((s) => s.status === 'pending_review').length;
  }, [submissions]);

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
    setToastMessage('Đang xuất file báo cáo chấm điểm (Excel/PDF)...');
    setTimeout(() => {
      setToastMessage('Xuất báo cáo thành công!');
      setTimeout(() => setToastMessage(null), 3000);
    }, 1000);
  };

  return (
    <div className="teacher-grading-layout">
      {/* Top Header */}
      <Header onToggleSidebar={() => setShowSidebar(!showSidebar)} />

      <div className="grading-main-container">
        {/* Sidebar */}
        {showSidebar && (
          <TeacherSidebar 
            activeNav="grading" 
            createButtonText="Tạo lớp học mới"
          />
        )}

        {/* Content Area */}
        <main className="grading-content-area">
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
        </main>
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
