// File Name: ExerciseRepositoryPage.jsx
// Description: Teacher Exercise Repository Page for creating, previewing, and managing assignments.
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-08-30
// Updated By: Tam Khang

import React, { useState, useMemo } from 'react';
import { ChevronRight, Plus, ChevronLeft } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import Header from '../../components/common/Header';
import TeacherSidebar from '../../components/teacher/TeacherSidebar';
import ExerciseFilterBar from '../../components/exercises/ExerciseFilterBar';
import ExerciseCard from '../../components/exercises/ExerciseCard';
import CreateExerciseModal from '../../components/exercises/CreateExerciseModal';
import ExercisePreviewModal from '../../components/exercises/ExercisePreviewModal';
import './ExerciseRepositoryPage.css';

export default function ExerciseRepositoryPage() {
  const [showSidebar, setShowSidebar] = useState(true);
  const [selectedGrade, setSelectedGrade] = useState('all');
  const [selectedSubject, setSelectedSubject] = useState('all');
  const [selectedType, setSelectedType] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [previewExercise, setPreviewExercise] = useState(null);

  const navigate = useNavigate();

  // Mock data matching the design screenshot
  const [exercises, setExercises] = useState([
    {
      id: 1,
      title: 'Kiểm tra 15p – Đạo hàm',
      type: 'quiz',
      questionCount: '10 câu hỏi',
      duration: '15 phút',
      date: '20/10/2023',
      grade: '12',
      subject: 'math',
      authorName: 'Thầy Nguyễn Văn A',
      authorInitial: 'NA',
      hasShare: true,
    },
    {
      id: 2,
      title: 'Bài tập về nhà – Quang học',
      type: 'homework',
      questionCount: '5 bài tập tự luận',
      duration: null,
      date: '18/10/2023',
      grade: '11',
      subject: 'physics',
      authorName: 'Thầy Nguyễn Văn A',
      authorInitial: 'NA',
      hasShare: false,
    },
    {
      id: 3,
      title: 'Kiểm tra cuối kỳ – Đại số 10',
      type: 'test',
      questionCount: '40 câu hỏi',
      duration: '60 phút',
      date: '15/11/2023',
      grade: '10',
      subject: 'math',
      authorName: 'Thầy Nguyễn Văn A',
      authorInitial: 'NA',
      hasShare: true,
    },
    {
      id: 4,
      title: 'Bài tập về nhà – Hình học không gian',
      type: 'homework',
      questionCount: '8 bài tập tự luận',
      duration: null,
      date: '12/11/2023',
      grade: '12',
      subject: 'math',
      authorName: 'Thầy Nguyễn Văn A',
      authorInitial: 'NA',
      hasShare: false,
    },
    {
      id: 5,
      title: 'Ôn tập chương 2 – Hóa học hữu cơ',
      type: 'quiz',
      questionCount: '25 câu hỏi',
      duration: '30 phút',
      date: '05/11/2023',
      grade: '11',
      subject: 'chemistry',
      authorName: 'Thầy Nguyễn Văn A',
      authorInitial: 'NA',
      hasShare: true,
    },
    {
      id: 6,
      title: 'Đề cương ôn tập Vật lý – Học kỳ 1',
      type: 'homework',
      questionCount: '15 bài tập tổng hợp',
      duration: null,
      date: '01/11/2023',
      grade: '10',
      subject: 'physics',
      authorName: 'Thầy Nguyễn Văn A',
      authorInitial: 'NA',
      hasShare: false,
    },
  ]);

  // Filtered exercises
  const filteredExercises = useMemo(() => {
    return exercises.filter((item) => {
      if (selectedGrade !== 'all' && item.grade !== selectedGrade) {
        return false;
      }
      if (selectedSubject !== 'all' && item.subject !== selectedSubject) {
        return false;
      }
      if (selectedType !== 'all' && item.type !== selectedType) {
        return false;
      }
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase().trim();
        return item.title.toLowerCase().includes(q);
      }
      return true;
    });
  }, [exercises, selectedGrade, selectedSubject, selectedType, searchQuery]);

  const handleCreateSuccess = (newExercise) => {
    setExercises((prev) => [newExercise, ...prev]);
  };

  const handleNavSelect = (navId) => {
    if (navId === 'dashboard') {
      navigate('/teacher');
    } else if (navId === 'documents') {
      navigate('/teacher/documents');
    } else if (navId === 'exercises') {
      navigate('/teacher/exercises');
    }
  };

  return (
    <div className="exercise-repository-layout">
      {/* Top Global Header */}
      <Header onToggleSidebar={() => setShowSidebar(!showSidebar)} />

      <div className="exercise-repository-body">
        {/* Left Teacher Sidebar */}
        {showSidebar && (
          <TeacherSidebar 
            activeNav="exercises" 
            onSelectNav={handleNavSelect} 
            onCreateExercise={() => setIsCreateOpen(true)}
          />
        )}

        {/* Main Content Area */}
        <main className="exercise-repository-main">
          {/* Top Row: Breadcrumb, Title & Create Button */}
          <div className="exercise-top-bar">
            <div className="exercise-title-group">
              <nav className="breadcrumb-nav" aria-label="Breadcrumb">
                <Link to="/teacher" className="breadcrumb-link">Trang chủ</Link>
                <ChevronRight size={14} className="breadcrumb-separator" />
                <span className="breadcrumb-current">Kho bài tập</span>
              </nav>
              <h1 className="page-heading">Kho bài tập</h1>
              <p className="page-subheading">
                Quản lý và tạo mới các bài tập, bài kiểm tra cho học sinh.
              </p>
            </div>

            <button 
              type="button" 
              className="btn-create-new-exercise"
              onClick={() => setIsCreateOpen(true)}
            >
              <Plus size={18} />
              <span>Tạo bài tập mới</span>
            </button>
          </div>

          {/* Filter & Search Toolbar */}
          <ExerciseFilterBar
            selectedGrade={selectedGrade}
            onChangeGrade={setSelectedGrade}
            selectedSubject={selectedSubject}
            onChangeSubject={setSelectedSubject}
            selectedType={selectedType}
            onChangeType={setSelectedType}
            searchQuery={searchQuery}
            onChangeSearch={setSearchQuery}
          />

          {/* Exercise Cards Grid */}
          <div className="exercise-cards-grid">
            {filteredExercises.length > 0 ? (
              filteredExercises.map((exercise) => (
                <ExerciseCard
                  key={exercise.id}
                  exercise={exercise}
                  onPreview={(item) => setPreviewExercise(item)}
                  onEdit={(item) => alert(`Chỉnh sửa bài tập: ${item.title}`)}
                  onShare={(item) => setPreviewExercise(item)}
                  onDownload={(item) => alert(`Tải xuống đề bài: ${item.title}`)}
                  onMore={(item) => alert(`Tùy chọn: ${item.title}`)}
                />
              ))
            ) : (
              <div className="exercise-empty-state">
                <p>Không tìm thấy bài tập nào phù hợp với điều kiện tìm kiếm.</p>
              </div>
            )}
          </div>

          {/* Bottom Pagination Row matching Document Repository */}
          <div className="exercise-pagination-row">
            <span className="pagination-info">
              Hiển thị <strong>1</strong> đến <strong>{filteredExercises.length}</strong> trong số <strong>24</strong> bài tập
            </span>

            <div className="pagination-controls">
              <button 
                type="button" 
                className="pagination-btn arrow-btn"
                disabled={currentPage === 1}
                onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
              >
                <ChevronLeft size={16} />
              </button>

              <button 
                type="button" 
                className={`pagination-btn page-num-btn ${currentPage === 1 ? 'active' : ''}`}
                onClick={() => setCurrentPage(1)}
              >
                1
              </button>

              <button 
                type="button" 
                className={`pagination-btn page-num-btn ${currentPage === 2 ? 'active' : ''}`}
                onClick={() => setCurrentPage(2)}
              >
                2
              </button>

              <button 
                type="button" 
                className="pagination-btn arrow-btn"
                disabled={currentPage === 2}
                onClick={() => setCurrentPage(prev => prev + 1)}
              >
                <ChevronRight size={16} />
              </button>
            </div>
          </div>
        </main>
      </div>

      {/* Create Exercise Modal */}
      <CreateExerciseModal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        onCreateSuccess={handleCreateSuccess}
      />

      {/* Preview & Assign Exercise Modal */}
      <ExercisePreviewModal
        exercise={previewExercise}
        isOpen={!!previewExercise}
        onClose={() => setPreviewExercise(null)}
      />
    </div>
  );
}
