// File Name: ExerciseRepositoryPage.jsx
// Description: Teacher Exercise Repository Page connected to backend RESTful APIs with filtering, search, real questions preview, PDF export, and soft deletion.
// Created At: 2026-08-30
// Created By: Tam Khang
// Updated At: 2026-09-01
// Updated By: Tam Khang

import React, { useState, useEffect, useMemo } from 'react';
import { ChevronRight, Plus, ChevronLeft, Loader2, AlertCircle } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import Header from '../../components/common/Header';
import TeacherSidebar from '../../components/teacher/TeacherSidebar';
import ExerciseFilterBar from '../../components/exercises/ExerciseFilterBar';
import ExerciseCard from '../../components/exercises/ExerciseCard';
import CreateExerciseModal from '../../components/exercises/CreateExerciseModal';
import ExercisePreviewModal from '../../components/exercises/ExercisePreviewModal';
import { exercisesApi, subjectsApi } from '../../services/api';
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

  const [exercises, setExercises] = useState([]);
  const [subjectsList, setSubjectsList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const navigate = useNavigate();

  useEffect(() => {
    let isMounted = true;

    async function loadData() {
      try {
        setLoading(true);
        setError(null);

        const [exercisesRes, subjectsRes] = await Promise.allSettled([
          exercisesApi.getExercises(),
          subjectsApi.getSubjects()
        ]);

        if (!isMounted) return;

        let rawExercises = [];
        if (exercisesRes.status === 'fulfilled' && Array.isArray(exercisesRes.value)) {
          rawExercises = exercisesRes.value;
        }

        let rawSubjects = [];
        if (subjectsRes.status === 'fulfilled' && Array.isArray(subjectsRes.value)) {
          rawSubjects = subjectsRes.value;
          setSubjectsList(rawSubjects);
        }

        const subjectsMap = {};
        rawSubjects.forEach((s) => {
          subjectsMap[s.subject_id] = s.subject_name;
        });

        // Enrich exercises data for card display
        const enriched = rawExercises.map((ex) => {
          const meta = ex.ai_metadata || {};
          const subjectName = subjectsMap[ex.subject_id] || 'Toán học';

          let grade = meta.grade || '12';
          if (!meta.grade) {
            const match = ex.title.match(/\b(10|11|12)\b/);
            if (match) grade = match[1];
          }

          let exType = meta.type || 'quiz';
          if (ex.title.toLowerCase().includes('về nhà')) exType = 'homework';
          else if (ex.title.toLowerCase().includes('cuối kỳ') || ex.title.toLowerCase().includes('giữa kỳ')) exType = 'test';

          const createdDate = ex.created_at ? new Date(ex.created_at).toLocaleDateString('vi-VN') : '20/10/2023';

          return {
            id: ex.exercise_id,
            title: ex.title,
            type: exType,
            questionCount: `${ex.total_questions || (ex.questions ? ex.questions.length : 0)} câu hỏi`,
            duration: meta.duration || (exType === 'test' ? '60 phút' : exType === 'quiz' ? '15 phút' : null),
            date: createdDate,
            grade: grade,
            subject: subjectName.toLowerCase().includes('toán') ? 'math' : subjectName.toLowerCase().includes('vật lý') ? 'physics' : subjectName.toLowerCase().includes('hóa') ? 'chemistry' : 'math',
            subjectName: subjectName,
            authorName: 'Thầy Nguyễn Văn A',
            authorInitial: 'NA',
            hasShare: true,
            raw: ex,
          };
        });

        if (isMounted) {
          setExercises(enriched);
        }
      } catch (err) {
        if (isMounted) {
          setError(err.response?.data?.detail?.message || 'Không thể tải danh sách bài tập.');
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
        return item.title.toLowerCase().includes(q) || item.subjectName.toLowerCase().includes(q);
      }
      return true;
    });
  }, [exercises, selectedGrade, selectedSubject, selectedType, searchQuery]);

  const handleCreateSuccess = (newExercise) => {
    setExercises((prev) => [newExercise, ...prev]);
  };

  const handleDownloadPdf = async (exercise) => {
    try {
      const blob = await exercisesApi.exportPdf(exercise.id);
      const url = window.URL.createObjectURL(new Blob([blob], { type: 'application/pdf' }));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${exercise.title || 'de_bai'}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert('Không thể xuất file PDF cho bài tập này.');
    }
  };

  const handleDeleteExercise = async (exercise) => {
    if (window.confirm(`Bạn có chắc chắn muốn xóa bài tập "${exercise.title}"?`)) {
      try {
        await exercisesApi.deleteExercise(exercise.id);
        setExercises((prev) => prev.filter((item) => item.id !== exercise.id));
        alert('Đã xóa thành công bài tập.');
      } catch (err) {
        alert('Không thể xóa bài tập này.');
      }
    }
  };

  const handleNavSelect = (navId) => {
    if (navId === 'dashboard') {
      navigate('/teacher');
    } else if (navId === 'classes') {
      navigate('/teacher/classes');
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
              <h1 className="page-heading">Kho bài tập ({exercises.length})</h1>
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

          {/* Error Alert */}
          {error && (
            <div style={{ padding: '12px 16px', background: '#FEF2F2', border: '1px solid #FCA5A5', borderRadius: '8px', color: '#991B1B', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <AlertCircle size={18} />
              <span>{error}</span>
            </div>
          )}

          {/* Loading Indicator or Cards Grid */}
          {loading ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '260px', gap: '12px', color: '#6B7280' }}>
              <Loader2 size={32} className="animate-spin" style={{ animation: 'spin 1s linear infinite' }} />
              <p>Đang tải danh sách bài tập từ hệ thống...</p>
            </div>
          ) : (
            /* Exercise Cards Grid */
            <div className="exercise-cards-grid">
              {filteredExercises.length > 0 ? (
                filteredExercises.map((exercise) => (
                  <ExerciseCard
                    key={exercise.id}
                    exercise={exercise}
                    onPreview={(item) => setPreviewExercise(item)}
                    onEdit={(item) => alert(`Chỉnh sửa bài tập: ${item.title}`)}
                    onShare={(item) => setPreviewExercise(item)}
                    onDownload={(item) => handleDownloadPdf(item)}
                    onMore={(item) => handleDeleteExercise(item)}
                  />
                ))
              ) : (
                <div className="exercise-empty-state">
                  <p>Không tìm thấy bài tập nào phù hợp với điều kiện tìm kiếm.</p>
                </div>
              )}
            </div>
          )}

          {/* Bottom Pagination Row */}
          {!loading && filteredExercises.length > 0 && (
            <div className="exercise-pagination-row">
              <span className="pagination-info">
                Hiển thị <strong>1</strong> đến <strong>{filteredExercises.length}</strong> trong số <strong>{filteredExercises.length}</strong> bài tập
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
                  className="pagination-btn arrow-btn"
                  disabled={currentPage === 1}
                  onClick={() => setCurrentPage(prev => prev + 1)}
                >
                  <ChevronRight size={16} />
                </button>
              </div>
            </div>
          )}
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
