// File Name: TeacherHomeroomPage.jsx
// Description: Homeroom class management page displaying student roster, GPA/subject score filtering, status badges, and export/add student actions.
// Created At: 2026-09-01
// Created By: Tam Khang
// Updated At: 2026-09-01
// Updated By: Tam Khang

import React, { useState, useEffect, useMemo } from 'react';
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
  Printer,
  Loader2,
  AlertCircle
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { classesApi } from '../../services/api';
import StudentDetailModal from '../../components/teacher/StudentDetailModal';
import EditStudentInfoModal from '../../components/teacher/EditStudentInfoModal';
import EditStudentGradesModal from '../../components/teacher/EditStudentGradesModal';
import StudentTranscriptPrintModal from '../../components/teacher/StudentTranscriptPrintModal';
import AddStudentModal from '../../components/teacher/AddStudentModal';
import './TeacherHomeroomPage.css';

export default function TeacherHomeroomPage() {
  const [showSidebar, setShowSidebar] = useState(true);
  const [classesList, setClassesList] = useState([]);
  const [selectedClassId, setSelectedClassId] = useState('');
  const [currentClassInfo, setCurrentClassInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

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

  const [studentsList, setStudentsList] = useState([]);

  // Load available classes on mount
  useEffect(() => {
    let isMounted = true;
    async function loadClasses() {
      try {
        setLoading(true);
        setError(null);
        const res = await classesApi.getClasses();
        if (!isMounted) return;
        if (Array.isArray(res) && res.length > 0) {
          setClassesList(res);
          setSelectedClassId(res[0].class_id);
          setCurrentClassInfo(res[0]);
        }
      } catch (err) {
        if (isMounted) setError('Không thể tải danh sách lớp học.');
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadClasses();
    return () => {
      isMounted = false;
    };
  }, []);

  // Load students for selected class
  useEffect(() => {
    if (!selectedClassId) return;
    let isMounted = true;

    async function loadStudents() {
      try {
        setLoading(true);
        const cls = classesList.find(c => c.class_id === selectedClassId);
        if (cls) setCurrentClassInfo(cls);

        const res = await classesApi.getStudentsInClass(selectedClassId);
        if (!isMounted) return;

        if (Array.isArray(res) && res.length > 0) {
          const avatarColors = ['#7C3AED', '#8B5CF6', '#A78BFA', '#6366F1', '#EC4899', '#3B82F6', '#10B981', '#F59E0B'];
          const mapped = res.map((s, idx) => {
            const name = s.student_name || `Học sinh ${idx + 1}`;
            const nameParts = name.trim().split(' ');
            const initials = nameParts.length >= 2
              ? (nameParts[nameParts.length - 2][0] + nameParts[nameParts.length - 1][0]).toUpperCase()
              : name.substring(0, 2).toUpperCase();
            return {
              id: s.student_id,
              code: s.student_code || `HS${String(idx + 1).padStart(3, '0')}`,
              name: name,
              initials: initials,
              avatarColor: avatarColors[idx % avatarColors.length],
              avgScore: 8.2,
              status: s.status === 'ACTIVE' ? 'good' : 'fair',
              statusLabel: s.status === 'ACTIVE' ? 'Đang học' : 'Nghỉ học',
              subjectScores: { math: 8.5, physics: 8.0, chemistry: 8.2, literature: 8.0, english: 8.5, biology: 8.0, history: 8.0, informatics: 8.5 }
            };
          });
          setStudentsList(mapped);
        } else {
          setStudentsList([]);
        }
      } catch (err) {
        if (isMounted) {
          // If error loading students
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    loadStudents();
    return () => {
      isMounted = false;
    };
  }, [selectedClassId, classesList]);

  // Homeroom class metadata
  const homeroomClass = {
    name: currentClassInfo?.class_name || '12A1 - Toán nâng cao',
    roleLabel: 'Lớp chủ nhiệm',
    totalStudents: studentsList.length,
    grade: currentClassInfo?.class_name?.match(/\d+/)?.[0] || 12,
    term: currentClassInfo?.school_year || '2025-2026'
  };

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
    <div className="homeroom-main">
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
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <h1 className="homeroom-class-title">{homeroomClass.name}</h1>
                {classesList.length > 1 && (
                  <select
                    value={selectedClassId}
                    onChange={(e) => setSelectedClassId(e.target.value)}
                    style={{ padding: '6px 12px', borderRadius: '6px', border: '1px solid #CBD5E1', fontSize: '13px', background: '#FFFFFF', color: '#1E293B', cursor: 'pointer', fontWeight: 600 }}
                  >
                    {classesList.map(c => (
                      <option key={c.class_id} value={c.class_id}>
                        {c.class_name} {c.school_year ? `(${c.school_year})` : ''}
                      </option>
                    ))}
                  </select>
                )}
              </div>
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
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h2 className="roster-toolbar-title">Danh sách học sinh</h2>
                {loading && <Loader2 size={16} className="animate-spin" style={{ color: '#6366F1' }} />}
              </div>

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
