// File Name: TeacherClassesPage.jsx
// Description: Teacher Classes overview page connected to backend RESTful API with search, filtering, and dynamic cards.
// Created At: 2026-08-31
// Created By: Tam Khang
// Updated At: 2026-09-01
// Updated By: Tam Khang

import React, { useState, useEffect, useMemo } from 'react';
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
  AlertCircle
} from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import Header from '../../components/common/Header';
import TeacherSidebar from '../../components/teacher/TeacherSidebar';
import { classesApi, subjectsApi } from '../../services/api';
import './TeacherClassesPage.css';

export default function TeacherClassesPage() {
  const [showSidebar, setShowSidebar] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedGrade, setSelectedGrade] = useState('all');
  const [selectedSubject, setSelectedSubject] = useState('all');
  const [classesList, setClassesList] = useState([]);
  const [subjectsList, setSubjectsList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const navigate = useNavigate();

  // Color themes for card banner rotation
  const THEMES = ['purple-theme', 'lavender-theme', 'pink-theme'];

  useEffect(() => {
    let isMounted = true;

    async function loadData() {
      try {
        setLoading(true);
        setError(null);

        // Fetch classes and subjects concurrently
        const [classesRes, subjectsRes] = await Promise.allSettled([
          classesApi.getClasses(),
          subjectsApi.getSubjects()
        ]);

        if (!isMounted) return;

        let classesData = [];
        if (classesRes.status === 'fulfilled' && Array.isArray(classesRes.value)) {
          classesData = classesRes.value;
        }

        let subjectsData = [];
        if (subjectsRes.status === 'fulfilled' && Array.isArray(subjectsRes.value)) {
          subjectsData = subjectsRes.value;
        }
        setSubjectsList(subjectsData);

        // Fetch students count for each class in parallel
        const enrichedClasses = await Promise.all(
          classesData.map(async (cls, index) => {
            let studentCount = 0;
            try {
              const students = await classesApi.getStudentsInClass(cls.class_id);
              if (Array.isArray(students)) {
                studentCount = students.length;
              }
            } catch {
              studentCount = 0;
            }

            // Extract grade from class_name (e.g., "12A1", "Lớp 11B2", "10A3")
            const gradeMatch = cls.class_name.match(/\b(10|11|12)\b/);
            const grade = gradeMatch ? gradeMatch[1] : '12';

            // Extract or assign subject name
            let subjectName = 'Toán học';
            let iconType = 'sigma';

            if (cls.class_name.toLowerCase().includes('lý') || cls.class_name.toLowerCase().includes('vật lý') || cls.class_name.toLowerCase().includes('physics')) {
              subjectName = 'Vật lý';
              iconType = 'flask';
            } else if (cls.class_name.toLowerCase().includes('hóa') || cls.class_name.toLowerCase().includes('chemistry')) {
              subjectName = 'Hóa học';
              iconType = 'flask';
            } else if (cls.class_name.toLowerCase().includes('toán') || cls.class_name.toLowerCase().includes('math')) {
              subjectName = 'Toán học';
              iconType = 'sigma';
            } else {
              iconType = 'grid';
            }

            return {
              id: cls.class_id,
              name: cls.class_name,
              grade: grade,
              gradeText: `Khối ${grade}`,
              term: cls.school_year ? `Năm học ${cls.school_year}` : 'Kì 1, 2023–2024',
              currentStudents: studentCount,
              maxStudents: 45,
              subject: subjectName.toLowerCase(),
              subjectName: subjectName,
              bannerTheme: THEMES[index % THEMES.length],
              iconType: iconType,
              status: cls.status,
            };
          })
        );

        if (isMounted) {
          setClassesList(enrichedClasses);
        }
      } catch (err) {
        if (isMounted) {
          setError(err.response?.data?.detail?.message || 'Không thể tải danh sách lớp học.');
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    loadData();

    return () => {
      isMounted = false;
    };
  }, []);

  const filteredClasses = useMemo(() => {
    return classesList.filter((item) => {
      if (selectedGrade !== 'all' && item.grade !== selectedGrade) {
        return false;
      }
      if (selectedSubject !== 'all') {
        const matchesSubject = item.subject.includes(selectedSubject.toLowerCase()) || 
                               item.subjectName.toLowerCase().includes(selectedSubject.toLowerCase());
        if (!matchesSubject) return false;
      }
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase().trim();
        return item.name.toLowerCase().includes(q) || item.subjectName.toLowerCase().includes(q);
      }
      return true;
    });
  }, [classesList, selectedGrade, selectedSubject, searchQuery]);

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

  const handleNavSelect = (navId) => {
    if (navId === 'documents') {
      navigate('/teacher/documents');
    } else if (navId === 'exercises') {
      navigate('/teacher/exercises');
    } else if (navId === 'classes') {
      navigate('/teacher/classes');
    } else if (navId === 'dashboard') {
      navigate('/teacher');
    }
  };

  return (
    <div className="teacher-classes-layout">
      {/* Top Header */}
      <Header onToggleSidebar={() => setShowSidebar(!showSidebar)} />

      <div className="teacher-classes-body">
        {/* Left Sidebar */}
        {showSidebar && (
          <TeacherSidebar 
            activeNav="classes" 
            onSelectNav={handleNavSelect}
            createButtonText="Tạo lớp học mới"
            onCreateAction={() => alert('Vui lòng liên hệ Quản trị viên để tạo thêm lớp mới.')}
          />
        )}

        {/* Main Content Area */}
        <main className="teacher-classes-main">
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

            {/* Grade Filter */}
            <div className="classes-select-wrapper">
              <select
                className="classes-select"
                value={selectedGrade}
                onChange={(e) => setSelectedGrade(e.target.value)}
              >
                <option value="all">Tất cả khối lớp</option>
                <option value="10">Khối 10</option>
                <option value="11">Khối 11</option>
                <option value="12">Khối 12</option>
              </select>
              <ChevronDown size={15} className="classes-select-arrow" />
            </div>

            {/* Subject Filter */}
            <div className="classes-select-wrapper">
              <select
                className="classes-select"
                value={selectedSubject}
                onChange={(e) => setSelectedSubject(e.target.value)}
              >
                <option value="all">Tất cả môn học</option>
                {subjectsList.length > 0 ? (
                  subjectsList.map((s) => (
                    <option key={s.subject_id} value={s.subject_name}>
                      {s.subject_name}
                    </option>
                  ))
                ) : (
                  <>
                    <option value="math">Toán học</option>
                    <option value="physics">Vật lý</option>
                    <option value="chemistry">Hóa học</option>
                  </>
                )}
              </select>
              <ChevronDown size={15} className="classes-select-arrow" />
            </div>
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
                          {cls.gradeText} • {cls.term}
                        </span>
                      </div>
                    </div>

                    {/* Card Bottom Meta */}
                    <div className="class-card-footer">
                      <div className="class-students-count">
                        <Users size={15} className="users-icon" />
                        <span>Sĩ số: {cls.currentStudents}/{cls.maxStudents}</span>
                      </div>
                      <span className="class-subject-badge">{cls.subjectName}</span>
                    </div>
                  </div>
                ))
              ) : (
                <div className="classes-empty-state">
                  <p>Không tìm thấy lớp học nào phù hợp với bộ lọc.</p>
                </div>
              )}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
