// File Name: TeacherClassesPage.jsx
// Description: Teacher Classes overview page with class cards, search, and filtering.
// Created At: 2026-08-31
// Created By: Tam Khang
// Updated At: 2026-09-01
// Updated By: Tam Khang

import React, { useState, useMemo } from 'react';
import { 
  ChevronRight, 
  Search, 
  Users, 
  ChevronDown, 
  Sigma, 
  LayoutGrid,
  BookOpen
} from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import Header from '../../components/common/Header';
import TeacherSidebar from '../../components/teacher/TeacherSidebar';
import './TeacherClassesPage.css';

export default function TeacherClassesPage() {
  const [showSidebar, setShowSidebar] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedGrade, setSelectedGrade] = useState('all');
  const navigate = useNavigate();

  // Mock data for the Mathematics department classes
  const classesData = [
    {
      id: '12a1',
      name: '12A1 - Toán nâng cao',
      grade: '12',
      gradeText: 'Khối 12',
      term: 'Kì 1, 2023–2024',
      currentStudents: 45,
      maxStudents: 45,
      subject: 'math',
      subjectName: 'Toán học',
      bannerTheme: 'purple-theme',
      iconType: 'sigma',
    },
    {
      id: '11b2',
      name: '11B2 - Toán cơ bản',
      grade: '11',
      gradeText: 'Khối 11',
      term: 'Kì 1, 2023–2024',
      currentStudents: 42,
      maxStudents: 45,
      subject: 'math',
      subjectName: 'Toán học',
      bannerTheme: 'lavender-theme',
      iconType: 'sigma',
    },
    {
      id: '10a3',
      name: '10A3 - Toán cơ bản',
      grade: '10',
      gradeText: 'Khối 10',
      term: 'Kì 1, 2023–2024',
      currentStudents: 40,
      maxStudents: 40,
      subject: 'math',
      subjectName: 'Toán học',
      bannerTheme: 'pink-theme',
      iconType: 'grid',
    }
  ];

  const filteredClasses = useMemo(() => {
    return classesData.filter((item) => {
      if (selectedGrade !== 'all' && item.grade !== selectedGrade) {
        return false;
      }
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase().trim();
        return item.name.toLowerCase().includes(q) || item.gradeText.toLowerCase().includes(q);
      }
      return true;
    });
  }, [classesData, selectedGrade, searchQuery]);

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

  return (
    <div className="teacher-classes-layout">
      {/* Top Header */}
      <Header onToggleSidebar={() => setShowSidebar(!showSidebar)} />

      <div className="teacher-classes-body">
        {/* Left Sidebar */}
        {showSidebar && (
          <TeacherSidebar 
            activeNav="classes" 
            createButtonText="Tạo lớp học mới"
            onCreateAction={() => alert('Tạo lớp học mới')}
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
          </div>

          {/* Classes Cards Grid */}
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
        </main>
      </div>
    </div>
  );
}
