// File Name: TeacherClassesPage.jsx
// Description: Teacher Classes overview page with real-time database sync, academic year filtering defaulting to current year, refresh button, and dynamic cards.
// Created At: 2026-08-31
// Created By: Tam Khang
// Updated At: 2026-10-28
// Updated By: Tam Khang

import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { 
  ChevronRight, 
  Search, 
  Users, 
  ChevronDown, 
  Sigma, 
  FlaskConical,
  LayoutGrid,
  BookOpen,
  Loader2,
  AlertCircle,
  RefreshCw
} from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { classesApi, subjectsApi } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import './TeacherClassesPage.css';

/**
 * Calculates current academic school year (e.g., '2026-2027' for October 2026).
 * School years in Vietnam typically begin around August/September.
 */
function getCurrentAcademicYear() {
  const now = new Date();
  const year = now.getFullYear();
  const month = now.getMonth() + 1; // 1-12
  return month >= 8 ? `${year}-${year + 1}` : `${year - 1}-${year}`;
}

// Minimum gap between automatic refreshes triggered by tab visibility.
const MIN_REFRESH_GAP_MS = 30000;

export default function TeacherClassesPage() {
  const currentAcademicYear = useMemo(() => getCurrentAcademicYear(), []);

  const [searchQuery, setSearchQuery] = useState('');
  const [selectedYear, setSelectedYear] = useState(currentAcademicYear);
  const [selectedGrade, setSelectedGrade] = useState('all');
  const [selectedSubject, setSelectedSubject] = useState('all');
  const [classesList, setClassesList] = useState([]);
  const [subjectsList, setSubjectsList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState(null);

  const { user } = useAuth();
  const navigate = useNavigate();

  // Refs keep the loader stable: it must not be re-created (and re-subscribed) when the user object changes.
  const userIdRef = useRef(user?.user_id);
  userIdRef.current = user?.user_id;
  const isRefreshingRef = useRef(false);
  const lastLoadedAtRef = useRef(0);
  const userId = user?.user_id;

  // Color themes for card banner rotation
  const THEMES = ['purple-theme', 'lavender-theme', 'pink-theme'];

  // Load and enrich classes data from backend APIs
  const loadData = useCallback(async (isInitial = false) => {
    isRefreshingRef.current = true;
    try {
      if (isInitial) {
        setLoading(true);
      } else {
        setIsRefreshing(true);
      }
      setError(null);

      // Fetch classes and subjects concurrently
      const [classesRes, subjectsRes] = await Promise.allSettled([
        classesApi.getClasses(),
        subjectsApi.getSubjects()
      ]);

      let classesData = [];
      if (classesRes.status === 'fulfilled' && Array.isArray(classesRes.value)) {
        classesData = classesRes.value;
      }

      let subjectsData = [];
      if (subjectsRes.status === 'fulfilled' && Array.isArray(subjectsRes.value)) {
        subjectsData = subjectsRes.value;
      }
      setSubjectsList(subjectsData);

      // Fetch real student counts and teacher assignments in parallel
      const enrichedClasses = await Promise.all(
        classesData.map(async (cls, index) => {
          let studentCount = 0;
          let assignedSubjectName = '';

          try {
            const [students, teacherAssignments] = await Promise.all([
              classesApi.getStudentsInClass(cls.class_id).catch(() => []),
              classesApi.getTeacherSubjects(cls.class_id).catch(() => [])
            ]);

            if (Array.isArray(students)) {
              studentCount = students.length;
            }

            if (Array.isArray(teacherAssignments)) {
              // Find assignment for current teacher if authenticated
              let myAssign = null;
              const currentUserId = userIdRef.current;
              if (currentUserId) {
                myAssign = teacherAssignments.find(a => a.teacher_id === currentUserId && a.status !== 'DELETED');
              }
              // If not found for current user, check active assignment in class
              if (!myAssign && teacherAssignments.length > 0) {
                myAssign = teacherAssignments.find(a => a.status !== 'DELETED') || teacherAssignments[0];
              }

              if (myAssign) {
                const foundSub = subjectsData.find(s => s.subject_id === myAssign.subject_id);
                if (foundSub) {
                  assignedSubjectName = foundSub.subject_name;
                }
              }
            }
          } catch {
            studentCount = 0;
          }

          // Extract real grade from class name (e.g. 10A3 -> 10, 11B2 -> 11, 12A1 -> 12)
          const gradeMatch = cls.class_name.match(/(10|11|12)/);
          const grade = gradeMatch ? gradeMatch[1] : '';

          const subjectName = assignedSubjectName || (subjectsData[0]?.subject_name || 'Bộ môn');
          const lowerSub = subjectName.toLowerCase();
          let iconType = 'book';

          if (lowerSub.includes('toán') || lowerSub.includes('math')) {
            iconType = 'sigma';
          } else if (lowerSub.includes('lý') || lowerSub.includes('hóa') || lowerSub.includes('sinh')) {
            iconType = 'flask';
          } else if (lowerSub.includes('anh') || lowerSub.includes('văn') || lowerSub.includes('sử') || lowerSub.includes('địa')) {
            iconType = 'book';
          } else {
            iconType = 'grid';
          }

          const rawYear = (cls.school_year || cls.academic_year || '').trim();

          return {
            id: cls.class_id,
            name: cls.class_name,
            grade: grade,
            gradeText: grade ? `Khối ${grade}` : 'Khối lớp',
            schoolYear: rawYear,
            term: rawYear ? `Năm học ${rawYear}` : '',
            currentStudents: studentCount,
            subject: subjectName.toLowerCase(),
            subjectName: subjectName,
            bannerTheme: THEMES[index % THEMES.length],
            iconType: iconType,
            status: cls.status,
          };
        })
      );

      setClassesList(enrichedClasses);
    } catch (err) {
      setError(err.response?.data?.detail?.message || 'Không thể tải danh sách lớp học.');
    } finally {
      if (isInitial) setLoading(false);
      setIsRefreshing(false);
      isRefreshingRef.current = false;
      lastLoadedAtRef.current = Date.now();
    }
  }, []);

  // Initial load and automated background synchronization
  useEffect(() => {
    loadData(true);

    // Refresh when the tab becomes visible again. Each refresh fans out two requests per class,
    // so there is no timer and a refresh is skipped while another one is still running or was just done.
    const handleVisibility = () => {
      if (document.visibilityState !== 'visible') return;
      if (isRefreshingRef.current || Date.now() - lastLoadedAtRef.current < MIN_REFRESH_GAP_MS) return;
      loadData(false);
    };

    document.addEventListener('visibilitychange', handleVisibility);
    return () => document.removeEventListener('visibilitychange', handleVisibility);
    // userId re-triggers the initial load once the authenticated user is known.
  }, [loadData, userId]);

  // Distinct academic years available from data + current academic year
  const availableYears = useMemo(() => {
    const yearsSet = new Set();
    yearsSet.add(currentAcademicYear);
    classesList.forEach(c => {
      if (c.schoolYear) {
        yearsSet.add(c.schoolYear);
      }
    });
    return Array.from(yearsSet).sort().reverse();
  }, [classesList, currentAcademicYear]);

  // Available subjects taught
  const teacherSubjects = useMemo(() => {
    return Array.from(new Set(classesList.map(c => c.subjectName).filter(s => s && s !== 'Bộ môn')));
  }, [classesList]);

  // Filtered classes according to search, academic year, grade, and subject
  const filteredClasses = useMemo(() => {
    return classesList.filter((item) => {
      // 1. Academic Year Filter
      if (selectedYear !== 'all') {
        if (item.schoolYear !== selectedYear) {
          return false;
        }
      }

      // 2. Grade Filter
      if (selectedGrade !== 'all' && item.grade !== selectedGrade) {
        return false;
      }

      // 3. Subject Filter
      if (selectedSubject !== 'all') {
        const matchesSubject = (item.subject || '').includes(selectedSubject.toLowerCase()) || 
                               (item.subjectName || '').toLowerCase().includes(selectedSubject.toLowerCase());
        if (!matchesSubject) return false;
      }

      // 4. Search Query
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase().trim();
        return (item.name || '').toLowerCase().includes(q) || 
               (item.gradeText || '').toLowerCase().includes(q) || 
               (item.subjectName || '').toLowerCase().includes(q) ||
               (item.schoolYear || '').toLowerCase().includes(q);
      }

      return true;
    });
  }, [classesList, selectedYear, selectedGrade, selectedSubject, searchQuery]);

  const renderClassIcon = (type) => {
    switch (type) {
      case 'sigma':
        return <Sigma size={20} className="class-banner-icon" />;
      case 'flask':
        return <FlaskConical size={20} className="class-banner-icon" />;
      case 'grid':
        return <LayoutGrid size={20} className="class-banner-icon" />;
      default:
        return <BookOpen size={20} className="class-banner-icon" />;
    }
  };

  const handleCardClick = (classId) => {
    navigate(`/teacher/classes/${classId}`);
  };

  const handleManualRefresh = () => {
    loadData(false);
  };

  return (
    <div className="teacher-classes-main">
      {/* Breadcrumb & Title */}
      <div className="classes-top-section">
        <nav className="breadcrumb-nav" aria-label="Breadcrumb">
          <Link to="/teacher" className="breadcrumb-link">Trang chủ</Link>
          <ChevronRight size={14} className="breadcrumb-separator" />
          <span className="breadcrumb-current">Lớp học của tôi</span>
        </nav>
        <h1 className="classes-page-heading">Lớp học của tôi</h1>
      </div>

      {/* Filter Toolbar */}
      <div className="classes-filter-bar">
        {/* Search Input */}
        <div className="classes-search-wrapper">
          <Search size={16} className="classes-search-icon" />
          <input
            type="text"
            className="classes-search-input"
            placeholder="Tìm kiếm tên lớp..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        {/* Academic Year Filter (Defaults to Current School Year) */}
        <div className="classes-select-wrapper">
          <select
            className="classes-select"
            value={selectedYear}
            onChange={(e) => setSelectedYear(e.target.value)}
            aria-label="Lọc theo năm học"
          >
            <option value="all">Tất cả năm học</option>
            {availableYears.map((yr) => (
              <option key={yr} value={yr}>
                Năm học {yr}{yr === currentAcademicYear ? ' (Hiện tại)' : ''}
              </option>
            ))}
          </select>
          <ChevronDown size={15} className="classes-select-arrow" />
        </div>

        {/* Grade Filter */}
        <div className="classes-select-wrapper">
          <select
            className="classes-select"
            value={selectedGrade}
            onChange={(e) => setSelectedGrade(e.target.value)}
            aria-label="Lọc theo khối lớp"
          >
            <option value="all">Tất cả khối lớp</option>
            <option value="10">Khối 10</option>
            <option value="11">Khối 11</option>
            <option value="12">Khối 12</option>
          </select>
          <ChevronDown size={15} className="classes-select-arrow" />
        </div>

        {/* Subject Filter (Only shown if teacher teaches more than 1 subject) */}
        {teacherSubjects.length > 1 && (
          <div className="classes-select-wrapper">
            <select
              className="classes-select"
              value={selectedSubject}
              onChange={(e) => setSelectedSubject(e.target.value)}
              aria-label="Lọc theo môn học"
            >
              <option value="all">Tất cả môn học</option>
              {teacherSubjects.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
            <ChevronDown size={15} className="classes-select-arrow" />
          </div>
        )}

        {/* Refresh Button */}
        <button
          type="button"
          className="classes-refresh-btn"
          onClick={handleManualRefresh}
          disabled={isRefreshing || loading}
          title="Làm mới danh sách lớp học"
        >
          <RefreshCw size={14} className={isRefreshing ? 'refresh-spin-icon' : ''} />
          <span>Làm mới</span>
        </button>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="classes-error-banner" style={{ padding: '12px 16px', background: '#FEF2F2', border: '1px solid #FCA5A5', borderRadius: '8px', color: '#991B1B', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      {/* Loading Indicator or Classes Grid */}
      {loading ? (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '260px', gap: '12px', color: '#6B7280' }}>
          <Loader2 size={32} className="animate-spin" style={{ animation: 'spin 1s linear infinite' }} />
          <p>Đang tải danh sách lớp học...</p>
        </div>
      ) : (
        /* Classes Cards Grid */
        <div className="classes-cards-grid">
          {filteredClasses.length > 0 ? (
            filteredClasses.map((cls) => (
              <div 
                key={cls.id} 
                className="class-card"
                onClick={() => handleCardClick(cls.id)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    handleCardClick(cls.id);
                  }
                }}
              >
                {/* Card Top Banner */}
                <div className={`class-card-banner ${cls.bannerTheme}`}>
                  <div className="class-icon-container">
                    {renderClassIcon(cls.iconType)}
                  </div>
                  <div className="class-banner-info">
                    <h2 className="class-banner-title">{cls.name}</h2>
                    <span className="class-banner-subtext">
                      {cls.gradeText}{cls.term ? ` • ${cls.term}` : ''}
                    </span>
                  </div>
                </div>

                {/* Card Bottom Meta */}
                <div className="class-card-footer">
                  <div className="class-students-count">
                    <Users size={15} className="users-icon" />
                    <span>Sĩ số: {cls.currentStudents}</span>
                  </div>
                  <span className="class-subject-badge">{cls.subjectName}</span>
                </div>
              </div>
            ))
          ) : (
            <div className="classes-empty-state">
              <p>
                {selectedYear !== 'all' 
                  ? `Không tìm thấy lớp học nào thuộc năm học ${selectedYear} phù hợp với bộ lọc.` 
                  : 'Không tìm thấy lớp học nào phù hợp với bộ lọc.'}
              </p>
              {selectedYear !== 'all' && (
                <button
                  type="button"
                  style={{ marginTop: '12px', padding: '6px 14px', background: '#F5F3FF', border: '1px solid #C4B5FD', borderRadius: '6px', color: '#4D308D', cursor: 'pointer', fontSize: '13px' }}
                  onClick={() => setSelectedYear('all')}
                >
                  Xem tất cả các năm học
                </button>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
