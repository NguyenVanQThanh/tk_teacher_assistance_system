// File Name: TeacherHomeroomPage.jsx
// Description: Homeroom class management page displaying student roster, GPA/subject score filtering, status badges, and export/add student actions.
// Created At: 2026-09-01
// Created By: Tam Khang
// Updated At: 2026-09-01
// Updated By: Tam Khang

import React, { useState, useMemo } from 'react';
import { 
  ChevronRight, 
  Search, 
  Users, 
  Star, 
  Plus, 
  SlidersHorizontal, 
  MoreVertical,
  ChevronDown,
  FileSpreadsheet,
  UserCog,
  FileEdit,
  ArrowUpDown,
  ArrowDown,
  ArrowUp,
  Printer
} from 'lucide-react';
import { Link } from 'react-router-dom';
import Header from '../../components/common/Header';
import TeacherSidebar from '../../components/teacher/TeacherSidebar';
import StudentDetailModal from '../../components/teacher/StudentDetailModal';
import EditStudentInfoModal from '../../components/teacher/EditStudentInfoModal';
import EditStudentGradesModal from '../../components/teacher/EditStudentGradesModal';
import StudentTranscriptPrintModal from '../../components/teacher/StudentTranscriptPrintModal';
import AddStudentModal from '../../components/teacher/AddStudentModal';
import './TeacherHomeroomPage.css';

export default function TeacherHomeroomPage() {
  const [showSidebar, setShowSidebar] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [scoreSortOrder, setScoreSortOrder] = useState('none'); // 'none' | 'desc' (cao -> thấp) | 'asc' (thấp -> cao)
  const [selectedSubject, setSelectedSubject] = useState('all');
  const [showFilterDropdown, setShowFilterDropdown] = useState(false);
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [editingInfoStudent, setEditingInfoStudent] = useState(null);
  const [editingGradesStudent, setEditingGradesStudent] = useState(null);
  const [printingStudent, setPrintingStudent] = useState(null);
  const [showAddStudentModal, setShowAddStudentModal] = useState(false);
  const [activeMenuId, setActiveMenuId] = useState(null);

  // Homeroom class metadata
  const homeroomClass = {
    name: '12A1 - Toán nâng cao',
    roleLabel: 'Lớp chủ nhiệm',
    totalStudents: 45,
    grade: 12,
    term: 'Kì 1, 2023–2024'
  };

  // Subject label dictionary
  const subjectLabels = {
    all: 'TẤT CẢ CÁC MÔN',
    math: 'Toán học',
    physics: 'Vật lý',
    chemistry: 'Hóa học',
    literature: 'Ngữ văn',
    english: 'Tiếng Anh',
    biology: 'Sinh học',
    history: 'Lịch sử',
  };

  // Mock student roster with per-subject scores
  const initialStudentsData = [
    { 
      id: 1, 
      code: 'HS2023001', 
      name: 'Nguyễn Văn A', 
      initials: 'NA', 
      avatarColor: '#7C3AED', 
      avgScore: 8.5, 
      status: 'good', 
      statusLabel: 'Tốt',
      subjectScores: { math: 8.8, physics: 8.5, chemistry: 8.2, literature: 8.0, english: 9.0, biology: 8.4, history: 8.6, informatics: 9.5 }
    },
    { 
      id: 2, 
      code: 'HS2023002', 
      name: 'Trần Thị B', 
      initials: 'TB', 
      avatarColor: '#8B5CF6', 
      avgScore: 9.2, 
      status: 'excellent', 
      statusLabel: 'Xuất sắc',
      subjectScores: { math: 9.6, physics: 9.2, chemistry: 9.0, literature: 8.8, english: 9.5, biology: 9.0, history: 9.3, informatics: 9.8 }
    },
    { 
      id: 3, 
      code: 'HS2023003', 
      name: 'Lê Văn C', 
      initials: 'LC', 
      avatarColor: '#A78BFA', 
      avgScore: 6.8, 
      status: 'fair', 
      statusLabel: 'Khá',
      subjectScores: { math: 7.0, physics: 6.5, chemistry: 6.8, literature: 6.5, english: 7.2, biology: 6.9, history: 6.7, informatics: 7.5 }
    },
    { 
      id: 4, 
      code: 'HS2023004', 
      name: 'Phạm Minh Tuấn', 
      initials: 'PT', 
      avatarColor: '#6366F1', 
      avgScore: 9.5, 
      status: 'excellent', 
      statusLabel: 'Xuất sắc',
      subjectScores: { math: 9.8, physics: 9.5, chemistry: 9.6, literature: 9.0, english: 9.8, biology: 9.2, history: 9.6, informatics: 9.8 }
    },
    { 
      id: 5, 
      code: 'HS2023005', 
      name: 'Đặng Thu Thảo', 
      initials: 'DT', 
      avatarColor: '#EC4899', 
      avgScore: 8.0, 
      status: 'good', 
      statusLabel: 'Tốt',
      subjectScores: { math: 8.2, physics: 8.0, chemistry: 7.8, literature: 8.5, english: 8.2, biology: 7.5, history: 7.8, informatics: 8.6 }
    },
    { 
      id: 6, 
      code: 'HS2023006', 
      name: 'Vũ Hoàng Long', 
      initials: 'VL', 
      avatarColor: '#3B82F6', 
      avgScore: 8.5, 
      status: 'good', 
      statusLabel: 'Tốt',
      subjectScores: { math: 8.6, physics: 8.8, chemistry: 8.4, literature: 7.8, english: 8.8, biology: 8.5, history: 8.6, informatics: 8.8 }
    },
    { 
      id: 7, 
      code: 'HS2023007', 
      name: 'Bùi Phương Linh', 
      initials: 'BL', 
      avatarColor: '#10B981', 
      avgScore: 9.0, 
      status: 'excellent', 
      statusLabel: 'Xuất sắc',
      subjectScores: { math: 9.2, physics: 8.8, chemistry: 9.0, literature: 9.2, english: 9.4, biology: 8.6, history: 8.8, informatics: 9.4 }
    },
    { 
      id: 8, 
      code: 'HS2023008', 
      name: 'Hoàng Quốc Bảo', 
      initials: 'HB', 
      avatarColor: '#F59E0B', 
      avgScore: 7.8, 
      status: 'fair', 
      statusLabel: 'Khá',
      subjectScores: { math: 8.0, physics: 7.8, chemistry: 7.5, literature: 7.6, english: 8.2, biology: 7.8, history: 7.9, informatics: 8.0 }
    },
    { 
      id: 9, 
      code: 'HS2023009', 
      name: 'Ngô Đức Thịnh', 
      initials: 'NT', 
      avatarColor: '#6B7280', 
      avgScore: 8.2, 
      status: 'good', 
      statusLabel: 'Tốt',
      subjectScores: { math: 8.4, physics: 8.0, chemistry: 8.5, literature: 7.9, english: 8.2, biology: 8.3, history: 8.1, informatics: 8.5 }
    },
    { 
      id: 10, 
      code: 'HS2023010', 
      name: 'Đỗ Mai Trang', 
      initials: 'DT', 
      avatarColor: '#8B5CF6', 
      avgScore: 7.2, 
      status: 'fair', 
      statusLabel: 'Khá',
      subjectScores: { math: 7.5, physics: 7.0, chemistry: 7.2, literature: 7.6, english: 7.4, biology: 6.8, history: 6.9, informatics: 7.8 }
    },
  ];

  const [studentsList, setStudentsList] = useState(initialStudentsData);

  const handleSaveStudent = (updatedStudent) => {
    setStudentsList(prev => prev.map(s => s.id === updatedStudent.id ? updatedStudent : s));
    if (selectedStudent && selectedStudent.id === updatedStudent.id) {
      setSelectedStudent(updatedStudent);
    }
  };

  // Filtering & Sorting
  const filteredStudents = useMemo(() => {
    let result = studentsList.filter((student) => {
      if (statusFilter !== 'all' && student.status !== statusFilter) {
        return false;
      }
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase().trim();
        return (
          student.name.toLowerCase().includes(q) || 
          student.code.toLowerCase().includes(q)
        );
      }
      return true;
    });

    if (scoreSortOrder === 'asc') {
      result.sort((a, b) => {
        const scoreA = selectedSubject === 'all' ? (a.avgScore ?? 0) : (a.subjectScores?.[selectedSubject] ?? a.avgScore ?? 0);
        const scoreB = selectedSubject === 'all' ? (b.avgScore ?? 0) : (b.subjectScores?.[selectedSubject] ?? b.avgScore ?? 0);
        return scoreA - scoreB;
      });
    } else if (scoreSortOrder === 'desc') {
      result.sort((a, b) => {
        const scoreA = selectedSubject === 'all' ? (a.avgScore ?? 0) : (a.subjectScores?.[selectedSubject] ?? a.avgScore ?? 0);
        const scoreB = selectedSubject === 'all' ? (b.avgScore ?? 0) : (b.subjectScores?.[selectedSubject] ?? b.avgScore ?? 0);
        return scoreB - scoreA;
      });
    }

    return result;
  }, [studentsList, statusFilter, searchQuery, scoreSortOrder, selectedSubject]);

  const nextStudentCode = useMemo(() => {
    const highestNum = studentsList.reduce((max, s) => {
      const match = s.code?.match(/HS2023(\d+)/);
      if (match) {
        const num = parseInt(match[1], 10);
        return num > max ? num : max;
      }
      return max;
    }, 0);
    const nextNum = (highestNum > 0 ? highestNum + 1 : studentsList.length + 1).toString().padStart(3, '0');
    return `HS2023${nextNum}`;
  }, [studentsList]);

  const handleAddStudent = () => {
    setShowAddStudentModal(true);
  };

  const handleCreateStudent = (newStudent) => {
    setStudentsList(prev => [newStudent, ...prev]);
  };

  const getStatusBadgeClass = (status) => {
    switch (status) {
      case 'excellent':
        return 'status-badge status-excellent';
      case 'good':
        return 'status-badge status-good';
      case 'fair':
        return 'status-badge status-fair';
      default:
        return 'status-badge status-average';
    }
  };

  return (
    <div className="homeroom-layout">
      {/* Top Global Header */}
      <Header onToggleSidebar={() => setShowSidebar(!showSidebar)} />

      <div className="homeroom-body">
        {/* Left Teacher Sidebar */}
        {showSidebar && (
          <TeacherSidebar 
            activeNav="homeroom" 
            createButtonText="Tạo bài giảng mới"
            onCreateAction={() => alert('Tạo bài giảng mới')}
          />
        )}

        {/* Main Content Area */}
        <main className="homeroom-main">
          {/* Breadcrumb Navigation */}
          <nav className="homeroom-breadcrumb" aria-label="Breadcrumb">
            <Link to="/teacher" className="breadcrumb-link">Trang chủ</Link>
            <ChevronRight size={14} className="breadcrumb-separator" />
            <Link to="/teacher/classes" className="breadcrumb-link">Lớp học của tôi</Link>
            <ChevronRight size={14} className="breadcrumb-separator" />
            <span className="breadcrumb-current">
              {homeroomClass.name} ({homeroomClass.roleLabel})
            </span>
          </nav>

          {/* Class Header Banner Card */}
          <div className="homeroom-header-card">
            <div className="header-card-left">
              <h1 className="homeroom-class-title">{homeroomClass.name}</h1>
              <div className="homeroom-meta-row">
                <div className="meta-item">
                  <Users size={16} className="meta-icon" />
                  <span>Tổng số: <strong>{homeroomClass.totalStudents} học sinh</strong></span>
                </div>
                <div className="meta-item">
                  <Star size={16} className="meta-icon" />
                  <span>Khối: <strong>{homeroomClass.grade}</strong></span>
                </div>
              </div>
            </div>

            <div className="header-card-actions">
              <button 
                type="button" 
                className="btn-add-student"
                onClick={handleAddStudent}
              >
                <Plus size={16} strokeWidth={2.5} />
                <span>Thêm học sinh</span>
              </button>
            </div>
          </div>

          {/* Student Roster Table Card */}
          <div className="homeroom-roster-card">
            {/* Table Toolbar Header */}
            <div className="roster-toolbar">
              <h2 className="roster-toolbar-title">Danh sách học sinh</h2>

              <div className="roster-toolbar-controls">
                {/* Search Bar */}
                <div className="roster-search-input-wrapper">
                  <Search size={15} className="search-icon" />
                  <input
                    type="text"
                    className="roster-search-input"
                    placeholder="Tìm kiếm theo tên hoặc mã..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                </div>

                {/* Subject Filter Select */}
                <div className="roster-subject-select-wrapper">
                  <select
                    className="roster-subject-select"
                    value={selectedSubject}
                    onChange={(e) => setSelectedSubject(e.target.value)}
                  >
                    <option value="all">Tất cả các môn</option>
                    <option value="math">Toán học</option>
                    <option value="physics">Vật lý</option>
                    <option value="chemistry">Hóa học</option>
                    <option value="literature">Ngữ văn</option>
                    <option value="english">Tiếng Anh</option>
                    <option value="biology">Sinh học</option>
                    <option value="history">Lịch sử</option>
                  </select>
                  <ChevronDown size={14} className="roster-select-arrow" />
                </div>

                {/* Filter Button & Dropdown */}
                <div className="filter-dropdown-container">
                  <button 
                    type="button" 
                    className={`btn-filter-toggle ${showFilterDropdown || statusFilter !== 'all' ? 'active' : ''}`}
                    onClick={() => setShowFilterDropdown(!showFilterDropdown)}
                  >
                    <SlidersHorizontal size={15} />
                    <span>Lọc</span>
                  </button>

                  {showFilterDropdown && (
                    <div className="filter-popover-menu">
                      <div className="filter-menu-header">Lọc theo trạng thái</div>
                      <button 
                        type="button"
                        className={`filter-menu-item ${statusFilter === 'all' ? 'selected' : ''}`}
                        onClick={() => { setStatusFilter('all'); setShowFilterDropdown(false); }}
                      >
                        Tất cả
                      </button>
                      <button 
                        type="button"
                        className={`filter-menu-item ${statusFilter === 'excellent' ? 'selected' : ''}`}
                        onClick={() => { setStatusFilter('excellent'); setShowFilterDropdown(false); }}
                      >
                        Xuất sắc
                      </button>
                      <button 
                        type="button"
                        className={`filter-menu-item ${statusFilter === 'good' ? 'selected' : ''}`}
                        onClick={() => { setStatusFilter('good'); setShowFilterDropdown(false); }}
                      >
                        Tốt
                      </button>
                      <button 
                        type="button"
                        className={`filter-menu-item ${statusFilter === 'fair' ? 'selected' : ''}`}
                        onClick={() => { setStatusFilter('fair'); setShowFilterDropdown(false); }}
                      >
                        Khá
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Students Table */}
            <div className="roster-table-responsive">
              <table className="homeroom-students-table">
                <thead>
                  <tr>
                    <th className="col-code">MÃ HỌC SINH</th>
                    <th className="col-name">HỌ VÀ TÊN</th>
                    <th 
                      className="col-gpa sortable-col-header"
                      onClick={() => setScoreSortOrder(prev => prev === 'none' ? 'desc' : prev === 'desc' ? 'asc' : 'none')}
                      title="Nhấp để sắp xếp điểm: Cao đến thấp / Thấp đến cao / Mặc định"
                    >
                      <div className="th-sort-wrapper">
                        <span>
                          {selectedSubject === 'all' 
                            ? 'ĐIỂM TB (TẤT CẢ CÁC MÔN)' 
                            : `ĐIỂM TB (${(subjectLabels[selectedSubject] || 'MÔN HỌC').toUpperCase()})`}
                        </span>
                        <div className={`sort-badge-indicator ${scoreSortOrder !== 'none' ? 'active' : ''}`}>
                          {scoreSortOrder === 'desc' && (
                            <span className="sort-state-tag" title="Điểm: Cao đến thấp">
                              <ArrowDown size={12} strokeWidth={2.5} />
                              <span>Cao → Thấp</span>
                            </span>
                          )}
                          {scoreSortOrder === 'asc' && (
                            <span className="sort-state-tag" title="Điểm: Thấp đến cao">
                              <ArrowUp size={12} strokeWidth={2.5} />
                              <span>Thấp → Cao</span>
                            </span>
                          )}
                          {scoreSortOrder === 'none' && (
                            <ArrowUpDown size={13} className="sort-icon-default" />
                          )}
                        </div>
                      </div>
                    </th>
                    <th className="col-status">TRẠNG THÁI</th>
                    <th className="col-actions">THAO TÁC</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredStudents.length > 0 ? (
                    filteredStudents.map((student) => (
                      <tr 
                        key={student.id} 
                        className="student-table-row"
                        onClick={() => setSelectedStudent(student)}
                      >
                        <td className="col-code-cell">
                          <span className="student-code-text">{student.code}</span>
                        </td>
                        <td className="col-name-cell">
                          <div className="student-name-wrapper">
                            <div 
                              className="student-avatar-badge"
                              style={{ backgroundColor: student.avatarColor }}
                            >
                              {student.initials}
                            </div>
                            <span className="student-full-name">{student.name}</span>
                          </div>
                        </td>
                        <td className="col-gpa-cell">
                          <span className="gpa-score-text">
                            {selectedSubject === 'all' 
                              ? student.avgScore.toFixed(1)
                              : (student.subjectScores?.[selectedSubject]?.toFixed(1) ?? student.avgScore.toFixed(1))}
                          </span>
                        </td>
                        <td className="col-status-cell">
                          <span className={getStatusBadgeClass(student.status)}>
                            {student.statusLabel}
                          </span>
                        </td>
                        <td className="col-actions-cell" onClick={(e) => e.stopPropagation()}>
                          <div className="row-action-menu-wrapper">
                            <button 
                              type="button" 
                              className="btn-action-more"
                              onClick={() => setActiveMenuId(activeMenuId === student.id ? null : student.id)}
                              title="Thao tác"
                            >
                              <MoreVertical size={16} />
                            </button>
                            {activeMenuId === student.id && (
                              <div className="row-action-dropdown">
                                <button 
                                  type="button"
                                  onClick={() => { setSelectedStudent(student); setActiveMenuId(null); }}
                                >
                                  <FileSpreadsheet size={14} className="action-icon" />
                                  <span>Xem bảng điểm chi tiết</span>
                                </button>
                                <button 
                                  type="button"
                                  onClick={() => { setEditingInfoStudent(student); setActiveMenuId(null); }}
                                >
                                  <UserCog size={14} className="action-icon" />
                                  <span>Chỉnh sửa thông tin học sinh</span>
                                </button>
                                <button 
                                  type="button"
                                  onClick={() => { setEditingGradesStudent(student); setActiveMenuId(null); }}
                                >
                                  <FileEdit size={14} className="action-icon" />
                                  <span>Chỉnh sửa bảng điểm học sinh</span>
                                </button>
                                <button 
                                  type="button"
                                  onClick={() => { setPrintingStudent(student); setActiveMenuId(null); }}
                                >
                                  <Printer size={14} className="action-icon" />
                                  <span>In phiếu điểm học kỳ (A4)</span>
                                </button>
                              </div>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="5" className="empty-table-cell">
                        Không tìm thấy học sinh nào phù hợp với điều kiện tìm kiếm.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </main>
      </div>

      {/* Student Analytics & Detail Modal */}
      {selectedStudent && (
        <StudentDetailModal
          isOpen={!!selectedStudent}
          onClose={() => setSelectedStudent(null)}
          student={selectedStudent}
          classInfo={homeroomClass}
          isHomeroom={true}
        />
      )}

      {/* Standalone Edit Student Information Modal */}
      {editingInfoStudent && (
        <EditStudentInfoModal
          isOpen={!!editingInfoStudent}
          onClose={() => setEditingInfoStudent(null)}
          student={editingInfoStudent}
          onSave={handleSaveStudent}
        />
      )}

      {/* Standalone Edit Student Grades Modal */}
      {editingGradesStudent && (
        <EditStudentGradesModal
          isOpen={!!editingGradesStudent}
          onClose={() => setEditingGradesStudent(null)}
          student={editingGradesStudent}
          onSave={handleSaveStudent}
        />
      )}

      {/* Standalone Print Student Transcript A4 Modal */}
      {printingStudent && (
        <StudentTranscriptPrintModal
          isOpen={!!printingStudent}
          onClose={() => setPrintingStudent(null)}
          student={printingStudent}
          classInfo={homeroomClass}
        />
      )}

      {/* Add New Student Modal */}
      {showAddStudentModal && (
        <AddStudentModal
          isOpen={showAddStudentModal}
          onClose={() => setShowAddStudentModal(false)}
          onAddStudent={handleCreateStudent}
          nextStudentCode={nextStudentCode}
        />
      )}
    </div>
  );
}
